# Phase 8 — Bad Architecture / Technical Debt

Each issue: CURRENT DESIGN → WHY IT IS BAD → RISK → RECOMMENDED DESIGN → MIGRATION DIFFICULTY.

---

## AP-01 · God file: `ui.py` (5,176 lines) contains the entire GUI

- **Current:** One file holds theme, ~40 widgets, the whole MainWindow (12 pages), lesson rendering, diagram rendering, quiz logic, auth landing, official-PDF viewer, settings, sign-out.
- **Why bad:** Untestable; every change risks unrelated regressions; imports fail open (whole-module `try/except` degrade) because the file is too big to reason about; a single syntax/runtime error kills the app.
- **Risk:** High. The `try/except` import fallbacks (DC-03/SEC-03) exist precisely because the module is fragile.
- **Recommended:** Split by responsibility: `ui/theme.py`, `ui/widgets/*.py`, `ui/pages/*.py`, `ui/lesson_view.py`, `ui/pdf_viewer.py`, `ui/chat.py`. Keep `JarvisUI` facade.
- **Migration difficulty:** Medium-High (mostly mechanical; no behavior change; tests can be added after).

## AP-02 · No automated tests anywhere

- **Current:** Only assertion-based data scripts and offscreen smoke scripts; no pytest/unittest/Vitest.
- **Why bad:** Content migrations (2,247 JSON files, 1,734 lessons) and UI rewrites happen without regression nets; the silent `or_client` failure went unnoticed for commits.
- **Risk:** High (correctness + security regressions undetected).
- **Recommended:** pytest for `core/*` (curriculum loader, student_mode, local_auth, profile_stats, official_book_content) and Vitest for `letters.js`/`noteParser`; CI to run them.
- **Migration difficulty:** Low for core; Medium for UI (requires offscreen Qt).

## AP-03 · Duplicate curriculum formats & dual content pipelines

- **Current:** (a) legacy `high_school.json` + `math/` (script-era) and (b) `index.json → manifests → books` (lazy). `ui.py` still reads both; `reb_build_units.py` writes only the legacy format; `build_full_access_curriculum.py` migrates legacy→new.
- **Why bad:** Two schemas to maintain; `_find_math_unit_index`/`_math_level_prefix` legacy lookups linger; stale files confuse contributors.
- **Risk:** Medium. Content drift between formats; legacy lookups return wrong units.
- **Recommended:** Finish the migration: drop legacy readers from `ui.py`, archive `high_school.json`/`math/`, keep enrichment pipeline pointed at the archive only.
- **Migration difficulty:** Low-Medium.

## AP-04 · `main.py` god-file + monolithic tool dispatch

- **Current:** 970 lines: 18 tool schemas (some ~40-line parameter blocks), async session management, memory hooks, reconnect loop, shutdown logic.
- **Why bad:** The tool schemas + dispatch + stubs are three parallel structures that can drift (e.g., `filter_tool_declarations` ALLOWED_TOOLS vs dispatcher `if name ==` chain vs `ACTION_TOOLS_AVAILABLE`).
- **Risk:** Medium. If a tool is re-enabled, one of the three layers may not match.
- **Recommended:** A declarative tool registry: one table of `{name, schema, handler, student_allowed, teacher_only}`; generate declarations and dispatch from it.
- **Migration difficulty:** Low-Medium.

## AP-05 · Auth/session as mutable JSON flag

- **Current:** `authenticated: true` boolean in `student_profile.json`; role in the same file; fail-open import fallback.
- **Why bad:** Forgeable, no expiry, no revocation, roles meaningless.
- **Risk:** High (see AUTH-D2, SEC-03).
- **Recommended:** Local token session (random token file + hash record) or password re-verification at startup; HMAC-signed role.
- **Migration difficulty:** Low.

## AP-06 · Business logic in the UI layer (desktop)

- **Current:** `MainWindow._submit_quiz` computes scores; `_lesson_detail` renders and resolves media; `_open_lesson` derives subject; quiz XP/streak writes happen in UI callbacks; `_auto_lesson_content` is ~200 lines of content generation embedded in the UI.
- **Why bad:** UI can't be reused headless; content logic and rendering entangled; the quiz "Performance Analysis" text is hardcoded generic fluff.
- **Recommended:** Extract `quiz_service`, `progress_service`, `lesson_service` (content selection, normalization, diagram inference already partially in `core/`).
- **Migration difficulty:** Medium.

