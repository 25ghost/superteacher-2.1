# EXECUTIVE SUMMARY — SuperTeacher / Letters Codebase Audit

**Audit date:** 2026-09-10 · **Scope:** full repository (2,693 tracked files; desktop PyQt app, React "Letters" web app, untracked "L2.0" nested copy) · **Method:** code-traced analysis; nothing modified.

**Bottom line:** The repo is a small team's working monorepo with two real products, a solid *data* architecture (lazy curriculum tree with bounded caches, allowlisted external fetches, path-traversal hardening), and **critical gaps in the security model**: Firestore object-level authorization is absent, desktop auth uses forgeable file-flags and fast SHA-256, several core modules are untracked (a fresh clone silently loses features), and there are **no tests, no CI, and no observability**. One feature (AI memory extraction) is broken at runtime because its dependency module source is missing.

---

## P0–P4 prioritization legend
**P0** = Critical / immediate security or correctness · **P1** = High risk · **P2** = Significant debt · **P3** = Improvement · **P4** = Nice-to-have

---

## Top 10 vulnerabilities

| # | Sev | ID | Finding |
|---|---|---|---|
| 1 | P0 | SEC-01 / AUTHZ-W1 | Firestore: any signed-in user can update/delete **any** letter or echo (no `ownerUid`, no admin check) |
| 2 | P0 | SEC-02 / AUTH-D1 | Desktop passwords: single-round SHA-256 + 4-char policy; trivial offline brute force |
| 3 | P0 | SEC-03 / AUTH-D6 | `ui.py` auth import fallback **fails open** — any non-empty username "logs in" if the module import breaks |
| 4 | P1 | SEC-04 | Gemini + OpenRouter API keys stored **plaintext** in `config/api_keys.json` |
| 5 | P1 | SEC-05 | Firestore `letters` write has **no field allowlist**; Storage `letters/**` writable by any authed user (publicly readable) |
| 6 | P1 | SEC-06 | Anonymous echo creation unthrottled → spam/cost; arbitrary `lat/lng` → map vandalism |
| 7 | P1 | SEC-07 | Memory pipeline sends PII to OpenRouter + stores plaintext + injects into Gemini prompt; **currently silently broken** (missing `or_client`) |
| 8 | P1 | SEC-08 | L2.0 localhost AI server has **no Origin check** → any webpage can burn the OpenAI key quota |
| 9 | P1 | SEC-09 | Gemini reconnect loop: infinite fixed 3 s retry; burns quota, no user-facing auth error |
| 10 | P2 | SEC-12 | Sensitive logging (tool args, memory values); dev logs at repo root leak user paths |

## Top 10 architectural problems

| # | ID | Finding |
|---|---|---|
| 1 | AP-01 | `ui.py` = 5,176-line god file (whole GUI) with fail-open imports |
| 2 | AP-02 | Zero automated tests; only hand-run data scripts |
| 3 | AP-16 | Core modules, 4 scripts, official-book data **untracked** → fresh clone loses the Learning Edition & library pipeline |
| 4 | AP-05 | Session = editable `authenticated` boolean flag; roles forgeable |
| 5 | AP-03 | Two coexisting curriculum formats (legacy `high_school.json`/`math/` vs manifest tree) |
| 6 | AP-04 | Monolithic tool dispatch: schemas/dispatcher/student-filter are 3 parallel structures that can drift |
| 7 | AP-07 | Fail-open degradation hides real breakage (auth, memory, untracked modules) |
| 8 | AP-11 | Placeholder UI pages (Missions/Classroom/Community) show fabricated data |
| 9 | AP-12 | No logging files, no metrics, no error reporting |
| 10 | AP-20 | 1,734 lessons largely template-generated study guides shipped as "content" |

## Top 10 dead-code candidates

| # | ID | Item | Class |
|---|---|---|---|
| 1 | DC-01 | `or_client` memory extraction (missing source, always fails) | CONFIRMED UNUSED |
| 2 | DC-12 | `rahura superteacher L 2.0/` whole untracked project | CONFIRMED UNUSED (intent unknown) |
| 3 | DC-05 | `core/subject_focus.json` (no importer) | CONFIRMED UNUSED |
| 4 | DC-22 | Duplicated histogram/pie/scatter branches in `lesson_visuals` | CONFIRMED UNUSED |
| 5 | DC-13 | 16 tool stubs + schemas in shipped build | CONFIRMED UNUSED (deliberate) |
| 6 | DC-04 | `src/notes` teacher guides/syllabus/PDF copies | LIKELY UNUSED |
| 7 | DC-07 | 11 one-shot data/asset scripts | LIKELY UNUSED |
| 8 | DC-03 | `data/curriculum/math/` outputs (legacy) | CONFIRMED UNUSED |
| 9 | DC-15 | Decorative classroom/community/missions content | LIKELY UNUSED |
| 10 | DC-06 | `scripts/generate_lesson_content.py` (superseded) | LIKELY UNUSED |

## Top 10 technical-debt items

