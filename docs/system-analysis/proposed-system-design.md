# Phase 14 — Proposed System Design

Describes the system as it **should** exist, acknowledging what exists today. This is a target architecture, not a commitment to rewrite everything at once — migration difficulty is noted per section.

---

## 1. System overview

**Today:** one repo, two shipped products (desktop SuperTeacher/RINA, web "Letters") plus a stray nested copy (L2.0), sharing no code, no CI, no tests, and three persistence styles.

**Target:** keep the two products (they serve different users), extract the shared concepts (curriculum schema, AI-tutor policy, secret handling, validation pipeline) into shared, tested modules; give the L2.0 app a clear fate (fold into desktop as the web companion or delete); add a thin, secure backend boundary for anything the browser must not do directly.

## 2. Architectural style

- **Desktop:** layered — UI (PyQt) → services (`core/*`) → data (JSON trees). Keep this, formalize the layers, remove fail-open imports.
- **Web (Letters):** serverless-first (Firebase) is fine for its scope; add a tiny Cloud Functions layer only for admin ops (delete letter, moderation) and rate limiting.
- **Tutor backend:** keep keys server-side; a single "AI gateway" pattern (desktop talks to providers directly by design — it is offline-first; L2.0 uses a localhost proxy). No cloud dependency added unless a managed deployment is required.

