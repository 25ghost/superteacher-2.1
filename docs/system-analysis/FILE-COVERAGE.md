# FILE COVERAGE — What Was Analyzed

Honest accounting of coverage. "Analyzed" means code was read (full or key windows), traced, or validated by tooling; **partial** means sampled or read in part. No file was modified.

---

## Root

| FILE/PATH | CATEGORY | PURPOSE | IMPORTANT DEPENDENCIES | ANALYZED? | NOTES |
|---|---|---|---|---|---|
| `main.py` | Entry (desktop) | RINA Gemini Live loop, tool dispatch, memory hooks | google-genai, ui, core.*, memory | ✅ Full | God-file; tool stubs; infinite reconnect |
| `ui.py` | GUI (desktop) | Entire PyQt6 app: pages, lessons, diagrams, PDF viewer, auth UI | PyQt6, core.* | ⚠️ Partial (read ~2,300/5,176 lines: imports, auth overlay, MainWindow init/auth landing, lesson detail, PDF viewer, quiz, settings, sign-out, Rina page, facade) | Key logic windows covered; ~2,900 lines (mostly widget painting/diagram drawing) skimmed via symbol map |
| `requirements.txt` | Deps | Python packages | — | ✅ | Unpinned; pillow unused at runtime |
| `index.html` / `vite.config.js` / `tailwind.config.js` / `postcss.config.js` | Web build | Letters app shell + tooling | Vite, React | ✅ Full | |
| `package.json` / `package-lock.json` | Deps | Letters app | Firebase, React, lucide | ✅ Full | |
| `firebase.rules` / `storage.rules` | Security | Firestore/Storage rules | — | ✅ Full | **Critical findings (SEC-01/05/06)** |
| `.env.example` | Config | Firebase vars template | — | ✅ | No `.env` present |
| `.gitignore` | Repo hygiene | Ignores secrets, cache, build | — | ✅ | Secrets ignored; nested L2.0 **not** ignored |
| `readme.md` / `DEPLOYMENT.md` | Docs | Product + deployment runbook | — | ✅ Full | Claims vs code verified |
| `Launch SuperTeacher.bat` | Script | Desktop launcher | — | ✅ | |
| `dev-server.log` / `dev-server.err.log` | Artifacts | Vite dev logs | — | ✅ | Should be ignored; leaks user path |
| `firebase.rules` note | — | — | — | — | |
| `assets/` (359 files) | Assets | Images for desktop UI | — | ⚠️ Sampled (listing) | No code references issues found in used paths |

## Desktop app — `core/`

| FILE/PATH | CATEGORY | PURPOSE | DEPENDENCIES | ANALYZED? | NOTES |
|---|---|---|---|---|---|
| `core/curriculum_loader.py` | Core service | Lazy curriculum tree, LRU caches, path safety | curriculum_nodes, official_book_library | ✅ Full | Well-built; traversal not memoized |
| `core/curriculum_nodes.py` | Model | CurriculumNode dataclass | — | ✅ Full | |
| `core/student_mode.py` | Security | Tool allow/block lists, role check | config/student_profile.json | ✅ Full | Defaults to student on error |
| `core/local_auth.py` | Security | File-based auth | config/accounts.json | ✅ Full | **SHA-256 weakness** |
| `core/profile_stats.py` | Service | XP/streak/quiz math | — | ✅ Full | |
| `core/lesson_visuals.py` | Service | Diagram-type inference | — | ✅ Full | Duplicated unreachable branches (DC-22) |
| `core/illustration_loader.py` | Integration | Allowlisted PDF download | requests | ✅ Full | Host allowlist, 200 MB cap, no retry |
| `core/official_book_content.py` | Service | PyMuPDF page extraction | pymupdf | ✅ Full | **Untracked** |
| `core/official_book_library.py` | Service | catalog.json lookup, path safety | — | ✅ Full | **Untracked** |
| `core/prompt.txt` | Config | Base system prompt | — | ✅ | Fallback duplicate in main.py |
| `core/subject_focus.json` | Data | Per-subject teaching prompts | — | ✅ | **No importer found (DC-05)** |

## Desktop app — `memory/`, `config/`

