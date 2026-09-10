# Phase 11 — External Dependencies

## 1. Python packages (`requirements.txt`)

| Package | Purpose | Where used | Version pinned? | Notes |
|---|---|---|---|---|
| `PyQt6` | GUI toolkit | ui.py | No | Huge; smoke tests run offscreen |
| `sounddevice` | Mic/speaker I/O | main.py | No | PortAudio bindings |
| `google-genai` | Gemini Live + generate_content | main.py, generate_lesson_content.py | No | API version pinned to `v1beta` in code; Live API is preview-grade — **model string already dated** (`gemini-2.5-flash-native-audio-preview-12-2025`) |
| `pillow` | Image processing | (declared; used by scripts/actions historically; no runtime import found in current tree) | No | **LIKELY UNUSED at runtime** |
| `requests` | HTTP | illustration_loader, fetch_official_library | No | Timeouts configured |
| `pymupdf` | PDF parse/render | official_book_content, ui.py viewer, catalog builder | No | Imported lazily |

**Dependency risks (Python):**
- **No pinned versions** — `requirements.txt` bare names; a fresh install can pull incompatible PyQt6/google-genai combos. The local runtime is Python 3.14 while deployment targets 3.11/3.12 (readme/DEPLOYMENT) — PyQt6/sounddevice wheels for 3.14 may not exist; **version drift is a real breakage vector**.
- `google-genai` Live API + `v1beta` is fast-moving; a breaking release silently breaks the tutor (handled by infinite reconnect → invisible).
- Missing runtime dependency: `openai` is imported only by the nested L2.0 server (own package.json). `or_client` (OpenRouter) has **no source and no package entry** — a phantom dependency (DC-01).
- `pillow` appears unused at runtime (checked imports in main/ui/core; only referenced in requirements).

## 2. npm packages (root Letters app)

| Package | Purpose | Notes |
|---|---|---|
| `firebase ^10.14.1` | Auth/Firestore/Storage | Optional at runtime (no `.env`) |
| `react` / `react-dom ^18.3.1` | UI | |
| `lucide-react ^0.468.0` | Icons | |
| `vite ^6`, `@vitejs/plugin-react`, `tailwindcss ^3.4`, `postcss`, `autoprefixer` | Build | |

- package-lock committed ✅. No audit info available offline; `npm audit` recommended.
- **Bundle:** raw textbook `.txt` imports (111k lines) are the biggest dependency on build size.

## 3. npm packages (nested L2.0 app)

| Package | Purpose | Notes |
|---|---|---|
| `express ^5.1` | Local server | Binds 127.0.0.1:8787 |
| `openai ^5.0` | Tutor | Key server-side |
| `remotion` / `@remotion/player` / `@remotion/cli` | Video | Large dep tree |
| `framer-motion`, `katex`, `lucide-react`, `react`, `typescript`, `vite` | UI/build | |

## 4. External services

| Service | Purpose | Where used | Auth method | Data sent | Data received | Failure behavior | Timeout | Retry | Security risk | SPOF? |
|---|---|---|---|---|---|---|---|---|---|---|
| **Gemini Live API** | Voice/text tutoring | main.py session | API key (header) | mic audio, transcripts, system prompt incl. memory + curriculum context | audio + transcripts + tool calls | reconnect 3 s forever | none explicit (SDK) | infinite fixed | Transcripts/PII egress; quota cost | Yes (tutor feature) |
| **OpenRouter (via `or_client`)** | Memory classification/extraction | memory_manager | API key | conversation snippets | YES/NO + JSON facts | **always fails (missing module)** | n/a | n/a | PII to third party (if restored) | Broken already |
| **Firebase Auth** | Web admin login | AdminWorkspace | email/password | credentials | tokens | SDK error → form error | SDK | SDK | Standard | Yes for admin |
| **Firestore** | Letters/echoes | letters.js | SDK + rules | docs | docs | silent empty UI | SDK | none | Rules weaknesses (SEC-01) | Yes for web data |
| **Firebase Storage** | Letter assets | AdminWorkspace | SDK + rules | files | URLs | partial upload → orphaned blobs | SDK | none | Public read; no type checks | Yes for media |
| **OSM tile servers** | Map tiles | MapCanvas | none | tile requests (z/x/y, IP) | PNG tiles | 9 s timeout → placeholder tile; `onerror` marks failed | 9 s | none (cache persists failures) | No auth; usage policy | Degrades gracefully |
| **REB/RTB e-learning** | Official textbook download | illustration_loader | none (public) | GET requests | PDF | IllustrationLoadError → status text | (12, 90) | **none at runtime** | Allowlisted hosts; size caps | Yes for Learning Edition |
| **OpenAI API** | L2.0 tutor | nested server | key server-side | prompts, images, lesson context | answers | 500 generic | SDK default | none | No Origin check (SEC-08) | Yes (nested app) |
| **PyPI / npm** | Dependencies | install | n/a | — | packages | install fails | n/a | n/a | Supply chain | At install |

## 5. Dependency risk register

1. **Unpinned Python deps + 3.14 vs 3.11/3.12 target drift** — highest immediate breakage risk.
2. **Gemini Live preview model pinned by name** — model retirement breaks the tutor with no graceful error.
3. **Phantom `or_client`** — dead import, silent failure (SEC-07/DC-01).
4. **Firestore composite index not documented** for `echoes` query (database.md).
5. **Nested app duplicates the entire web stack** — double dependency surface, untracked.
6. **No dependency auditing** (no `pip-audit`/`npm audit` in CI — no CI at all).
7. **OSM tile dependency** — the map experience is unusable offline; consider local tiles for school networks (DEPLOYMENT.md only allows REB/RTB hosts).
8. **`pillow` unused** (declared, not imported at runtime) — candidate removal (verify before deleting).

## 6. Duplicate / unnecessary dependencies

- `postcss` + `autoprefixer` + `tailwind` standard trio — fine.
- `lucide-react` present in both web apps (separate trees — fine, isolated).
- `openai` vs `google-genai` vs `or_client` — three AI SDKs across three products, no shared layer.
- `pymupdf` vs `pypdf` (catalog builder fallback) — fallback only, acceptable.
- No lockfile for Python at all.