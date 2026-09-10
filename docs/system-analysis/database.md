# Phase 10 — Database Analysis

The system has **no relational database**. Persistence is (a) Firestore for the web app, (b) JSON files for the desktop app, (c) JSON trees for curriculum. Analysis covers each.

---

## 1. Firestore (Letters web app)

### Collections & schema (inferred from `letters.js`, `AdminWorkspace.jsx`, `LetterOverlay.jsx`, rules)

**`letters/{letterId}`**
| Field | Type | Written by | Constraints in rules |
|---|---|---|---|
| `title` | string | admin form | **none** |
| `locationName` | string | admin form | none |
| `lat` / `lng` | number | admin form (toFixed(6)) | **none** (NaN rejected by Firestore; range unchecked) |
| `dateString` | string | admin form | none |
| `textContent` | string | admin form | **none** (unbounded) |
| `portraitUrl` / `audioUrl` | string | upload → getDownloadURL | none |
| `secretClueTags` | array<string> | admin form | none |
| `createdAt` | serverTimestamp | `letters.js` | none |

**`echoes/{echoId}`**
| Field | Type | Written by | Rules |
|---|---|---|---|
| `letterId` | string | public form | is string ✅ |
| `authorName` | string | public form | **no length cap** |
| `textContent` | string | public form | string + ≤1600 ✅ |
| `type` | string | public form | in ['reply','independent_confession'] ✅ |
| `lat` / `lng` | number | public form | **no range check** |
| `createdAt` | serverTimestamp | `letters.js` | — |

### Indexes / queries
- `subscribeLetters`: `collection(letters) orderBy createdAt desc` — requires Firestore composite index? No — single-field order on createdAt is automatic. ✅
- `subscribeEchoes`: `where letterId == X orderBy createdAt desc` — **requires a composite index** (equality + order) that must be created in the Firebase console; not documented in the repo. If missing, echo feeds fail at runtime. ⚠️
- No other queries. **No pagination anywhere** — `letters` and `echoes` are fully loaded into client memory; unbounded growth → slow reads and big bundles.

### Missing constraints / risks
- **No owner field** → no per-doc authorization (SEC-01).
- **Orphaned echoes** — no referential integrity; `letterId` can point to a deleted letter (echoes remain, forever unreadable from UI since overlay needs a letter).
- **Orphaned storage blobs** — uploads happen before `createLetter`; failures leave blobs with no doc.
- **No TTL/soft-delete** — deletion is hard `delete` only; no audit trail.
- **No counters/stats** (e.g., echo count) — reads must fetch all echoes to count.
- **Rules**: letters write has no field allowlist; no `request.resource.data.size()` cap.

## 2. Desktop JSON "databases"

### `config/accounts.json`
```json
{ "accounts": [ { "username", "password_hash": "sha256:<salt>:<hex>", "role" } ] }
```
- No schema version; no indexes needed (≤ handful of accounts, linear scan).
- Security issues in SEC-02/AUTH-D1. No locking on write (single-writer UI).

### `config/student_profile.json`
```json
{ username, avatar_path, avatar_color, xp, streak, theme, sound, completed_lessons[], quiz_scores[], role, student_mode, authenticated, last_study_date }
```
- Written by UI callbacks (`_submit_quiz`, `_complete_lesson`, `_on_profile_done`, `_sign_out`) with **no mutex** — concurrent writes from UI + background threads can interleave and lose data (AP-17).
- `quiz_scores` capped at 50 in `profile_stats`; `xp` accumulates unbounded.
- No integrity: `completed_lessons` can contain stale lesson ids after curriculum renames.

### `memory/long_term.json`
```json
{ "identity": {"name": {"value": "...", "updated": "YYYY-MM-DD"}}, "student_profile": {}, "learning_progress": {}, "preferences": {}, "projects": {}, "relationships": {}, "wishes": {}, "notes": {} }
```
- Capped at 2,200 serialized chars (`_trim_to_limit` evicts oldest by `updated` date).
- Value cap 380 chars; truncated with `…`.
- **Lock-protected** (threading.Lock) ✅. Plaintext PII (SEC-07).

## 3. Curriculum JSON tree

- `index.json` → `manifests/{o_level,a_level,tvet}.json` (+ level files) → `books/full/{pathway}/{level}/{subject}/{book.json, units/*.json, lessons/*.json}`.
- 2,247 JSON files, ~73 books / 408 units / 1,734 lessons.
- Each node: `{id, name, node_type, children_ref|content_ref, status, metadata{source_url, syllabus_url, ...}}`.
- **No database engine** — the LRU-cached loader *is* the DB layer. Manifest cache 16 entries; lesson cache 3 entries / 4 MB; mtime+size invalidation.

### Consistency checks (via `validate_curriculum.py`)
- ✅ refs must stay inside `data/curriculum` (`.json` only)
- ✅ source_url/syllabus_url https + approved hosts
- ✅ reachable lessons have required fields (objectives, reading, deep_explanation, practice, practice_answers, experiment, assignment, checkbox_answers)
- ✅ diagrams types supported
- ⚠️ **No check that `content_ref` files are ≤ cache byte limit** (only runtime eviction); oversized single lessons silently evict siblings.
- ⚠️ `status` field is not validated ("catalogued" vs "ready" strings only checked informally by humans per DEPLOYMENT.md).

### Data-quality issues observed
- Mojibake: `STUDY GUIDE � BIOLOGY` (encoding artifact in lesson content) — AP-15.
- Template lessons share near-identical text across subjects/lessons (AP-20).
- Duplicated content: same REB math text exists in `data/reb_books/*.txt`, `src/notes/*.txt`, and legacy `high_school.json`-derived lessons.
- `data/official_books/catalog.json` references `data/reb_student_books/**` (untracked) — catalog entries are unresolvable on a fresh clone (verified: `official_books/files` is empty).

## 4. Security assessment of persistence layer

| Concern | Desktop JSON | Firestore |
|---|---|---|
| Encryption at rest | None (plaintext) | Google-managed (default) |
| Access control | File permissions (default permissive on Windows) | Rules (weak for writes) |
| Injection | JSON only — no query language | Firestore SDK parameterized; rules are the only filter |
| Data deletion | Manual | No retention policy |
| Backup | None documented | Firebase-managed |

## 5. Recommendations

1. **Firestore:** add composite index doc for `echoes(letterId, createdAt desc)`; add pagination/limit (`limit(100)` + cursor); add `ownerUid` + rules (SEC-01); range-check `lat/lng`; cap `textContent`/`authorName` sizes in rules; add cleanup function for orphaned echoes/blobs.
2. **Desktop:** lock `student_profile.json` writes; schema-version + migration field; move `accounts.json` to a hashed+encrypted store; add backup guidance (DEPLOYMENT.md item).
3. **Curriculum:** add a validator check that lesson files fit the cache budget; validate `status` enum; add a manifest→content integrity check (content_refs referenced exactly once).
4. **Catalog:** commit the catalog-relevant metadata but keep PDFs external with documented acquisition (re-run `fetch_official_library.py`).