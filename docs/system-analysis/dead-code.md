# Phase 7 — Dead Code / Unused Code

Classification: **CONFIRMED UNUSED** · **LIKELY UNUSED** · **POSSIBLY ACTIVE** · **UNKNOWN**. Nothing was deleted.

---

## 1. Modules / files

### DC-01 · `memory/memory_manager.py` OpenRouter path (`or_client`)
- **Finding:** `should_extract_memory()` and `extract_memory()` do `from or_client import client`. The **source file does not exist** — only `__pycache__/or_client.cpython-314.pyc` remains (compiled for Python 3.14).
- **Class:** CONFIRMED UNUSED (runtime-broken). The functions always raise `ModuleNotFoundError` → caught → return `False`/`{}`.
- **Determined by:** `find . -name "or_client*"` → only `.pyc`; grep shows the import only in these two functions.
- **Impact:** "AI memory extraction" is dead; `save_memory` tool (direct JSON write) still works, so users can't tell.

### DC-02 · `config/__init__.py` (`get_config`, `get_os`, `get_reb_book`, …)
- **Finding:** Only `scripts/reb_build_units.py` imports `get_reb_book`/`_BASE` from `config`. The runtime app uses `memory/config_manager.py` and direct JSON reads instead.
- **Class:** LIKELY UNUSED (only one offline script consumer).

### DC-03 · `data/curriculum/high_school.json` + `data/curriculum/math/`
- **Finding:** Legacy curriculum format (`sub_levels → subjects → units → lessons_content`). The new tree is `index.json → manifests → books`. `ui.py` `_find_math_unit_index` still opens `data/curriculum/{level}.json` (i.e., `high_school.json`) to find math unit indexes; `scripts/reb_build_units.py` writes `data/curriculum/math/` which nothing reads.
- **Class:** POSSIBLY ACTIVE (one narrow UI lookup) / the `math/` outputs are CONFIRMED UNUSED.
- **Note:** The legacy files were the source for `build_full_access_curriculum.py --legacy-source`.

### DC-04 · `src/notes/Mathematics-S1-TG.txt`, `Mathematics-S2-TG.txt`, `Mathematics-S3-TG.txt`, `Mathematics-S1-SB.pdf`, `Mathematics-S2- TG.pdf`, `Maths senior 1 TG.pdf`, `Maths Senior 3 TG.pdf`, `Mathematics_Syllabus_Ordinary_Level.pdf`, `Mathematics-S1-SB.pdf`
- **Finding:** `noteParser.js` imports only `Mathematics-S{1,2,3}-SB.txt` (`?raw`). The other `.txt` (teacher guides, syllabus) and all `.pdf` copies under `src/notes/` are never imported by app code.
- **Class:** LIKELY UNUSED (source artifacts kept for reference). Note `data/reb_books/` also contains `Mathematics-S1-SB.txt` duplicates — the same content exists in two places.

### DC-05 · `core/subject_focus.json`
- **Finding:** Rich per-subject teaching prompts. Searched: no importer found in `ui.py`, `main.py`, or scripts (only referenced in this analysis).
- **Class:** CONFIRMED UNUSED (dead data — would be valuable if wired into `get_lesson_context`/system prompt).

### DC-06 · `scripts/generate_lesson_content.py`
- **Finding:** One-off Gemini generator for legacy `high_school.json` (S1 math only), progress file `.gen_progress.json`. The generation pipeline was superseded by `build_full_access_curriculum.py`.
- **Class:** LIKELY UNUSED (historical; rerunnable only for that legacy file).

### DC-07 · `scripts/clean_unicode.py`, `scripts/cleanup_params.py`, `scripts/verify_output.py`, `scripts/extract_params.py`, `scripts/discover_figures.py`, `scripts/extract_figure_pages.py`, `scripts/integrate_diagrams.py`, `scripts/add_lesson_illustrations.py`, `scripts/revert_diagrams.py`, `scripts/generate_assets.py`, `scripts/render_visual_smoke.py`
- **Finding:** One-shot data-wrangling/smoke scripts for past content migrations. Not invoked by any pipeline or CI.
- **Class:** LIKELY UNUSED (maintenance tools; `render_visual_smoke.py` is the only reusable smoke test).
- **Note:** `scripts/clean_unicode.py` and `scripts/cleanup_params.py` fixed issues now baked into the data — rerunning may corrupt current files. Handle with care.

