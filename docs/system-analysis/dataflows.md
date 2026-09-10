# Phase 3 — Dataflow Analysis

Traces the important data flows through both applications, identifying source, destination, trust boundaries, validation, authorization, persistence, failure handling, logging, and retry behavior.

**Legend:** 🟢 validated · 🟡 partially/weakly validated · 🔴 not validated

---

## A. Desktop app — authentication & profile

### A1. First-run sign-in / account creation (ProfileOverlay)

```
INPUT: username, password (ProfileOverlay._submit)
→ validation: username ≥ 2 chars, password ≥ 4 chars (core/local_auth.register) 🟢
→ authentication: local_auth.authenticate()
   • accounts.json absent → FIRST user auto-registers as role "student" 🟡
     (anyone who opens the app first on the machine becomes the only account holder)
→ storage: accounts.json (plaintext JSON, SHA-256 hash) 
→ session: profile dict written to config/student_profile.json with authenticated:true 🟡
   (no token/session object; "logged in" == a boolean flag in a JSON file; sign-out just flips the flag)
→ output: MainWindow._build_app_shell()
```
- **Logging:** none for login (no logging of auth events).
- **Failure handling:** wrong password → inline placeholder error; first-run auto-register swallows errors to a message.
- **Retry:** none.
- **Trust boundary:** device-local file system. Anyone with file access can read/write both JSON files.

### A2. Sign-out
`_sign_out()` sets `profile["authenticated"]=False`, saves, rebuilds UI. No invalidation of anything else (no tokens exist). 🔴 No session revocation possible; a copied `student_profile.json` replays "logged in".

### A3. API-key provisioning (SetupOverlay)
```
INPUT: Gemini key, OpenRouter key, OS
→ validation: both keys non-empty 🟡 (no format check, no live test)
→ storage: config/api_keys.json plaintext 🟡 (gitignored, but plaintext at rest; app busy-waits on its existence)
→ effect: wait_for_api_key() unblocks → Rina can connect
```
- **Failure:** invalid key → Gemini connect fails → infinite 3 s reconnect loop logs errors forever.

---

## B. Desktop app — Rina tutoring session

### B1. Voice/text turn
```
INPUT: mic PCM (16 kHz int16) via sounddevice OR typed text (QLineEdit)
→ audio queue (asyncio.Queue, maxsize 10) → Gemini Live session
→ Gemini returns: output audio + output/input transcriptions + tool calls
→ transcription → ui.write_log (in-app log) + memory extraction trigger
→ tool call → _execute_tool:
     • tool_allowed(name) from student_mode 🟢
     • save_memory → update_memory (long_term.json) 
     • shutdown_rina → os._exit(0) after 1 s
     • anything else → _disabled_action stub text (safe build)
→ response audio → RawOutputStream (24 kHz)
```
- **Trust boundary:** audio/text flows to Google Gemini (external). Transcripts and memory content leave the machine. Personal facts (name, city, etc.) are extracted and stored locally (see B2).
- **Validation:** text turns are sent as-is; no length caps, no content filtering beyond the model's own.
- **Failure/retry:** session errors → 3 s reconnect, forever. Mic errors → task raises → TaskGroup cancels the session → reconnect.
- **Logging:** `[RINA]`, tool calls `🔧 name args`, memory saves, errors via `logger.warning/error`; sensitive-ish data (tool args, first 80 chars of results) is logged.

### B2. Long-term memory (broken in practice)
```
turn (user_text, rina_text)
→ _update_memory_async (daemon thread)
→ should_extract_memory() → imports or_client (ModuleNotFoundError → caught → returns False) 🔴
→ extract_memory() → same import failure 🔴
→ format_memory_for_prompt() (memory → system prompt)
```
- **Confirmed:** the OpenRouter-backed extraction **never runs** because `or_client` source is absent. `save_memory` tool (direct JSON write) is the only path that works. So the "memory" feature is a **latent broken feature**, and the stored data (identity.name=Justin, long_term.json) came from earlier runs of a build that had the module.

