# Phase 2 — Architecture Discovery

How the system is *actually* architected, traced through source code rather than folder names.

---

## 1. Two independent products share one repository

The repository is a monorepo *by accident*: it contains

1. **SuperTeacher desktop (Python/PyQt6)** — the flagship learning app ("RINA" tutor + curriculum browser). Entry point `main.py`.
2. **Letters web app (React/Vite + optional Firebase)** — a public map of fictional letters, an admin desk, and a REB math-notes reader. Entry point `index.html` → `src/main.jsx`.
3. **Rahura SuperTeacher L 2.0 (untracked nested copy)** — a React/TS curriculum app with an Express + OpenAI tutor server and Remotion videos. Not part of git; physically nested in the working tree.

There is **no shared code** between the three — no imports, no shared types, no shared config. They share only the root directory and git history.

---

## 2. Desktop app — component map

```
main.py  (entry, 970 lines)
 ├─ config/api_keys.json        → Gemini + OpenRouter keys
 ├─ core/prompt.txt             → base system prompt
 ├─ core/curriculum_loader.py   → lazy curriculum tree + LRU caches
 │    ├─ core/curriculum_nodes.py        (dataclass CurriculumNode)
 │    ├─ core/official_book_library.py   (catalog lookup; UNTRACKED)
 │    └─ data/curriculum/index.json → manifests/*.json → books/**/*.json
 ├─ core/student_mode.py        → tool allow/block lists, role check
 ├─ memory/memory_manager.py    → long_term.json + OpenRouter via `or_client` (MISSING)
 ├─ memory/config_manager.py    → api_keys.json read/write
 └─ ui.py (JarvisUI, 5176 lines) → whole PyQt6 GUI
      ├─ core/local_auth.py            → accounts.json login
      ├─ core/profile_stats.py         → xp/streak/quiz stats
      ├─ core/lesson_visuals.py        → diagram-type inference per lesson
      ├─ core/illustration_loader.py   → allowlisted PDF download → .cache/textbooks/
      ├─ core/official_book_content.py → PyMuPDF page extraction (UNTRACKED)
      └─ assets/, data/curriculum/media → images
```

### Entry points / runtime processes

- `python main.py` spawns **two threads** from `main()`:
  - **UI thread:** `JarvisUI` → `MainWindow` → `ui.root.mainloop()`.
  - **Daemon thread `runner`:** `wait_for_api_key()` (busy-waits on config) → `wait_for_rina_activation()` (waits on a `threading.Event` set when the user enters the Rina page) → `asyncio.run(JarvisLive.run())`.
- `JarvisLive.run()` opens a **Gemini Live session** (`client.aio.live.connect`) and runs 4 asyncio tasks in a `TaskGroup`: `_send_realtime` (mic → queue → session), `_listen_audio` (sounddevice InputStream), `_receive_audio` (session → play queue + transcript + tool calls), `_play_audio` (RawOutputStream).
- On session failure the outer `while True` loop **reconnects every 3 s** indefinitely — an infinite retry loop with no backoff cap.
- Tool calls arrive in `_receive_audio` → `_execute_tool`. With `ACTION_TOOLS_AVAILABLE = False` (the safe build) **only `save_memory` and `shutdown_rina` are declared to the model**; every other tool name resolves to the `_disabled_action` stub returning a canned message. This is defense in depth on top of `student_mode.py` filtering.

### Component responsibilities

| Component | Responsibility | Coupling |
|---|---|---|
| `main.py` `JarvisLive` | Live session orchestration, tool dispatch, memory hooks | → ui, curriculum_loader, memory, student_mode |
| `ui.py` `MainWindow` | All pages: Home, Learn, Quizzes, Missions, Progress, Classroom, Community, Resources, Rina, Profile, Settings; auth landing; lesson rendering incl. diagrams + `OfficialTextbookViewer` | → core.* , memory via main, curriculum loader |
| `curriculum_loader` | Lazy navigation: caches manifests (16) and lesson content (3 entries / 4 MB), path traversal, source links | → curriculum_nodes, official_book_library |
| `student_mode` | Role → tool policy | → config/student_profile.json |
| `local_auth` | Register/authenticate against `accounts.json` | standalone |
| `memory_manager` | Read/write `long_term.json`; OpenRouter-backed extraction | → `or_client` (broken import) |
| `illustration_loader` | Approved-host PDF streaming to `.cache/textbooks/` | requests |
| `official_book_content` | PyMuPDF page → text+visual regions (Learning Edition) | pymupdf |
| `official_book_library` | `catalog.json` lookup / path safety | standalone |
| `lesson_visuals` | Keyword → diagram spec inference | standalone |
| `profile_stats` | XP/streak/quiz-score math | standalone |

### Internal APIs (module boundaries)