### DC-08 · `agent/` and `actions/` directories
- **Finding:** Empty except `__pycache__` (stale bytecode from a prior build that contained the OS-control modules).
- **Class:** CONFIRMED UNUSED (intentionally removed; `main.py` stubs reference these names).
- **Determined by:** directory listing + `main.py` `_disabled_action` stubs.

### DC-09 · `core/illustration_loader.py` `ALLOWED_SOURCE_HOSTS` includes `elearning.rtb.gov.rw` (unused; the used set in scripts includes `www.elearning.rtb.gov.rw`)
- **Finding:** Runtime loader host set = `{elearning.reb.rw, elearning.rtb.gov.rw, www.elearning.rtb.gov.rw}` vs `validate_curriculum.py`/`fetch_official_library.py` slightly different sets. Minor drift, not dead.
- **Class:** POSSIBLY ACTIVE (drift, see architecture problems).

### DC-10 · `tmp/pdfs/*` (2 render test PNGs) and `dev-server*.log`
- **Finding:** Artifacts in the working tree (untracked). Logs should be ignored; PNGs are smoke-test byproducts.
- **Class:** LIKELY UNUSED (junk).

### DC-11 · `dist/` (root) and `rahura superteacher L 2.0/dist`
- **Finding:** Vite build output, gitignored, present on disk.
- **Class:** LIKELY UNUSED (regenerable).

### DC-12 · `rahura superteacher L 2.0/` (whole tree)
- **Finding:** Full duplicate project (own package.json, node_modules, server, Remotion) — **not tracked, not ignored**.
- **Class:** CONFIRMED UNUSED by the shipped products, but UNKNOWN intent (may be the future direction). Risk: accidental `git add -A` commits 30k+ files including `node_modules`.

---

## 2. Functions / code paths

### DC-13 · `main.py` `TOOL_DECLARATIONS` (18 tool schemas) vs dispatched names
- **Finding:** Schemas exist for `open_app, web_search, weather_report, send_message, reminder, youtube_video, screen_process, computer_settings, browser_control, file_controller, desktop_control, code_helper, dev_agent, agent_task, computer_control, game_updater, flight_finder, file_processor, shutdown_rina, save_memory`. With `ACTION_TOOLS_AVAILABLE = False`, only `save_memory`/`shutdown_rina` are declared to the model; `_execute_tool`'s dispatch `if name == …` chain still references all of them (all stubs).
- **Class:** CONFIRMED UNUSED *in the shipped build* (the schemas + dispatch are the documented extension point for the "teacher deployment").
- **Determined by:** `filter_tool_declarations(TOOL_DECLARATIONS if ACTION_TOOLS_AVAILABLE else [two-tool subset])`.

### DC-14 · `ui.py` `_auto_lesson_content()` and its big topic-templating branch
- **Finding:** Only reached when `get_lesson_content` returns nothing for a legacy path (`_open_lesson` → `_get_lesson_content` → None → `_auto_lesson_content`?). Verified callers: `_lesson_detail` uses `_get_lesson_content`; the `_auto_lesson_content` path is triggered for paths like `["Quick Access", ...]` or when content_ref is missing.
- **Class:** POSSIBLY ACTIVE (fallback for quick-access/demo paths — effectively dead for the full library which always has content_ref).
- **Note:** `_find_math_unit_index` + `_math_level_prefix` are also legacy-path helpers.

### DC-15 · `ui.py` decorative pages: Classroom, Community, Missions, Resources, Home quick actions
- **Finding:** These build static card grids with hardcoded strings ("Master Chemistry Unit 1", "8 badges", etc.). No data sources, no callbacks that do anything real.
- **Class:** LIKELY UNUSED logic (UI shell active, but content is placeholder — display-only dead weight).

### DC-16 · `ui.py` `_RootShim`
- **Finding:** Wraps `QApplication.exec()`; `main.py` uses `ui.root.mainloop()`. Why the shim exists (Tkinter compatibility?) is unclear; it's active but trivial.
- **Class:** POSSIBLY ACTIVE.

### DC-17 · `ui.py` SoundEngine `play()` variants
- **Finding:** `self.sound.enabled = False` at startup; sounds only play via `sound.play(...)` calls that no-op when disabled. `_toggle_sound` can enable.
- **Class:** POSSIBLY ACTIVE (feature-flagged).