## 3. Component architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      RAHURA / SUPERTEACHER                    │
├───────────────┬──────────────────────────┬───────────────────┤
│ Desktop (PyQt)│  Web Letters (React/FB)  │  Web L2.0 (React) │
│  ui/ pages    │  map + admin + notes     │  curriculum web   │
│  chat/tools   │  Firebase rules          │  localhost server │
├───────────────┴──────────────────────────┴───────────────────┤
│ Shared: curriculum-schema (data/**), validation scripts,     │
│         secret handling (keyring), student_mode policy,      │
│         content provenance rules                             │
├──────────────────────────────────────────────────────────────┤
│ Persistence: JSON trees + config JSON · Firestore/Storage ·  │
│              memory JSON (encrypted) · PDF cache             │
└──────────────────────────────────────────────────────────────┘
```

## 4. Frontend architecture

### 4.1 Letters (React SPA)
- **Routing:** keep pathname-based routing (fine at this scale) or adopt `react-router` when >4 routes.
- **State:** extract a `LetterStore` interface — `FirestoreLetterStore` and `SeedLetterStore` (today's hybrid becomes two explicit implementations). Single sort utility.
- **Admin:** keep Firebase Auth gate; **add server-enforced admin identity** (see 8).
- **Data fetching:** paginate letters (limit 100 + cursor); echoes limited (limit 50) with a counter field on letters.
- **Notes:** prebuild structured JSON (units/sections/examples) at build time; remove runtime regex parsing; keep raw-text fallback.
- **Error handling:** add ErrorBoundary + toast system; handle `onSnapshot` errors.

### 4.2 L2.0 (decision required)
- **Option A (recommended):** promote to the official web companion — track it, share the desktop curriculum loader schema, keep the localhost Express + OpenAI gateway, add Origin validation and bounded rate map.
- **Option B:** archive/delete; do not leave a third untracked tree in the repo.

## 5. Backend architecture

- **Desktop:** split `main.py`/`ui.py` into: `app/config.py` (single path/secret module), `app/session.py` (token-based auth), `app/tools/` (registry-driven dispatch), `app/chat/` (Gemini session with backoff), `core/*` stays.
- **Tool registry (core improvement):** one table per tool: `{name, schema, handler, student_allowed, teacher_only, stubbed}`; declarations + dispatcher + student filter all derive from it. `ACTION_TOOLS_AVAILABLE` becomes a deployment flag in `config/`.
- **Auth:** replace the `authenticated` flag with a device-local session token (random 256-bit, stored in user-profile file with restrictive ACL, HMAC-checked at startup, expiry 30 days). Roles stored with an HMAC so students cannot flip `role`.
- **AI gateway policy:** a `providers.py` module abstracts Gemini Live / OpenRouter / (future) local models; memory extraction runs on a **local** classifier by default (no PII egress) with an opt-in cloud mode; memory JSON encrypted at rest.

## 6. Database architecture

- **Curriculum:** keep the lazy JSON tree (it works and is cache-friendly) — add: schema version field, `status` enum validation, content-size budget check, one-pass `get_node_by_path` memoization.
- **Firestore:** add `ownerUid` to letters and echoes; rules enforce `ownerUid == request.auth.uid`; admin allowlist for moderation; document the `echoes(letterId, createdAt)` composite index; add App Check where feasible; TTL cleanup (Cloud Function) for orphaned echoes/blobs.
- **Desktop config/profile:** single-writer lock; atomic writes (write-temp + rename); schema-version + migration hook; optional export/backup.

## 7. Authentication architecture

| Surface | Today | Target |
|---|---|---|
| Desktop | SHA-256 file + flag | Argon2id + session token + HMAC role + lockout |
| Web admin | Firebase email/password, any user = admin | Firebase + custom claim `admin: true` checked in rules; App Check |
| Echo creation | anonymous | keep public, but rate-limited (rules timestamp window) + validated geo |
| AI keys | plaintext JSON | OS keyring; per-deployment keys; `is_configured()` via config module |

## 8. Authorization architecture

- **Single enforcement point:** Firestore rules (web) + tool registry (desktop). No frontend-only checks for anything security-relevant.
- **Web model:** letters/echoes owned docs; admin allowlist uid(s); storage path bound to `{ownerUid}`; moderation endpoint (delete any) behind `admin` claim.
- **Desktop model:** role policy table in one module; student mode remains the default; teacher flag requires HMAC-verified token.
- **Content:** provenance field surfaced to learners ("SuperTeacher study guide — verify against official book") rather than hidden.

## 9. External integrations

- **Gemini Live:** keep, but: configurable model name; auth-error fast-fail; backoff; opt-in consent note for transcripts.
- **OpenRouter (`or_client`):** restore the module **or** delete the path. If restored: key from config, local-first extraction.
- **REB/RTB:** keep allowlist + size caps; add retry with backoff and Range-resume; document licensing per book (catalog already tracks authority).
- **OpenAI (L2.0):** keep server-side; add Origin check, bounded rate map, request timeout.
- **OSM:** add local-tile fallback for offline schools (optional).

## 10. Data flows (target)

Same flows as today (Phase 3) with three changes:
1. Memory: local classifier → local storage → (opt-in) cloud; every flow logs an audit event.
2. Web writes: authenticated & owned; anonymous echoes validated + throttled.
3. Desktop login: token verified at startup; profile writes serialized.

## 11. Pipelines (target)

- **CI (new):** GitHub Actions: `validate_curriculum.py` → `verify_official_library.py --rehash` → pytest (core) → Vitest (letters) → `vite build` → smoke renders (offscreen).
- **Content release:** generator → validator → human review gate (`status: ready`) → smoke render → release record (DEPLOYMENT.md checklist automated where possible).
- **Library:** fetch → catalog → verify, all tracked scripts, PDFs external with documented re-acquisition.
- **Runtime pipelines:** as today, plus backoff, retries, error banners.

## 12. Error handling

- Desktop: error-toast queue + log file; fail-closed imports with explicit feature flags.
- Web: ErrorBoundary + toasts; `onSnapshot` error state ("reconnecting…"); upload transactions with cleanup.
- All AI calls: structured error codes (AUTH, QUOTA, NETWORK, MODEL) → distinct UX.

## 13. Security boundaries

- Desktop: OS user boundary; encrypted secrets (keyring); encrypted memory; token-based session.
- Web: Firestore/Storage rules as the trust boundary; App Check for client integrity; admin claims server-side.
- AI gateway: keys never on the client; origin checks; rate limits.

## 14. Observability

- Rotating file log + `--verbose`; redacted args.
- Optional privacy-safe telemetry toggle (sessions, tool usage, errors only — no content).
- Scripts emit structured JSON summaries; CI consumes them.

## 15. Deployment architecture

- **School desktop:** unchanged (Windows, offline-first, keyring-backed keys); add signed build + version manifest + self-update check (optional).
- **Letters web:** Firebase hosting + rules + optional Cloud Functions; `.env` documented; admin provisioning documented.
- **L2.0:** localhost Express behind Vite proxy (as today) or a managed host with auth.

## 16. Scalability

- Curriculum: bounded caches already; memoized path lookups; validation parallelizable.
- Firestore: pagination + counters; App Check; geo-queries later (geohash) if the map grows.
- Tutor: per-deployment keys; concurrency limits on the gateway; queue for memory extraction.

## 17. Disaster / recovery

- **Backups:** profile/memory/config export (school policy per DEPLOYMENT.md); Firestore managed backups; catalog + acquisition report are the source-of-truth for re-downloading official books.
- **Restore:** `fetch_official_library.py` + `build_official_book_catalog.py` rebuild the library from scratch; curriculum is versioned in git.
- **Incident:** log files + structured session records enable triage; add a health self-check page (desktop "System info" + web `/healthz`).

---

## Migration roadmap (effort-ordered)

1. **Track the untracked code** (core modules + scripts) — minutes, unblocks everything.
2. **Rules hardening** (ownerUid + admin claims) — hours.
3. **Desktop auth hardening** (Argon2id + token session + fail-closed) — 1–2 days.
4. **Tool registry** refactor — 2–3 days.
5. **Split ui.py** — 3–5 days (mechanical).
6. **Test suite (core + web)** + CI — 3–5 days.
7. **Pagination + notes JSON prebuild** — 2–3 days.
8. **Memory decision** (restore `or_client` or local extraction) — 1 day.
9. **L2.0 fate decision** — 1 day + cleanup.
10. **Observability + keyring** — 2–3 days.