1. Unpinned Python deps + local 3.14 vs deployed 3.11/3.12 (DR-1)
2. `echoes(letterId, createdAt)` Firestore composite index undocumented
3. JSON profile writes unlocked (AP-17)
4. Duplicated path/config helpers ×5 (AP-09)
5. Legacy curriculum readers in UI (`_find_math_unit_index`) (AP-03)
6. Hardcoded model name / magic strings (AP-10)
7. Mojibake + encoding artifacts in generated content (AP-15)
8. `dev-server*.log` + `tmp/` artifacts in working tree
9. Quiz answers ship with lessons (by design; document for schools)
10. `pillow` declared but unused at runtime

## Authentication risks
- Forgeable session flag + role (AUTH-D2) · fast hash (AUTH-D1) · first-run auto-account (AUTH-D3) · no lockout (AUTH-D4) · fail-open fallback (SEC-03) · web: no admin claim, no ownership (AUTH-W1).

## Authorization risks
- No ownership fields anywhere in Firestore (AUTHZ-W1) · letters writes unvalidated (AUTHZ-W2) · any authenticated user = admin (AUTHZ-W3) · anonymous spam (AUTHZ-W4) · client-editable role on desktop (AUTHZ-D1) · localhost AI server open (AUTHZ-L1).

## Data-flow risks
- Memory PII egress/storage (F3) · transcripts to Google (F4) · orphaned storage blobs on partial uploads (F7) · seed/hybrid web modes diverge by config (F-13) · template content as curriculum (F10).

## Pipeline risks
- Infinite reconnect (P2) · silent memory failure (P4) · no retry on PDF download (P5) · Firestore outage renders empty map silently (P7) · untracked library pipeline (P9) · no CI gate (P10).

## Database risks
- No owner fields (SEC-01) · no pagination (P-7) · orphaned echoes/blobs · undocumented composite index · no retention/backup policy · plaintext local JSON.

## Performance risks
- Full-collection Firestore reads (P-7) · 111k-line textbook text in bundle (P-8) · per-frame full canvas redraws (P-9) · unmemoized curriculum path traversal (P-1) · unbounded L2.0 rate map (P-12).

---

## Recommended remediation order

| Phase | Work | Est. |
|---|---|---|
| 1 (immediate) | Track untracked core modules + scripts; add `ownerUid`/admin rules to Firestore; fail-closed auth; document composite index | 1–2 days |
| 2 (week 1) | Argon2id + session token + lockout; keyring for API keys; fix/remove `or_client`; reconnect backoff | 2–3 days |
| 3 (week 2) | Tool registry refactor; split `ui.py`; pytest/Vitest for core + web; CI (validate → test → build → smoke) | 1 week |
| 4 (week 3) | Firestore pagination + counters; notes JSON prebuild; error toasts + ErrorBoundary; logging file | 1 week |
| 5 (later) | L2.0 fate decision; placeholder-page cleanup; content review gate for released subjects; observability | ongoing |

---

# WHAT I WOULD FIX FIRST

The 10 highest-value changes, ordered by impact and risk (impact ↑, risk ↓):

1. **Commit the untracked Python modules and scripts** (`core/official_book_content.py`, `core/official_book_library.py`, the 4 library/verification scripts, plus decide on the 106 PDFs). A fresh clone today silently loses the Official Learning Edition — this is a 10-minute change that unblocks every other fix and stops silent feature loss.
2. **Harden `firebase.rules` with ownership and admin checks.** Add `ownerUid` on letters/echoes, `allow write: if request.auth.uid == resource.data.ownerUid`, an admin-uid allowlist, and a letters field allowlist + size caps. One rules file, high impact, near-zero regression risk.
3. **Fail closed on auth import failure in `ui.py`** (remove the `(bool(u.strip()), "Signed in.", "student")` fallback) and log loudly. Tiny change, removes a silent auth bypass.
4. **Upgrade desktop password hashing to Argon2id/PBKDF2** with per-account salt, ≥ 8-char policy, and read-time migration of existing hashes. Keeps the same file format family (self-describing `scheme:salt:hash`).
5. **Replace the `authenticated` flag with a device session token** (random 256-bit token file + expiry + HMAC-signed role) so role/`student_mode` can't be flipped by editing JSON.
6. **Move API keys into the OS keyring** (`keyring` package) with a file fallback for the offline school build; keep keys out of logs.
7. **Add exponential backoff + auth-error fast-fail to the Gemini reconnect loop** so a bad key shows "check your API key" instead of an infinite retry storm.
8. **Fix or remove the `or_client` memory path.** Either vendor the module (or port to `google-genai`/direct OpenRouter REST with the key from config) or delete the dead extraction and keep only the `save_memory` tool — and surface memory status in the UI either way.
9. **Stand up a minimal CI:** run `validate_curriculum.py`, `verify_official_library.py --rehash`, a first pytest batch for `core/`, `vite build`, and the two offscreen smoke scripts. This converts the release checklist into a gate and starts closing the "no tests" hole.
10. **Split `ui.py` into modules** (`pages/`, `widgets/`, `lesson_view.py`, `pdf_viewer.py`, `chat.py`) behind the existing `JarvisUI` facade — the largest debt item, but mechanical, and it makes every subsequent change (auth, quizzes, PDF viewer) testable and reviewable.

*Do first: items 1–3 (days). Next: 4–8 (a week). Then 9–10 (ongoing).*