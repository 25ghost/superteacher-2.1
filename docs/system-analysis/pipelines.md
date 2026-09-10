# Phase 9 — Pipelines

Every meaningful pipeline, with trigger → steps → output, plus failure/retry/timeout/transaction/race/security/observability notes.

---

## P1 · Desktop app startup

```
python main.py
→ logging.basicConfig (console)
→ JarvisUI() → QApplication → MainWindow (reads student_profile.json; authenticated? shell : auth landing)
→ main(): daemon thread runner
   → wait_for_api_key()  (busy-loop 0.1 s until config/api_keys.json has gemini+openrouter+os)
   → wait_for_rina_activation() (blocks on threading.Event)
   → asyncio.run(JarvisLive.run())
→ ui.root.mainloop()
```
- **Failure points:** missing keys → indefinite busy-wait (no user feedback until overlay); `or_client` import failure (silent); PyQt6 missing → crash.
- **Observability:** console logs only.
- **Security boundary:** UI thread and AI thread both run as the OS user; no sandbox.

## P2 · Gemini Live session lifecycle (the RINA loop)

```
connect() → TaskGroup:
  _send_realtime: out_queue → session.send_realtime_input (PCM 16k)
  _listen_audio: sounddevice InputStream → callback → out_queue (maxsize 10)
  _receive_audio: session.receive()
      ├─ audio data → audio_in_queue
      ├─ transcriptions → buffers → turn_complete → UI log + _update_memory_async (daemon)
      └─ tool_call → _execute_tool → send_tool_response
  _play_audio: audio_in_queue → RawOutputStream (24k)
session close (lesson switch) → loop → reconnect in 3 s (forever)
```
- **Failure points:** mic unavailable; network drop; quota (429); session close on lesson switch mid-turn.
- **Retry:** fixed 3 s, infinite, no backoff — **P0-ish availability/cost issue** (see SEC-09).
- **Race:** `self.session` replaced on reconnect while `_on_lesson_selected` may `close()` a stale session; `_pending_queue` shared across threads.
- **Observability:** `logger.info/error` + `write_log`; no structured session metrics.
- **Security boundary:** transcripts and system prompt (which embeds long-term memory) leave the machine to Google.

## P3 · Tool execution

```
model tool_call → tool_allowed(name)? (student_mode)
→ dispatcher if/elif chain → run_in_executor(thread) for sync tools
→ result → FunctionResponse
```
- **Failure:** per-tool try/except → `speak_error` → result string. Blocked tools return `blocked_message`.
- **Retry:** none (model may re-call).
- **Security:** student_mode + ACTION_TOOLS_AVAILABLE stubs; only save_memory/shutdown_rina live.

## P4 · Memory write path

```
turn → _update_memory_async (daemon thread)
→ should_extract_memory() → or_client (ModuleNotFoundError → False)  ← BROKEN
→ extract_memory() → or_client (fails) ← BROKEN
→ update_memory() → long_term.json (Lock-protected) ← only save_memory tool uses this
→ format_memory_for_prompt() → system prompt (truncated to 2,000 chars)
```
- **Failure:** silent (prints to console). **No logging of the missing module** beyond a warning that's swallowed.
- **Security:** PII at rest + PII egress to OpenRouter/Gemini when working.

## P5 · Lesson open

```
click → get_node_by_path (manifests, LRU 16) → get_lesson_content (LRU 3 / 4 MB)
→ normalize → render sections + diagrams (MathDiagramWidget) + media resolve (approved roots)
→ get_source_links → OfficialTextbookViewer:
    local_path? open immediately
    : get_cached_official_pdf(url) → host allowlist → stream ≤200 MB → %PDF check → cache
→ page render (PyMuPDF) → find_best_source_page (score≥0.72 auto-jump)
```
- **Failure:** `IllustrationLoadError` shown in viewer; missing lesson JSON → fallback `_auto_lesson_content` (legacy path).
- **Retry:** download has timeout (12,90) but **no retry**; user clicks again.
- **Security:** SSRF-hardened (allowlist + https + magic bytes + size caps). ✅
- **Observability:** status label only.

## P6 · Build (web Letters app)