## AP-07 · Error handling: fail-open imports + silent degradation

- **Current:** `ui.py` wraps every core import in try/except with no-op fallbacks (some fail-open like `authenticate`; most fail to "feature missing"). `curriculum_loader` returns `[]`/`None` on errors. Memory failures print to console.
- **Why bad:** Real breakage is invisible to users and developers; SEC-03 is a direct consequence.
- **Recommended:** Fail loudly in dev (log + status bar), fail closed for security paths; explicit feature-flag for optional modules.
- **Migration difficulty:** Low.

## AP-08 · Config scattered in 4 formats

- **Current:** `config/api_keys.json` (runtime), `.env`/`.env.example` (web), `.env.local` (nested app), `config/paths.json` (scripts), plus three api_keys readers (AP-09).
- **Why bad:** Key rotation and deployment differ per format; onboarding friction; secrets risk.
- **Recommended:** One env-var/`.env` convention for the desktop app too, with a file-based fallback for the offline school build.
- **Migration difficulty:** Low.

## AP-09 · Duplicate utility implementations

- **Current:** 3 readers for `api_keys.json` (`main._get_api_key`, `memory/config_manager`, `config/__init__`); 2–3 base-dir/path helpers duplicated across `main.py`, `ui.py`, `memory/*`, `core/*`, `scripts/*` (`get_base_dir`/`_base_dir` ×5); `clean_text` logic duplicated in `reb_build_units.py` and noteParser; `sha256_file` in 2 scripts.
- **Why bad:** Drift (e.g., frozen-path handling differs), maintenance burden.
- **Recommended:** `app/paths.py` + `app/config.py` single helpers.
- **Migration difficulty:** Low.

## AP-10 · Hardcoded / magic strings scattered

- **Current:** Lesson model names ("models/gemini-2.5-flash-native-audio-preview-12-2025"), subject names ("Mathematics"), tool names, page keys, `data/curriculum/{level}.json` paths, secret keywords ("Commanders") embedded across `main.py`, `ui.py`, `scripts/`.
- **Why bad:** Renames ripple; model pinning is fragile (Gemini renames models often — the pinned preview model is already dated).
- **Recommended:** Central `constants.py`; config-driven model names.
- **Migration difficulty:** Low.

## AP-11 · Decorative placeholder UI (Missions/Classroom/Community/Resources)

- **Current:** Static cards with fabricated numbers ("8 badges", "72% complete", "Master Chemistry Unit 1"), hardcoded mission lists, fake community content.
- **Why bad:** Misleading for students; dead weight that implies features that don't exist.
- **Recommended:** Wire to real profile data or remove; mark as "coming soon".
- **Migration difficulty:** Low.

## AP-12 · No observability (metrics/tracing/structured logs)

- **Current:** Console logging only; no log files for the desktop app; no error reporting.
- **Why bad:** School deployments are remote; failures (like `or_client`) are invisible.
- **Recommended:** Rotating file log + opt-in telemetry toggle (privacy-friendly), structured JSON logs for scripts.
- **Migration difficulty:** Low.

## AP-13 · Frontend state duplication: Firestore + localStorage + seed mode

- **Current:** Letters app runs in three modes (Firebase, seed, hybrid) with `sortByCreated` client-sort duplication and two "create" implementations (seed-local vs Firestore).
- **Why bad:** Behavior differs by config; bugs only appear when Firebase is enabled; `createdAt` sorting duplicated.
- **Recommended:** Abstract a `LetterStore` interface with two implementations (Local/Seed + Firestore); single sort.
- **Migration difficulty:** Low.

## AP-14 · `noteParser` regex-driven textbook parsing

- **Current:** `stripToc`/`splitIntoUnits`/`parseSections` heuristics on 111k lines of raw text; falls back to raw text.
- **Why bad:** Fragile to typography changes; the PDF→text extraction already shows artifacts (e.g., the `\u2610`/`�` mojibake seen in curriculum JSON; "STUDY GUIDE � BIOLOGY").
- **Recommended:** Generate structured notes JSON once (build step) instead of parsing at runtime.
- **Migration difficulty:** Medium.