| FILE/PATH | CATEGORY | PURPOSE | DEPENDENCIES | ANALYZED? | NOTES |
|---|---|---|---|---|---|
| `memory/memory_manager.py` | Service | Long-term memory JSON + AI extraction | **or_client (missing)** | ✅ Full | Silent broken feature (SEC-07/DC-01) |
| `memory/config_manager.py` | Config | api_keys.json read/write | — | ✅ Full | Duplicate reader (AP-09) |
| `memory/long_term.json` | Data | Personal facts (plaintext) | — | ✅ (masked) | 1 entry |
| `config/__init__.py` | Config | Old config helpers | — | ✅ | Script-only consumer (DC-02) |
| `config/api_keys.json` | Secrets | **Real** Gemini + OpenRouter keys | — | ✅ (masked, not echoed) | Gitignored; plaintext at rest |
| `config/accounts.json` | Secrets | Real local account (SHA-256) | — | ✅ (masked) | Gitignored |
| `config/student_profile.json` | Data | Profile/progress/role | — | ✅ (masked) | Forgeable session (AUTH-D2) |
| `config/paths.json` | Config | REB book paths | — | ✅ | Legacy script consumer |
| `config/*.example.json` | Templates | — | — | ✅ | |

## Desktop app — `scripts/` (20)

| FILE/PATH | CATEGORY | PURPOSE | ANALYZED? | NOTES |
|---|---|---|---|---|
| `scripts/validate_curriculum.py` | Test | Data validation | core | ✅ Full | No CI runner |
| `scripts/fetch_official_library.py` | Pipeline | REB/RTB crawl+download | requests, urllib3 | ✅ Full | **Untracked**; solid security posture |
| `scripts/build_official_book_catalog.py` | Pipeline | catalog.json builder | pymupdf | ✅ Full | **Untracked** |
| `scripts/verify_official_library.py` | Test | Checksum verification | core | ✅ Partial (head) | **Untracked**; used in DEPLOYMENT |
| `scripts/render_learning_edition_smoke.py` | Test | Offscreen PDF viewer | ui, PyQt6 | ✅ Partial (head) | **Untracked** |
| `scripts/build_full_access_curriculum.py` | Pipeline | 1,734-lesson generator | core.lesson_visuals | ✅ Full | Template content (AP-20) |
| `scripts/reb_build_units.py` | Pipeline | Legacy math unit builder | config | ✅ Full | Legacy-format output |
| `scripts/generate_lesson_content.py` | Pipeline | One-off Gemini generation | google-genai | ✅ Full | Superseded (DC-06) |
| `scripts/clean_unicode.py` / `cleanup_params.py` / `verify_output.py` | Tools | Data hygiene | — | ✅ (heads) | One-shot |
| `scripts/extract_params.py` / `discover_figures.py` / `extract_figure_pages.py` / `integrate_diagrams.py` / `add_lesson_illustrations.py` / `revert_diagrams.py` | Tools | Figure/diagram pipeline | pymupdf | ✅ (heads) | One-shot migration tools |
| `scripts/generate_assets.py` / `render_visual_smoke.py` | Tools/Test | Asset gen / smoke | PyQt6 | ✅ (heads) | render_visual_smoke reusable |
| `scripts/download_reb_student_books.ps1` | Tool | PowerShell downloader | — | ❌ Not read | Untracked; flagged |

## Data (2,267 tracked + untracked)

| FILE/PATH | CATEGORY | PURPOSE | ANALYZED? | NOTES |
|---|---|---|---|---|
| `data/curriculum/index.json` | Data | Tree root | — | ✅ Full |
| `data/curriculum/manifests/*.json` (13) | Data | Navigation manifests | — | ✅ Sampled + validated via script |
| `data/curriculum/books/full/**` (2,232) | Data | Books/units/lessons | — | ⚠️ Sampled (structure, provenance, encoding) + full validation via `validate_curriculum.py` logic review; 155 modified in worktree |
| `data/curriculum/high_school.json` | Data (legacy) | Old curriculum | — | ✅ Structure read; used by `_find_math_unit_index` |
| `data/curriculum/math/` | Data (legacy) | Old unit JSON | — | ✅ (empty listing) | No readers (DC-03) |
| `data/reb_resources.json` | Data | REB study order | — | ✅ | |
| `data/reb_student_books/` (106 PDFs) | Data | Official books | — | ⚠️ Counted + cataloged (not read) | **Untracked** |
| `data/reb_books/` (18) | Data | Legacy math books | — | ⚠️ Listed | Duplicates `src/notes` |
| `data/official_books/catalog.json` | Data | 102-book catalog | — | ✅ Full | **Untracked** |
| `data/official_books/acquisition_report.json` | Data | Fetch report | — | ⚠️ Listed | **Untracked** |
| `data/official_books/files/` | Data | Download staging | — | ✅ | Empty |