### B3. Lesson selection & content load
```
INPUT: click in Learn tree
→ get_node_by_path(path) → manifests (LRU cache, 16 entries)
→ get_lesson_content(path) → lesson JSON (LRU cache, 3 entries / 4 MB; mtime+size invalidation) 🟢
→ _normalize_lesson_content (lists → strings) → sections render
→ get_source_links(path) → source_url/syllabus_url (https-only + host allowlist) + local book path 🟢
→ OfficialTextbookViewer:
     • local PDF present → open immediately (no network) 
     • else get_cached_official_pdf(url) → host allowlist, https, ≤200 MB, %PDF magic check, .cache/textbooks/ 🟢
→ page render via PyMuPDF; find_best_source_page fuzzy match (score ≥ 0.72 auto-jumps) 🟡
```
- **Failure:** `IllustrationLoadError` surfaces in the viewer status text; downloads resume from scratch (`.part` files cleaned on error).
- **Retry:** requests timeout (12,90) with no automatic retry in `illustration_loader` (the fetch *script* has urllib3 Retry, the runtime loader does not).

### B4. Quiz & progress
```
INPUT: radio-button answers
→ _submit_quiz → compare with lesson JSON "answer" field (client-side, visible to students) 🟡
→ record_quiz_score (clamp 0-100, keep last 50, xp += max(10, score//5))
→ touch_study_day (streak) → save student_profile.json → refresh UI
```
- The answer key ships with the lesson content — by design ("CheckBox answers"), but it means quizzes measure honesty, not knowledge.

---

## C. Letters web app

### C1. Public letter reading (no auth)
```
INPUT: page load → subscribeLetters()
→ Firestore onSnapshot(letters, orderBy createdAt desc) — real-time 🟢 (rules: read public)
→ MapCanvas renders pins; click → LetterOverlay → letter content
→ subscribeEchoes(letterId) → where letterId == … (indexed compound query) 
→ discoveredIds / threads persist to localStorage
```
- **Trust boundary:** client ← Firestore. All letter content is public by design.
- **Failure:** Firestore unavailable → onSnapshot error is unhandled (`subscribeLetters` callback never invoked; UI shows empty map silently) 🔴.
- **Validation:** none client-side; rules validate echoes fields on create.

### C2. Echo creation (anonymous)
```
INPUT: authorName, textContent (≤1600), type
→ createEcho → addDoc (no auth)
→ rules: keys hasOnly [letterId, authorName, textContent, type, lat, lng, createdAt];
   letterId/textContent strings; textContent ≤ 1600; type in [reply, independent_confession] 🟢
→ not enforced: length of authorName 🟡, lat/lng range 🟡, letterId existence (orphans possible) 🟡
→ local echo prepended in seed mode
```
- **Spam vector:** no rate limit on echo creation (Firestore rules have no throttling; a script can flood the collection) 🔴.