### DC-18 · `scripts/.gen_progress.json`
- **Finding:** Progress file for the legacy generator (DC-06).
- **Class:** CONFIRMED UNUSED data artifact (untracked? verified present on disk).

### DC-19 · `core/prompt.txt` fallback in `_load_system_prompt`
- **Finding:** Fallback string is used only if `prompt.txt` read fails. Both exist; fallback likely unused in practice.
- **Class:** LIKELY UNUSED (safety net).

### DC-20 · `AmbientPlayer` "generated loop" branch
- **Finding:** Runs when `audioUrl` is empty; seed letters have `audioUrl: ""` → the WebAudio loop is the active path today. Uploaded letters get `<audio>`.
- **Class:** POSSIBLY ACTIVE (both branches live).

### DC-21 · `Journal`/`threads` feature
- **Finding:** Threads are stored per-browser (localStorage), never synced to Firestore; `letterId`-based threads reference demo IDs only.
- **Class:** POSSIBLY ACTIVE (client-only feature).

### DC-22 · `core/lesson_visuals.infer_lesson_diagrams` — duplicated histogram/pie/scatter branches
- **Finding:** The first three checks (`histogram`, `pie chart`, `scatter…`) appear **twice** (once before, once after the geometry block). The second copies are unreachable duplicates (first branch returns).
- **Class:** CONFIRMED UNUSED (unreachable duplicate code).

### DC-23 · `memory/config_manager.py` vs `config/__init__.py` vs `main._get_api_key`
- **Finding:** Three different readers for `api_keys.json` (main.py inline, memory/config_manager, config/__init__). `config/__init__` reader is script-only (DC-02).
- **Class:** duplication finding (see Phase 8), not dead per se.

---

## 3. Environment variables / config

| Key | Used by | Status |
|---|---|---|
| `VITE_FIREBASE_*` (6) | `src/lib/firebase.js` | ACTIVE (optional) |
| `gemini_api_key`, `openrouter_api_key`, `os_system` | main.py, SetupOverlay, config_manager, generate_lesson_content | ACTIVE |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `PORT` | L2.0 server | ACTIVE (nested) |
| `QT_QPA_PLATFORM` | smoke scripts | ACTIVE (test) |
| `VITE_*` in `.env.example` | — | Template only |

## 4. Database tables / collections / files with no readers

| Store | Readers | Status |
|---|---|---|
| Firestore `threads` | none (localStorage only) | Concept not in rules/schema — LIKELY UNUSED server-side |
| `data/curriculum/math/*.json` | none | CONFIRMED UNUSED |
| `data/official_books/acquisition_report.json` | humans/scripts only | POSSIBLY ACTIVE (audit artifact) |
| `config/paths.json` | `config/__init__.get_reb_book` → reb_build_units | POSSIBLY ACTIVE (legacy script only) |
| `data/reb_books/*.txt` (duplicates of `src/notes/*`) | `scripts/reb_build_units` reads them | POSSIBLY ACTIVE (script-only) |

---

## 5. Summary table (highest-value candidates)

| ID | Item | Class | Why |
|---|---|---|---|
| DC-01 | `or_client` memory extraction | CONFIRMED UNUSED | Missing source; always fails silently |
| DC-04 | `src/notes` TG/syllabus/PDF files | LIKELY UNUSED | Not imported by app |
| DC-05 | `subject_focus.json` | CONFIRMED UNUSED | No importer found |
| DC-22 | duplicated diagram branches | CONFIRMED UNUSED | Unreachable code |
| DC-13 | 16 tool stubs + schemas | CONFIRMED UNUSED (shipped build) | Deliberate; keep as documented extension point |
| DC-12 | `rahura superteacher L 2.0/` | CONFIRMED UNUSED by tracked product | Untracked duplicate project |
| DC-03 | legacy curriculum files | POSSIBLY ACTIVE | One narrow UI lookup |
| DC-08 | `agent/`, `actions/` | CONFIRMED UNUSED | Empty dirs |

**Caution:** several "unused" items are deliberate safety architecture (DC-13, DC-08) or historically meaningful data (DC-03 legacy content used as enrichment source). Deleting without a migration plan would lose enrichment data for `build_full_access_curriculum.py`.