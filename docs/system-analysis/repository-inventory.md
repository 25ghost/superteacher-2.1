# Phase 1 — Repository Inventory

**Date of analysis:** 2026-09-10
**Branch:** main (65 commits visible; shallow clone)
**Tracked files:** 2,693 · **Working-tree additions:** 16 untracked, 166 modified

---

## 1. Languages and frameworks

| Stack | Where | Notes |
|---|---|---|
| Python 3.11/3.12 (target) · running 3.14 locally | Desktop app | PyQt6 GUI, asyncio, `google-genai` (Gemini Live API) |
| JavaScript / JSX (React 18) | "Letters" web app at repo root | Vite 6, Tailwind 3, Firebase SDK 10 |
| TypeScript / React 18 | Nested `rahura superteacher L 2.0/` app | Remotion 4, Express 5, OpenAI SDK — **untracked working copy** |
| HTML/CSS | Both web apps | Tailwind-driven |

## 2. Frontend applications

1. **"Letters" SPA** (`index.html`, `src/`, `vite.config.js`) — a public interactive world map of "letters" (geocaching-style notes), an admin desk (Firebase Auth), and a mathematics notes reader (REB S1–S3 texts bundled as raw `.txt`).
   - Routes (client-side, no router library): `/` → `PublicMapExperience`, `/admin` → `AdminWorkspace`, `/notes` → `NotesIndex`, `/notes/s[1-3]` → `NotesReader`.
   - Firebase is optional: with no `.env`, the app runs on seed/demo data.
2. **"Rahura SuperTeacher L 2.0"** (`rahura superteacher L 2.0/`) — a separate React/TS curriculum app with a local Express + OpenAI tutor backend and Remotion video tooling. **Not tracked by git and not in `.gitignore`** — a stray working copy that would be committed wholesale if `git add -A` were ever run.

## 3. Backend applications / services

1. **SuperTeacher desktop app** (`main.py` + `ui.py`) — the primary product. A PyQt6 desktop learning app (RINA tutor) with:
   - Gemini Live bidirectional voice/text session (`main.py` → `JarvisLive`)
   - Lazy-loaded Rwanda REB/O-Level/A-Level/TVET curriculum browser
   - Offline lesson reading, quizzes, missions, profile, and an "Official Learning Edition" PDF viewer
2. **Express AI server** (nested app only, `rahura superteacher L 2.0/server/index.mjs`) — proxies learner questions to OpenAI; binds to `127.0.0.1:8787`.

## 4. APIs

| API | Client | Purpose |
|---|---|---|
| Gemini Live (`models/gemini-2.5-flash-native-audio-preview-12-2025`) | `main.py` | Real-time voice tutoring session (v1beta) |
| Gemini `generate_content` (`gemini-2.5-flash-lite`) | `scripts/generate_lesson_content.py` | Legacy one-off lesson-content generation |
| OpenRouter (`or_client` module) | `memory/memory_manager.py` | Memory relevance check + extraction — **module source missing (only `__pycache__/or_client.cpython-314.pyc` exists)** |
| OpenAI `responses.create` | nested `server/index.mjs` | Rina tutor in the L2.0 app (key from `.env.local`) |
| Firebase Auth / Firestore / Storage | `src/lib/firebase.js` | Letters app auth, data, uploads |
| OpenStreetMap tiles | `src/components/MapCanvas.jsx` | Map rendering (a/b/c.tile.openstreetmap.org) |
| REB/RTB e-learning hosts (`elearning.reb.rw`, `*.rtb.gov.rw`) | `core/illustration_loader.py`, `scripts/fetch_official_library.py` | On-demand official textbook downloads (host-allowlisted) |

## 5. Databases

| Store | Type | Used by |
|---|---|---|
| Firestore (`letters`, `echoes` collections) | NoSQL, cloud | Letters web app (if configured) |
| `config/accounts.json` | JSON file | Desktop local auth |
| `config/student_profile.json` | JSON file | Desktop profile/progress |
| `memory/long_term.json` | JSON file | Desktop tutor long-term memory |
| `data/curriculum/**` (2,247 JSON files) | JSON file tree | Desktop curriculum (index → manifests → books → units → lessons) |
| `data/official_books/catalog.json` | JSON file | Official book catalog (102 entries) |
| `data/reb_resources.json` | JSON file | REB study-order metadata |

There is **no SQL database, no ORM, no migrations** anywhere.

## 6. Storage systems

- Firebase Storage (`letters/{folder}/…`) for letter assets (web app; rules committed).
- Local `.cache/textbooks/` (gitignored) for downloaded official PDFs (desktop).
- `data/reb_student_books/` (106 PDFs) — **untracked** local official books.
- `data/reb_books/` (18 tracked legacy files: PDFs + extracted `.txt`).
- `data/official_books/files/` — currently empty (download staging area).
- `src/notes/*.txt` — 111k lines of REB math text bundled into the Letters web build.
- `assets/` (359 tracked images) and `public/assets/` (8 reference images).

## 7. Authentication providers