### C3. Admin letter publishing
```
INPUT: email+password → Firebase Auth signInWithEmailAndPassword
→ auth state → AdminWorkspace shows desk
→ form: title, dateString, locationName, secretClueTags, textContent, 3 optional files
→ uploadLetterAsset → Storage ref letters/{folder}/{ts}-{sanitized} (name sanitized: [^\w.-]+ → -) 
→ createLetter → addDoc (rules: write requires request.auth != null)
```
- **Authorization:** *any* authenticated Firebase user can publish letters and update/delete echoes — there is no admin role check server-side (see authorization-audit.md). The rules file is the *only* backend enforcement, and it only checks "is signed in" 🔴.
- **Validation:** `Number(coordinate.lat.toFixed(6))` etc. — no bounds check (lat/lng could be NaN → Firestore rejects; rules don't range-check) 🟡.
- **Failure:** upload errors surface as status text; no retry; partial state possible (some assets uploaded, letter not created → orphaned blobs) 🔴.

### C4. Notes reader (static)
```
INPUT: /notes/s{1,2,3} → loadLevel → dynamic import of raw .txt (bundled, ~111k lines total)
→ stripToc → splitIntoUnits (regex header matching) → parseSections (sub-section headers)
→ render; search filters units by name/rawText; read progress in localStorage
```
- **Validation:** none needed (static local data). Fragile parsing: unit detection is regex heuristic; missing units render "No structured content" + raw text fallback. 🟡

---

## D. Nested L2.0 app — AI tutor

```
INPUT: message (≤4000), optional image (PNG/JPEG/WebP base64 ≤ ~10.5 MB), lesson context, history (last 6, ≤1200 each)
→ server /api/ai/tutor (POST, json limit 12 MB)
→ rate limit: 20 / 10 min per sessionId (client-supplied or IP) 🟡 (spoofable sessionId, unbounded Map)
→ OpenAI responses.create (model gpt-5.6-terra default), store:false, max_output_tokens:1400
→ JSON {answer, model}
```
- **Trust boundary:** browser → localhost Express → OpenAI. Key stays server-side 🟢.
- **Failure:** 503 when unconfigured; 500 generic message on errors; 429 rate-limited; client shows error text.
- **Logging:** `console.error` only.
- **Security:** no origin check (any local webpage could POST to 127.0.0.1:8787 → CSRF-style abuse of the key quota) 🔴.

---

## E. Cross-cutting flows

### E1. Official library acquisition (scripts, offline)
```
fetch_official_library.py: seed category URLs → crawl course index (host-allowlisted, ≤300 visited)
→ resource links (file/direct_file/h5p/page/url/folder) → download (≤250 MB, sha256, .part staging)
→ acquisition_report.json (never bypasses login; HTML → report-only)
→ build_official_book_catalog.py: scan data/reb_student_books + official_books/files → catalog.json
   (sha256, page count via PyMuPDF, subject/kind inference, dedupe by checksum)
→ verify_official_library.py --rehash: re-hash and compare
```
- All three scripts are **untracked** — the pipeline is not reproducible from a fresh clone.

### E2. Curriculum generation (scripts, offline)
```
generate_lesson_content.py (legacy): Gemini gen → high_school.json lessons_content (progress .gen_progress.json)
reb_build_units.py: REB .txt → data/curriculum/math/{level}_unitN.json
build_full_access_curriculum.py: manifests → books/full/... (73 books / 408 units / 1,734 lessons; template guides + legacy enrichment)
validate_curriculum.py: JSON validity, ref containment, reachability, required fields, diagram types, cache bounds
```
- **Data-quality risk:** the "content" in most generated lessons is boilerplate; `provenance` marks it, but a school release must review each (DEPLOYMENT.md acknowledges this).

---

## F. Data-flow risk register

| # | Flow | Risk | Severity |
|---|---|---|---|
| F1 | Desktop login | "authenticated" flag file is forgeable; first-run auto-account | High (local) |
| F2 | API keys at rest | Plaintext keys in `config/api_keys.json` (Gemini, OpenRouter) | High |
| F3 | Memory extraction | Silent failure (missing `or_client`); when it worked, PII (name/age/preferences) written to plaintext JSON, included verbatim in system prompt sent to Google | Medium-High |
| F4 | Gemini session | User transcripts/audio sent to Google; no retention config, no user notice in-app | Medium |
| F5 | Echo creation | Unauthenticated, unthrottled writes; orphans allowed | Medium |
| F6 | Admin publish | Any signed-in user can write letters/echoes; no role check | High (if deployed) |
| F7 | Asset upload | Any signed-in user can upload to `letters/**`; no file-type/size enforcement in rules (client accept attr only); files publicly readable | Medium |
| F8 | L2.0 tutor | No origin check on localhost API; rate-limit spoofable | Low-Medium (local only) |
| F9 | Official PDF download | Host-allowlisted + magic check 🟢; content is official govt material — licensing/redistribution policy required (documented in DEPLOYMENT.md) | Policy |
| F10 | Curriculum content | Template-generated study guides presented inside the app; risk of factual drift vs official books | Medium (pedagogical) |