# Phase 6 — Security / Vulnerability Audit

Defensive audit. Each finding: ID, severity, location, problem, why it matters, attack scenario, evidence, remediation, confidence. **Nothing was exploited; analysis only.**

---

## CRITICAL

### SEC-01 · Firestore object-level authorization: any signed-in user can modify/delete any letter or echo
- **Location:** `firebase.rules` (`letters` write: `request.auth != null`; `echoes` update/delete: `request.auth != null`); no `ownerUid` written by `AdminWorkspace`/`letters.js`.
- **Problem:** No ownership or role check on any authenticated write.
- **Why it matters:** The admin desk is a public route; any user who creates a Firebase account can overwrite/delete every letter and echo, and upload arbitrary content.
- **Attack scenario:** 1) Attacker signs in at `/admin` with any email/password. 2) Using Firestore REST/SDK, `update` any `letters/{id}` (change textContent to defacement) or `delete` it. 3) Overwrites audioUrl with a malicious URL served to all public readers.
- **Evidence:** `firebase.rules` lines for `letters` and `echoes`; `AdminWorkspace.jsx` publishes with no role check; `letters.js` never stores the uid.
- **Remediation:** Add `ownerUid` on create (`request.auth.uid`); rule `allow write: if request.auth.uid == resource.data.ownerUid`; maintain an admin-uid allowlist for delete/any.
- **Confidence:** Confirmed (rules + code read).

### SEC-02 · Desktop passwords hashed with single-round unkeyed SHA-256; 4-char minimum
- **Location:** `core/local_auth.py` `_hash_password`.
- **Problem:** Fast hash, trivial offline brute force; weak policy.
- **Attack scenario:** Attacker copies `config/accounts.json` (world-readable file) → GPU hash-crack 4-char passwords in seconds; then edits `student_profile.json` to `role: teacher`.
- **Remediation:** Argon2id/PBKDF2; ≥ 8-char policy; file ACLs.
- **Confidence:** Confirmed.

### SEC-03 · Auth fallback in `ui.py` fails open
- **Location:** `ui.py` lines ~99–105 (try/except around `core.local_auth` import).
- **Problem:** If the import fails (broken install, partial PyInstaller bundle), `authenticate(u,p)` returns success for any non-empty username.
- **Attack scenario:** Corrupt/rename `core/local_auth.py` → everyone logs in as `student` (and could hand-edit profile to teacher).
- **Remediation:** Fail closed; log loudly.
- **Confidence:** Confirmed.

---

## HIGH

### SEC-04 · API keys stored plaintext on disk (Gemini + OpenRouter)
- **Location:** `config/api_keys.json` (gitignored, but plaintext).
- **Problem:** Any local user/process/backup can read both keys; cost abuse possible.
- **Attack scenario:** Malware or shared-lab user reads the file → drains Gemini/OpenRouter quota or uses keys for their own calls.
- **Remediation:** OS keychain (Windows Credential Manager via `keyring`), restrict ACLs, separate per-deployment keys (DEPLOYMENT.md already advises).
- **Confidence:** Confirmed (file read; values masked in this report).

### SEC-05 · Letters `write` unvalidated fields + storage writes unconstrained
- **Location:** `firebase.rules` (letters), `storage.rules` (`letters/{allPaths=**}`).
- **Problem:** Arbitrary fields/sizes in letters docs; authenticated users can write any blob path under `letters/` (overwrite existing assets, store non-image content served publicly).
- **Remediation:** Field allowlist + size caps in rules; path-bound to `ownerUid`; content-type checks.
- **Confidence:** Confirmed.

### SEC-06 · Anonymous echo creation with no throttling (spam/abuse)
- **Location:** `firebase.rules` echoes create (public); `LetterOverlay.handleSubmit`.
- **Problem:** Scriptable flood of docs → cost + content moderation burden; map vandalism via arbitrary `lat`/`lng`.
- **Remediation:** Rate-limit via Firestore (e.g., `allow create: if request.time < ... ` or App Check), validate lat/lng ranges and authorName length.
- **Confidence:** Confirmed.

### SEC-07 · Desktop memory pipeline sends PII to a third party and stores it plaintext (when functional)
- **Location:** `memory/memory_manager.py` (`should_extract_memory`/`extract_memory` via `or_client` → OpenRouter; writes `memory/long_term.json`); `main.py` `_build_config` injects memory into the Gemini system prompt.
- **Problem:** Personal facts (name, age, city, family) are (a) sent to OpenRouter for classification/extraction, (b) stored unencrypted, (c) sent to Google Gemini in every session, (d) **currently broken silently** (`or_client` missing).
- **Remediation:** Decide policy; encrypt at rest; allow users to view/delete; fix or remove the broken import; consider local-only extraction (e.g., on-device NER) to avoid PII egress.
- **Confidence:** Confirmed (code); "when functional" — current runtime is broken.

### SEC-08 · No origin check on the L2.0 localhost AI server (CSRF-style quota abuse)
- **Location:** `rahura superteacher L 2.0/server/index.mjs` `/api/ai/tutor`.
- **Problem:** Any webpage running in the user's browser can POST to `127.0.0.1:8787` (no CORS/Origin validation), spending the OpenAI key.
- **Remediation:** Validate `Origin`/`Referer`; require a local bearer token.
- **Confidence:** Confirmed.