| Provider | Where | Notes |
|---|---|---|
| Firebase Auth (email/password) | Letters `/admin` | Only gate for the admin desk |
| Local file-based auth | Desktop (`core/local_auth.py`) | SHA-256 (salted-prefix, unsalted scheme) stored in `config/accounts.json` |
| Gemini API key | Desktop | Plaintext in `config/api_keys.json` (gitignored) |
| OpenRouter API key | Desktop | Plaintext in `config/api_keys.json` (gitignored) |
| OpenAI API key | Nested L2.0 app | `.env.local` (server-side) |

## 8. Authorization mechanisms

- Desktop: `core/student_mode.py` — role from `student_profile.json`; `student` restricts tool allowlist/blocklist; teacher/other roles get all (disabled) tools.
- Desktop: tool-level gate `tool_allowed()` in `_execute_tool`.
- Web: Firestore security rules — `letters` read public / write requires any auth; `echoes` create public with field validation, update/delete requires any auth. **No role or ownership checks anywhere.**
- No RBAC, no claims, no row-level security.

## 9. External APIs / services

See Phase 11 (`external-dependencies.md`) for the full table. Summary: Google Gemini (Live + generate), OpenRouter, OpenAI, Firebase (Auth/Firestore/Storage), OpenStreetMap tiles, REB/RTB e-learning sites, PyPI + npm registries.

## 10. Background workers / jobs

- Desktop: memory extraction runs on a daemon thread per turn (`_update_memory_async`).
- Desktop: PDF download/render and page-matching run in daemon threads.
- Desktop: audio capture/playback run as asyncio tasks in a `TaskGroup`.
- Desktop: `shutdown_rina` schedules `os._exit(0)` on a daemon thread.
- Nested L2.0: rate-limit bookkeeping is in-memory only.

## 11. Queues / event systems

- Desktop: `asyncio.Queue` for outbound audio (maxsize 10) and inbound audio.
- Desktop: Qt signals (`pyqtSignal`) for UI↔thread communication (`_log_sig`, `_state_sig`, `_loaded`, `_page_found`).
- Nested L2.0: none (in-memory `Map` for rate limiting).
- No durable queue (Redis/SQS/Kafka) anywhere.

## 12. Cron / scheduled tasks

- None. (The `reminder` tool that would use Windows Task Scheduler is a disabled stub in the safe build.)

## 13. Webhooks

- None.

## 14. CLI tools

- 20 scripts under `scripts/` (see item 16), including:
  - `validate_curriculum.py` — validates all JSON + reachable lessons + cache bounds
  - `fetch_official_library.py` — inventories/downloads public REB/RTB resources
  - `verify_official_library.py --rehash` — checksum verification of catalog
  - `build_official_book_catalog.py` — rebuilds `catalog.json` from local PDFs
  - `build_full_access_curriculum.py` — generates the 1,734-lesson study-guide tree
  - `reb_build_units.py` — extracts REB unit content into legacy unit JSON
  - `generate_lesson_content.py` — one-off Gemini lesson generation (legacy)
  - Diagram/asset scripts: `discover_figures.py`, `extract_figure_pages.py`, `integrate_diagrams.py`, `add_lesson_illustrations.py`, `revert_diagrams.py`, `generate_assets.py`, `render_visual_smoke.py`, `render_learning_edition_smoke.py`, `cleanup_params.py`, `clean_unicode.py`, `verify_output.py`

## 15. Scripts

| Script | Purpose | Tracked? |
|---|---|---|
| `scripts/build_full_access_curriculum.py` | Generate the full lesson tree (template study guides) | ✅ |
| `scripts/reb_build_units.py` | Split REB math text into per-unit JSON (legacy `data/curriculum/math`, `high_school.json` era) | ✅ |
| `scripts/validate_curriculum.py` | Full curriculum validation | ✅ |
| `scripts/generate_lesson_content.py` | Legacy Gemini content generation (S1 math) | ✅ |
| `scripts/clean_unicode.py`, `cleanup_params.py`, `verify_output.py` | Data cleanup/checks | ✅ |
| `scripts/extract_params.py`, `extract_figure_pages.py`, `discover_figures.py`, `integrate_diagrams.py`, `add_lesson_illustrations.py`, `revert_diagrams.py`, `generate_assets.py` | PDF figure discovery / diagram wiring | ✅ |
| `scripts/render_visual_smoke.py` | Offscreen render of diagram widgets | ✅ |
| `scripts/build_official_book_catalog.py` | Catalog builder | ❌ **untracked** |
| `scripts/fetch_official_library.py` | REB/RTB importer | ❌ **untracked** |
| `scripts/verify_official_library.py` | Catalog integrity check | ❌ **untracked** |
| `scripts/render_learning_edition_smoke.py` | Offscreen PDF viewer smoke test | ❌ **untracked** |
| `scripts/download_reb_student_books.ps1` | (listed in dir; not tracked) PowerShell downloader | ❌ **untracked** |

## 16. Infrastructure / deployment configuration