## Web app — `src/`

| FILE/PATH | CATEGORY | PURPOSE | ANALYZED? | NOTES |
|---|---|---|---|---|
| `src/main.jsx` / `src/App.jsx` | Entry/Routes | Route switching | React | ✅ Full | No router lib |
| `src/lib/firebase.js` | Integration | Firebase init (optional) | firebase | ✅ Full | |
| `src/services/letters.js` | Data layer | Firestore/Storage + seed fallback | firebase | ✅ Full | No pagination |
| `src/components/PublicMapExperience.jsx` | UI | Map page | components, services | ✅ Full | |
| `src/components/MapCanvas.jsx` | UI | Canvas map + tiles + pins | utils/mapProjection | ✅ Full | Full redraw per frame |
| `src/components/AdminWorkspace.jsx` | UI | Admin desk + auth gate | firebase/auth, services | ✅ Full | Any authed user = admin |
| `src/components/LetterOverlay.jsx` / `Journal.jsx` / `AmbientPlayer.jsx` | UI | Letter/echo/journal/audio | services | ✅ Full | Echo errors swallowed |
| `src/components/NotesIndex.jsx` / `NotesReader.jsx` | UI | Notes browser | utils/noteParser | ✅ Full | **Untracked** |
| `src/utils/noteParser.js` | Util | Raw txt → units/sections | — | ✅ Full | Regex-fragile; **untracked** |
| `src/utils/mapProjection.js` | Util | Web-Mercator math | — | ✅ Full | |
| `src/data/seedLetters.js` | Seed | Demo letters/echoes | — | ✅ Full | |
| `src/notes/*.txt` + PDFs | Data | REB math text | — | ⚠️ Sampled | 111k lines bundled; TG/syllabus unused (DC-04) |
| `src/styles.css` | Style | Tailwind + custom | — | ⚠️ Skimmed | |
| `public/assets/references/*` | Assets | Map overlays | — | ✅ Listed | |

## Nested app — `rahura superteacher L 2.0/` (untracked)

| FILE/PATH | CATEGORY | PURPOSE | ANALYZED? | NOTES |
|---|---|---|---|---|
| `package.json` / `remotion.config.ts` | Deps/Build | Remotion + React + OpenAI | — | ✅ Full | |
| `src/App.tsx` / `src/types.ts` | App | Curriculum browser | lib/content | ✅ Full | |
| `server/index.mjs` | Backend | Express AI gateway | openai, express | ✅ Full | Rate limit spoofable; no Origin check |
| `server/rina-prompt.mjs` | Config | Tutor prompt | — | ✅ Full | Good safety wording |
| `src/components/*` (7), `src/lib/*` (3), `src/remotion/*` (3) | UI/Util | App pieces | — | ⚠️ Partial (RinaTutor + content.ts traced; others skimmed via listing/grep) | Not tracked; decision needed |
| `node_modules/`, `dist/`, `data/` | Deps/Out | — | — | ❌ Not analyzed | Untracked; would blow up `git add -A` |

## Not present (verified absent)

CI/CD (`.github`, YAML) · Docker · pytest/unittest/Vitest suites · migrations · webhooks · cron · Terraform/K8s · `.env` · `or_client.py` source · `agent/`/`actions/` source modules.

---

## Coverage gaps (explicit)

1. **`ui.py` widget-painting interior** (~2,900 lines: `MathDiagramWidget._draw_*`, `LearningBackground`, `AvatarWidget`, etc.) — read via symbol map and targeted windows; not line-by-line. Low security relevance (pure painting), but quiz/profile/lesson flows *were* traced.
2. **Lesson JSON content** — structurally validated and sampled; not read individually (1,734 files). Encoding artifacts confirmed in samples.
3. **REB/RTB PDF contents** — never opened; only catalog metadata/checksums.
4. **`src/styles.css`** and L2.0 styles — styling only.
5. **`node_modules`** trees — dependency lists analyzed, contents not.
6. **Git history** — only recent 20 commits + `--all` greps for secrets reviewed; full history not audited.

Where anything could not be fully analyzed, it is stated above rather than claimed as complete.