```
npm run dev / build (Vite)
→ index.html → src/main.jsx → App.jsx routes
→ imports: components (lazy) + services/letters.js + noteParser (dynamic import of raw txt)
→ output: dist/ (7.7 MB)
```
- **Failure:** missing `.env` → Firebase disabled → seed mode (by design); large txt imports slow build.
- **Performance:** 111k lines of raw text bundled — main chunk includes all S1–S3 texts via dynamic import (split per level, but each ~25k lines).

## P7 · Letters web data flow (real-time)

```
subscribeLetters → onSnapshot (orderBy createdAt desc)
subscribeEchoes(letterId) → where + orderBy
createEcho → addDoc (rules validated) → onSnapshot updates UI
createLetter (admin) → uploads (Storage) → addDoc
```
- **Failure:** Firestore outage → empty map (silent); upload partial failure → orphaned blobs; `onSnapshot` errors unhandled.
- **Retry:** none.
- **Security:** rules as analyzed (SEC-01/05/06).

## P8 · Curriculum generation (offline build)

```
generate_lesson_content.py (legacy, Gemini) → high_school.json lessons_content + .gen_progress.json
reb_build_units.py → data/curriculum/math/{level}_unitN.json (REB txt → regex split)
build_full_access_curriculum.py --legacy-source high_school.json
   → manifests → books/full/** (73 books, 408 units, 1,734 lessons)
   → enrichment: legacy content where present, else template study guide (provenance marked)
validate_curriculum.py → all JSON, refs, reachability, required fields, diagram types, cache bounds
```
- **Failure:** generator retries 429 with backoff (good); validator `assert` fails on any issue.
- **Retry:** generation: 5 attempts with 30 s/15 s backoff; build script: none needed.
- **Observability:** stdout prints; `.gen_progress.json` for resume.

## P9 · Official library pipeline (offline)

```
fetch_official_library.py [--download-public]
   → crawl category pages (≤300 visited) → course pages → resources
   → download files (≤250 MB, sha256, .part staging) → data/official_books/files/
   → acquisition_report.json (login/HTML → report-only; never bypass auth)
build_official_book_catalog.py → scan reb_student_books + files/ → catalog.json (sha256, dedupe, subject inference)
verify_official_library.py --rehash → re-hash + compare → summary
```
- **Failure:** 429s handled via urllib3 Retry (3, backoff 1.0, status_forcelist incl. 429); timeouts (45,90)/(12,90); `.part` cleanup on error.
- **Security:** host allowlist + https + content-type checks + size caps. ✅ (scripts untracked — reproducibility gap)

## P10 · Deployment pipeline (school)

```
Windows 10/11 → python -m pip install -r requirements.txt → python main.py
preflight: verify_official_library.py --rehash; validate_curriculum.py; render smoke tests
```
- **Failure:** no CI; manual runbooks (DEPLOYMENT.md).
- **Observability:** none built-in.

## P11 · L2.0 AI tutor pipeline (nested app)

```
browser POST /api/ai/tutor {message≤4000, image?, lesson, level, history≤6×1200, sessionId}
→ rate limit 20/10min per sessionId|ip
→ OpenAI responses.create (store:false, max 1400 tokens)
→ {answer, model}
```
- **Failure:** 503 unconfigured; 429; 400; 500 generic. Timeout: none set on OpenAI call (default).
- **Security:** key server-side; no Origin check (SEC-08); in-memory Map unbounded.

## P12 · Remotion render (nested app, not shipped)

```
remotion render src/remotion/index.ts MathConcept output/math-concept.mp4
```
- Standalone; used for video marketing assets.

---

## Pipeline risk register

| Pipeline | Top risk | Suggested fix |
|---|---|---|
| P2 Gemini loop | Infinite 3 s reconnect, quota burn | Backoff + auth-error fast-fail |
| P4 Memory | Silent breakage + PII handling | Fix/remove `or_client`; add visible status; encrypt at rest |
| P5 PDF download | No retry; REB site flakiness | Retry with backoff; resume via Range |
| P7 Firestore | Silent outage, orphaned uploads | Error banners; transactional create; cleanup job |
| P8 Curriculum gen | Template content shipped as real | Review-gate `status: ready`; provenance UI |
| P9 Library | Untracked scripts/data | Commit scripts; document PDF acquisition |
| P11 L2.0 | No origin check, unbounded map | Origin validation; bounded TTL map |