## AP-15 · Encoding hygiene

- **Current:** Mixed line endings (LF/CRLF), cp1252 console prints crash (`UnicodeEncodeError` seen during analysis), `ensure_ascii=False` writes + `\u2610` mojibake in lesson content ("STUDY GUIDE � BIOLOGY"), duplicated `◻`-style glyphs.
- **Why bad:** Cross-machine crashes, corrupted display, broken validation on some platforms.
- **Recommended:** Normalize to UTF-8 + LF; run a lint pass (scripts/clean_unicode exists).
- **Migration difficulty:** Low.

## AP-16 · Untracked-but-essential files (repo hygiene)

- **Current:** `core/official_book_content.py`, `core/official_book_library.py`, `scripts/{fetch_official_library,verify_official_library,build_official_book_catalog,render_learning_edition_smoke}.py`, `data/official_books/`, `data/reb_student_books/` (106 PDFs), `src/components/NotesIndex.jsx`, `NotesReader.jsx`, `src/utils/noteParser.js`, `src/notes/*`, plus 155 modified + 16 untracked files.
- **Why bad:** A fresh clone cannot run the Learning Edition, verify the library, or even build the Letters notes feature; `ui.py` imports untracked modules → those features silently vanish (fail-open imports mask it).
- **Recommended:** Decide policy (commit or provide fetch script); at minimum track the Python modules and scripts; keep the big PDFs out but document how to obtain them.
- **Migration difficulty:** Low (process), the PDFs raise licensing questions.

## AP-17 · Race conditions / shared state

- **Current:** `curriculum_loader` uses a global `OrderedDict` cache guarded by `RLock` (good); `memory/long_term.json` guarded by `Lock` (good); but `student_profile.json` is read/written from UI thread and `_update_memory_async`-adjacent flows without a lock; `JarvisLive._pending_queue` is touched from UI thread and asyncio thread (list append/clear without lock — benign for CPython but fragile); the reconnect loop recreates sessions while `self.session` is swapped.
- **Why bad:** Intermittent lost profile writes; session teardown during reconnect may drop the `close()` racing `connect()`.
- **Recommended:** Serialize profile writes; guard session lifecycle with a single async lock.
- **Migration difficulty:** Low-Medium.

## AP-18 · Infinite retry with fixed 3 s delay

- **Current:** `while True: try connect … except: sleep(3)` — no backoff, no max retries, no distinction between auth vs network errors.
- **Why bad:** Burns quota on bad key; pins CPU; masks the actual error from the UI.
- **Recommended:** Exponential backoff (3→60 s), auth-error fast-fail to the SetupOverlay.
- **Migration difficulty:** Low.

## AP-19 · Duplicated curriculum concept across products (L2.0 vs desktop)

- **Current:** L2.0 has its own `content.ts` loader for the same `books/full/**` layout with a different index schema (`levels[]` vs `nodes[]`).
- **Why bad:** Two clients parsing the same data differently; schema changes break one silently.
- **Recommended:** Publish a shared schema + generator; or adopt the desktop manifest format for L2.0.
- **Migration difficulty:** Medium.

## AP-20 · Content quality: template study guides as "content"

- **Current:** `build_full_access_curriculum.py` generates most lessons from templates ("STUDY GUIDE — {SUBJECT}", generic objectives/practice); `provenance` flags them.
- **Why bad:** A teaching product whose lessons are placeholders risks delivering wrong/empty pedagogy; quiz answers are auto-generated "B".
- **Recommended:** Ship real curated lessons for released subjects; gate `status: ready` on review (DEPLOYMENT.md already says this); show provenance to the learner.
- **Migration difficulty:** High (content work, not code).

---

## Top-10 debt summary

1. AP-01 ui.py god file
2. AP-02 no tests
3. AP-16 untracked essential code/data
4. AP-05 forgeable auth
5. AP-03 dual curriculum formats
6. AP-04 monolithic tool dispatch
7. AP-07 fail-open degradation
8. AP-12 no observability
9. AP-11 placeholder UI
10. AP-20 template content as shipped content