### SEC-09 · Infinite 3-second Gemini reconnect loop (availability/DoS of own app; cost)
- **Location:** `main.py` `JarvisLive.run` (`while True: ... await asyncio.sleep(3)`).
- **Problem:** Any persistent error (bad key, quota, network) spins forever, hammering the API and pinning CPU/audio tasks.
- **Remediation:** Backoff with cap, distinct handling for auth errors (stop and prompt user).
- **Confidence:** Confirmed.

---

## MEDIUM / LOW

### SEC-10 · XSS surface in `highlightText` (React) — low risk, but check
- **Location:** `src/components/NotesReader.jsx` `highlightText`.
- **Problem:** Uses React elements (`<mark>`), not `dangerouslySetInnerHTML` — **no XSS found**. `textContent` rendered as text everywhere in the app (React escapes). Low risk noted as verified-good.
- **Confidence:** Verified no XSS.

### SEC-11 · CSV/PDF/text lesson content rendered as text — no injection path found
- **Location:** `ui.py` `_lesson_section`, `OfficialTextbookViewer`.
- **Problem:** Qt `QLabel` with plain text — no HTML parsing enabled for lesson bodies (no `setTextFormat(RichText)`). Verified: lesson JSON could contain `<img onerror=...>` but QLabel default renders it as literal text. Low risk.
- **Confidence:** Verified low risk (QLabel plain-text default).

### SEC-12 · Verbose local errors / logs
- **Location:** `main.py` `logger.info(f"🔧 {name}  {args}")`, `traceback.print_exc()`; `dev-server.err.log` (absolute Windows user path committed).
- **Problem:** Tool args (which can include user data like message text) logged; stack traces to console; dev log at repo root leaks the developer's username path.
- **Remediation:** Redact args; stop tracking `dev-server*.log` (they're untracked but present; add to `.gitignore`).
- **Confidence:** Confirmed.

### SEC-13 · `QDesktopServices.openUrl` opens URLs from lesson metadata
- **Location:** `ui.py` lines 3566–3584 (`source_url`, `syllabus_url`, `local_path`).
- **Problem:** Only https URLs from approved hosts are surfaced via `get_source_links` (validated in `curriculum_loader` and `validate_curriculum`), so external-open risk is low. `QUrl.fromLocalFile` for `source_path` — path comes from catalog (checked to be `.pdf` under approved roots). Low.
- **Confidence:** Verified; guarded upstream.

### SEC-14 · `shutdown_rina` calls `os._exit(0)` from a daemon thread
- **Location:** `main.py` `_execute_tool`.
- **Problem:** Not a security issue, but abrupt exit can corrupt JSON writes (memory/profile saves are small & atomic-ish via `write_text`). Operational.
- **Confidence:** Confirmed.

### SEC-15 · `illustration_loader` download lacks retry and is a single point of failure
- **Location:** `core/illustration_loader.py`.
- **Problem:** No retry (unlike the fetch script), 200 MB cap enforced by content-length + streaming count (good). REB sites may be slow → timeout (12,90) aborts; user retries manually. Availability risk, not integrity.
- **Confidence:** Confirmed.

### SEC-16 · `.env.example` references a real-looking Firebase project (`your-project…` placeholders) — fine. No `.env` present — Firebase unconfigured by default (no accidental exposure).
- **Confidence:** Verified.

### SEC-17 · `secretClueTags`/letters data publicly readable includes GPS coordinates and audio files of "secret" letters — product design; call out privacy implications for contributors.
- **Confidence:** Confirmed by design.

### SEC-18 · Template-generated curriculum content may contain inaccurate teaching material
- **Location:** `data/curriculum/books/full/**` (`provenance: "SuperTeacher structured study guide generated…"`), `scripts/build_full_access_curriculum.py`.
- **Problem:** Pedagogical integrity risk: 1,734 lessons of which many are templated boilerplate. Not a runtime vulnerability, but a correctness/trust issue for a school product.
- **Confidence:** Confirmed via sample lesson + script.

---

## Positive controls verified

- Curriculum JSON path reads are **path-traversal-safe** (`curriculum_loader._safe_json_path`, `resolve_lesson_media` root checks, `official_book_library._safe_catalog_path`).
- Official PDF downloads are **host-allowlisted + https-only + magic-bytes checked + size-bounded**.
- Firestore echoes create has a **field allowlist + length/type constraints** (best-in-repo rule).
- L2.0 server keeps the OpenAI key **off the browser**, caps request size, and sets basic security headers.
- React rendering is **XSS-safe by default**; no `dangerouslySetInnerHTML` in the codebase.
- Secrets are **gitignored** and were never committed (`git grep` for key patterns across history found nothing).

---

## Priority remediation order

1. SEC-01 (rules ownership) — one rules-file change, high impact.
2. SEC-02 + SEC-03 (desktop hashing + fail-open) — core auth hardening.
3. SEC-04 (key storage) — keychain integration.
4. SEC-05/SEC-06 (rules hardening + throttling).
5. SEC-07 (memory PII policy + fix/remove `or_client`).
6. SEC-08 (origin check), SEC-09 (backoff).
7. SEC-12 (log hygiene).