- `curriculum_loader`: `get_levels()`, `get_children(node)`, `get_node_by_path(path)`, `get_lesson_content(path|node)`, `get_unit_metadata(path)`, `get_source_links(path)`, `get_lesson_context(path)` — **documented, stable, and used by both the desktop UI and (in spirit) the L2.0 app's content loader**.
- `student_mode`: `is_student_mode()`, `tool_allowed(name)`, `filter_tool_declarations(list)`.
- `local_auth`: `register(u,p,role)`, `authenticate(u,p) -> (ok,msg,role)`, `has_accounts()`.
- `memory`: `load_memory()`, `update_memory(dict)`, `should_extract_memory(...)`, `extract_memory(...)`, `format_memory_for_prompt(...)`.
- `JarvisUI` exposes a small facade (`muted`, `on_text_command`, `set_state`, `write_log`, `wait_for_api_key`, …) that `main.py` uses so it never touches Qt widgets directly.

### Entry-point / import hazards

- `ui.py` imports core modules inside `try/except` and **silently degrades** (e.g. `authenticate` fallback returns `(bool(u.strip()), "Signed in.", "student")` — any non-empty username "succeeds" if `local_auth` fails to import).
- `memory_manager.py` imports `or_client` inside functions; the source module is **missing** (only a `__pycache__/*.pyc` remains). At runtime `should_extract_memory`/`extract_memory` raise `ModuleNotFoundError`, are caught, and memory extraction **silently never runs**. The `save_memory` tool still works (writes JSON directly).
- `config/__init__.py` (`get_config`, `get_reb_book`) is only used by `scripts/reb_build_units.py`; it is effectively dead outside scripts.

---

## 3. Letters web app — component map

```
index.html → src/main.jsx → App.jsx (route switch by location.pathname)
 ├─ PublicMapExperience   (map + journal + overlays)
 │    ├─ MapCanvas        (canvas rendering, OSM tiles, pins, threads, inertia pan/zoom)
 │    ├─ Journal          (discovered letters + thread list; localStorage)
 │    ├─ LetterOverlay    (letter view + echoes feed + echo form)
 │    └─ AmbientPlayer    (WebAudio generated loop or <audio> tag)
 ├─ AdminWorkspace        (Firebase Auth gate → map + publish form + asset upload)
 ├─ NotesIndex / NotesReader (REB math notes; noteParser splits raw txt into units/sections)
 └─ services/letters.js   (Firestore subscribe/create + Storage upload; seed fallback)
```

- **State:** React hooks + `localStorage` (`letters.discovered`, `letters.threads`, `notes-read-*`). No global store, no server state library.
- **Firebase is optional.** `src/lib/firebase.js` returns `null` app/auth/db/storage unless all six `VITE_FIREBASE_*` env vars are set; `letters.js` then falls back to `seedLetters`/`seedEchoes` and local echoes. This makes the app runnable with zero backend.
- **No router library** — routes are parsed from `window.location.pathname` in `App.jsx`.

### Data boundaries

- `letters` collection: title, locationName, lat, lng, dateString, textContent, portraitUrl, audioUrl, secretClueTags, createdAt.
- `echoes` collection: letterId, authorName, textContent, type (reply | independent_confession), lat, lng, createdAt.
- Firebase rules allow anyone to read everything; writes to `letters` need any authenticated user; `echoes` create is open (validated fields), update/delete need any auth.

---

## 4. Nested L2.0 app — component map (untracked)

```
rahura superteacher L 2.0/
 ├─ server/index.mjs      (Express: /api/ai/status, /api/ai/tutor; static dist; binds 127.0.0.1:8787)
 ├─ server/rina-prompt.mjs (RINA_SYSTEM_PROMPT, makeLessonContext)
 ├─ src/App.tsx           (curriculum browser; localStorage progress)
 ├─ src/components/*      (BookShelf, CurriculumLibrary, LessonWorkspace, MathDiagram, RinaTutor, MorphingHero, StudyMotion)
 ├─ src/lib/content.ts    (fetch curriculum JSON from data/)
 ├─ src/remotion/*        (MathConceptVideo render pipeline)
 └─ data/                 (empty)
```

- The AI endpoint is a reasonable pattern: **server-side key**, request-size cap (12 MB), image-type allowlist (PNG/JPEG/WebP base64 ≤ ~10.5 MB), per-session rate limit (20 req / 10 min via in-memory `Map`), `X-Content-Type-Options`/`Referrer-Policy`/`Permissions-Policy` headers.
- Weaknesses: rate limit is per-IP-derived `sessionId` keyed on client-supplied `sessionId` (spoofable) and the map grows unbounded (memory leak), no CSRF/origin check (binds localhost), no auth.

---

## 5. Architecture diagram

