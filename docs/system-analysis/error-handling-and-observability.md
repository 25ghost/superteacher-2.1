# Phase 12 — Error Handling & Observability

## 1. Exception handling inventory

| Surface | Pattern | Gaps |
|---|---|---|
| Desktop imports (`ui.py`) | `try/except: fallback` per module | **Fail-open for auth** (SEC-03); silent feature loss for untracked modules (official_book_content, official_book_library) |
| Curriculum loader | Raises `CurriculumDataError`; callers catch → `[]`/`None` | Silent empty trees — UI shows nothing |
| Memory | Broad `except Exception` → `False`/`{}`; 429 suppressed | **Silent total failure** (missing module); user never knows memory is off |
| Tool execution | per-tool try/except → `speak_error` → result text | Errors injected into conversation as plain text; stack traces to console only |
| Gemini session | outer `while True` + `except` → reconnect 3 s | Infinite; no distinction of auth vs network; no cap |
| Audio tasks | `except → logger.error → raise` | TaskGroup cancellation → whole session dies → reconnect |
| PDF download | `IllustrationLoadError` → status label | No retry |
| Letters web | `catch (err) → setStatus(err.message)` | `onSnapshot` errors unhandled → silent empty map; `createEcho` errors unhandled in overlay (finally only) |
| L2.0 server | try/catch → 500 generic + console.error | No structured logging; no timeout on OpenAI call |

## 2. Error boundaries / user-facing errors

- **Desktop:** errors mostly become status labels or log lines; no dialog system; `speak_error` narrates tool failures aloud ("Sir, X encountered an error.").
- **Web:** `AdminWorkspace` shows `err.message` verbatim (Firebase error strings can be technical); `LetterOverlay` shows **nothing** on echo-create failure (the `finally` resets state; error swallowed). `NotesReader` shows generic error → fallback raw text.
- **No global error boundary** in React (no `componentDidCatch`/`ErrorBoundary`); a crash in a component blanks the route.

## 3. Logging

| Where | What | Format |
|---|---|---|
| `main.py` | session events, tool calls (`🔧 name args`), results (first 80 chars), memory saves | `logging` to console |
| `ui.py` | log widget lines (You/Rina/SYS/ERR) | in-app UI |
| scripts | print() to stdout | plain |
| L2.0 server | console.error only | plain |
| Web | none | — |

**Sensitive data in logs:** tool `args` (may include message text, file paths), memory keys/values (`logger.info(f"Memory 💾 save_memory: {category}/{key} = {value}")` — **stores the remembered fact in logs**), first 80 chars of tool results. Not redacted.

## 4. Monitoring / metrics / tracing / alerts

- **None.** No metrics endpoint, no tracing, no alerting, no error-reporting SDK (no Sentry etc.).
- Desktop logs are lost on close (no file).
- Web app: no analytics.

## 5. Retry / timeout / circuit breakers

| Flow | Timeout | Retry | Circuit breaker |
|---|---|---|---|
| Gemini Live | SDK default | infinite 3 s (fixed) | none |
| PDF download | (12, 90) | none | none |
| fetch_official_library crawl | (45, 90) page, (12, 90) file | urllib3 Retry(3, backoff 1.0, on 429/5xx) | none |
| Firestore onSnapshot | SDK | none | none |
| Storage upload | SDK | none | none |
| OpenAI (L2.0) | SDK default | none | none |
| OSM tiles | 9 s | none (failed tiles stay failed in cache) | none |
| Quiz/lesson writes | n/a (local) | n/a | n/a |

## 6. Where failures silently occur (watch list)

1. **`or_client` missing** — memory extraction dead (silent).
2. **Firestore unconfigured/offline** — web app silently renders seed/empty data; no banner (only the admin page shows a config hint).
3. **`onSnapshot` errors** — no handler in `subscribeLetters`/`subscribeEchoes`.
4. **`createEcho` failure** — error swallowed in `LetterOverlay`.
5. **Untracked core modules** — on a fresh clone, Learning Edition silently disappears.
6. **Auth import failure** — fail-open login (SEC-03).
7. **Lesson JSON missing** — fallback template content is generated silently.
8. **Reconnect loop** — bad key produces endless logged 403/429s with no user-facing "check your key" state.
9. **Profile JSON write races** — lost XP/streak updates.
10. **Orphaned storage blobs** — upload success + doc-create failure leaves garbage.

## 7. Recommendations

1. Add a **rotating file log** (e.g., `logs/app.log`) + `--verbose` flag; redact tool args/memory values.
2. Add an **in-app error banner/notification queue** (desktop status chip; web toast) for recoverable errors; a React `ErrorBoundary`.
3. Implement **exponential backoff** for Gemini reconnect; distinguish 401/403 (→ show SetupOverlay) from transient.
4. Add retry (with backoff) to `illustration_loader`; surface cache misses clearly.
5. Handle `onSnapshot` error callbacks in `letters.js` and show a "reconnecting" state.
6. Add error logging + structured JSON for scripts; make validation scripts CI-runnable.
7. Instrument counters: sessions, tool calls, memory saves, quiz completions, echo creates (opt-in, privacy-safe).