- `DEPLOYMENT.md` — school deployment runbook (Windows 10/11, Python 3.11/3.12, 4–8 GB RAM).
- `Launch SuperTeacher.bat` — launcher for the desktop app.
- `vite.config.js` — Vite dev server bound to `127.0.0.1:5173`.
- `firebase.rules`, `storage.rules` — Firestore/Storage security rules (committed, presumably deployed to the Firebase project).

## 17. Docker / container configuration

- **None.** No `Dockerfile`, no `docker-compose*`, no container CI.

## 18. CI/CD

- **None.** No `.github/`, no YAML pipelines, no build servers. The repo relies on manual runs of `scripts/validate_curriculum.py`, `verify_official_library.py`, and the two smoke render scripts.

## 19. Testing infrastructure

- **No unit/integration test suites.** The only "tests" are:
  - `scripts/validate_curriculum.py` (assertion-based validation of data)
  - `scripts/verify_official_library.py` (checksum verification)
  - `scripts/render_visual_smoke.py` / `render_learning_edition_smoke.py` (offscreen render checks, `QT_QPA_PLATFORM=offscreen`)
  - Nested app: `verify-content.mjs`
- No pytest/unittest files, no Jest/Vitest files.

## 20. Monitoring / logging

- Desktop: Python `logging` to console (`main.py`), plus an in-UI log widget (`LogWidget`). Errors surface via `speak_error` and `traceback.print_exc`.
- `dev-server.log` / `dev-server.err.log` committed at repo root (Vite dev logs — **should not be tracked**).
- Web: no analytics, no error reporting (no Sentry etc.).
- No metrics, no tracing, no alerting.

## 21. Environment / configuration files

| File | Tracked | Contents |
|---|---|---|
| `.env.example` | ✅ | Firebase vars template for Letters app |
| `config/api_keys.json` | ❌ gitignored | **Real** Gemini + OpenRouter keys (plaintext, on disk) |
| `config/accounts.json` | ❌ gitignored | **Real** local account w/ SHA-256 hash |
| `config/student_profile.json` | ❌ gitignored | Real student profile, `student_mode: true` |
| `config/paths.json` | ✅ | REB book paths |
| `config/api_keys.example.json` / `accounts.example.json` | ✅ | Templates |
| `memory/long_term.json` | ❌ gitignored | Personal memory data |
| `.env` | — | Does not exist (Firebase unconfigured by default) |
| Nested `rahura superteacher L 2.0/.env.local` | ❌ | OpenAI key (server-side; not present) |

**Important:** `config/accounts.example.json` contains the *literal text* `sha256...only` — the example is a placeholder, not a real hash.

## 22. Database migrations

- None. All data stores are JSON files or Firestore collections without versioned schemas. `catalog.json` and `acquisition_report.json` carry a `schema_version` field; curriculum manifests are versionless.

## 23. Seed / demo data

- `src/data/seedLetters.js` — 4 demo letters + 2 echoes for the unconfigured-Firebase mode.
- `data/curriculum/**` — full curriculum (73 books, 408 units, 1,734 lessons).
- `data/reb_resources.json` — REB study order (Primary 4 → A-Level).
- `core/subject_focus.json` — per-subject teaching guidance prompts (44 subjects).
- `memory/long_term.json` — one real entry (`identity.name = "Justin"`).

## 24. Generated code

- `dist/` — Vite build output (gitignored; present on disk, 7.7 MB).
- `data/curriculum/books/full/**` — 1,734 lesson files generated by `build_full_access_curriculum.py`. Many lessons are **template study guides** (self-declared via `content.provenance`), not curated source material.
- `data/curriculum/math/*.json` — legacy generated unit files.
- `__pycache__/or_client.cpython-314.pyc` — compiled module whose source is absent.
- Nested `rahura superteacher L 2.0/dist` — L2.0 build output.

## 25. Documentation

- `readme.md` — desktop app overview, curriculum layout, content status, security notes.
- `DEPLOYMENT.md` — school deployment + security/content release checklists.
- Nested app `README.md`.
- `docs/` — **this analysis** (new).

---

## Cross-cutting observations

1. **Two shipped products + one stray copy in one repo.** The tracked tree is the desktop app + Letters web app; `rahura superteacher L 2.0/` is a third, untracked project sitting inside the working directory (with its own `node_modules`, `dist`, and a functional AI server).
2. **Secrets handling is decent but fragile.** Real API keys and a real account hash exist on disk but are correctly gitignored. The risk is *exfiltration of the working directory* or accidental `git add -f`.
3. **A third of the scripts are untracked**, including the four most security-relevant ones (`fetch_official_library.py`, `verify_official_library.py`, `build_official_book_catalog.py`, `render_learning_edition_smoke.py`) plus `core/official_book_content.py` / `core/official_book_library.py` and the whole `data/official_books/` + `data/reb_student_books/` data. A fresh clone cannot reproduce the "Official Learning Edition" feature or re-run the library pipeline.
4. **No CI, no tests, no monitoring.** Everything is validated by hand-run scripts.
5. **Dev logs and build output** are untracked (good) but present on disk (noise, potential info leak: the err log exposes an absolute user path).