```
                        ┌────────────────────────────────────────────┐
                        │            REPOSITORY (2 products)          │
                        └────────────────────────────────────────────┘

  USERS ──► DESKTOP APP (SuperTeacher / RINA)          USERS ──► LETTERS WEB APP
             │  PyQt6 UI thread (ui.py)                           │  React SPA (Vite)
             │  └─ Learn / Quizzes / Missions / Rina chat          │  └─ /admin (Firebase Auth)
             │  └─ auth landing (local_auth)                       │  └─ /        (public map)
             │  │                                                  │  └─ /notes   (REB math)
             │  ▼                                                  ▼
             │  JarvisLive (asyncio)                    services/letters.js
             │  ├─ mic ──► Gemini Live ◄── speaker        ├─ Firestore letters/echoes (rules)
             │  └─ tool calls: save_memory, shutdown      ├─ Firebase Storage assets
             │       (all other tools disabled)           └─ OSM tiles (canvas)
             │  │
             │  ▼
             │  Services / Business logic (Python)
             │  ├─ curriculum_loader ──► data/curriculum/*.json (2,247 files, LRU-cached)
             │  ├─ official_book_library + official_book_content ──► catalog.json / PDFs (PyMuPDF)
             │  ├─ illustration_loader ──► elearning.reb.rw | *.rtb.gov.rw (allowlist, ≤200 MB)
             │  ├─ memory_manager ──► memory/long_term.json (+ OpenRouter via or_client*)
             │  └─ student_mode / local_auth ──► config/*.json
             │
             ▼
   Storage: config/*.json · memory/*.json · data/** · assets/** · .cache/textbooks/
   External: Gemini Live · (OpenRouter*) · REB/RTB HTTPS
   * or_client source is missing → memory AI extraction is broken at runtime

  ── NESTED, UNTRACKED ─────────────────────────────────────────────
  USERS ─► L2.0 React/TS app ─► Express (127.0.0.1:8787) ─► OpenAI API
                                  └─ static dist/ · rate-limited in-memory
```

---

## 6. Dependency relationships & coupling

| Relationship | Type | Notes |
|---|---|---|
| `ui.py` → `core/*` | Import (hard) | Wide but shallow; most core modules are pure functions on JSON |
| `ui.py` → `main.py` | None (inverted) | `main.py` drives `JarvisUI` facade; UI never imports main |
| `main.py` → `memory_manager` | Hard, but runtime-broken (`or_client`) | Memory extraction silently fails |
| `curriculum_loader` → `official_book_library` | Hard | `official_book_library.py` is **untracked** → fresh clones lose `get_source_links` book resolution (ui.py catches ImportError → feature silently disappears) |
| `core/*` → `config/*` | File I/O | Paths derived from `__file__`; PyInstaller/frozen handled by `sys.frozen` checks |
| Desktop ↔ Web | **None** | No shared code or protocol |
| L2.0 ↔ Desktop | None | Duplicate curriculum-browser concept with different data layout |

### Circular dependencies

- None found at import level. `config/__init__.py` → `scripts/reb_build_units.py` is one-way. `curriculum_loader` → `official_book_library` → files only.

### Hidden / implicit coupling

- `ui.py`'s `_find_math_unit_index` reads **legacy** `data/curriculum/{level}.json` files (`high_school.json` structure) that the new manifest tree does not use — two curriculum formats coexist (`high_school.json` / `math/` legacy vs `index.json` → `manifests/` → `books/`).
- `scripts/reb_build_units.py` writes `data/curriculum/math/` (legacy) which the new UI never reads.
- `main.py`'s `LIVE_MODEL` string pins a dated preview model; `google-genai` versions must stay compatible (requirements pins none).
- `student_mode` reads `student_profile.json`; `ProfileOverlay._submit` sets `student_mode: role == "student"` — **teacher role disables student mode entirely**, enabling the (currently stubbed) OS-control tools if ever restored.

## 7. Important abstractions

1. **`CurriculumNode`** — uniform navigation record; everything in the curriculum is a node with `children_ref`/`content_ref`. This is the app's backbone and is well-designed (lazy, bounded caches, path-safe JSON reads with `relative_to` checks).
2. **Tool declarations → dispatcher** in `main.py` — the model-facing contract; the actual functions are all stubs in the safe build.
3. **`JarvisUI` facade** — isolates Qt from the asyncio tutor loop.
4. **`MathDiagramWidget`** — one widget, ~30 hand-painted diagram types, selected by `lesson_visuals.infer_lesson_diagrams`.
5. **`OfficialTextbookViewer`** — a PDF page renderer with a "Learning Edition" reflow and an "Original page" mode.

## 8. Build-time processes

- `npm run build` (Vite) — Letters app → `dist/` (7.7 MB).
- Nested: `tsc --noEmit && vite build`; `remotion render` for videos.
- Python: no build step; optionally frozen with PyInstaller (`sys.frozen` branches exist but no `.spec`/build script is tracked).

## 9. What is missing architecturally

- **No service layer / no controller layer in the web app** — Firestore SDK calls are made directly from components through one thin `letters.js` helper.
- **No background processing for anything server-side** (the only server is the nested localhost Express app).
- **No configuration abstraction** — paths hardcoded via `Path(__file__)` conventions, two config formats (`api_keys.json` vs `.env` vs `.env.local`).
- **No feature flags** beyond `ACTION_TOOLS_AVAILABLE` and `student_mode`.
- **No telemetry/observability** (see Phase 12).