# Phase 13 — Performance

Evidence-based and strongly-suspected bottlenecks only. No premature optimization.

---

## 1. Desktop app

### P-1 · `get_node_by_path` re-traversal (confirmed)
- **Where:** `core/curriculum_loader.get_lesson_content`, `get_source_links`, `get_unit_metadata`, `ui.py._open_lesson` subject detection, `main.py.get_lesson_context`.
- **Problem:** Each call re-walks the tree from `get_levels()` downward (`get_node_by_path` loops `get_children` per level). `get_source_links` calls `get_node_by_path` **for every prefix** (O(depth) traversals), and `_open_lesson` calls `get_node_by_path` repeatedly for the same path. Manifest lookups are cached (LRU 16), but the traversal itself is not memoized.
- **Impact:** Bounded (manifest JSON is small, cache hits), but repeated per-click overhead grows with tree depth (O(levels × children-scan)); visible on slower school machines during navigation.
- **Fix:** memoize `get_node_by_path(path_tuple)` (cache invalidated on mtime) or return the resolved path chain in one pass.

### P-2 · Infinite 3 s reconnect loop (confirmed)
- **Where:** `main.py` `JarvisLive.run`.
- **Problem:** On any persistent failure the app reconnects forever every 3 s — repeated network/TLS setup, quota calls; pins CPU when audio tasks die and restart.
- **Fix:** backoff 3→60 s; stop on auth errors (see SEC-09).

### P-3 · `_update_memory_async` per turn (confirmed)
- **Where:** `main.py` `_receive_audio` spawns a daemon thread per turn; each thread (if `or_client` existed) would do an LLM round-trip.
- **Problem:** N threads per session turn; currently the import fails fast (cheap), but if restored there's no dedupe beyond `_last_memory_input` single-turn guard; long sessions spawn many threads.
- **Fix:** a single worker + queue.

### P-4 · Quiz/profile JSON writes (minor)
- Whole `student_profile.json` rewritten on each quiz submit — trivial file size; fine.

### P-5 · PDF page rendering (accepted)
- `_page_pixmap` renders per page at up to 3× scale; bounded by page size; acceptable for on-demand use.

### P-6 · `find_best_source_page` (confirmed)
- Opens the whole PDF (`pymupdf.open`) and scans **every page** in a background thread per lesson open; for 400-page books this is a full-text scan of the document each time (cached only by OS). Runs once per viewer open — acceptable but could cache the page-index per book.

## 2. Letters web app

### P-7 · Whole-collection reads, no pagination (confirmed)
- `subscribeLetters` fetches **all** letters; `subscribeEchoes` fetches all echoes for a letter. With public anonymous writes (SEC-06), collections can grow without bound; every client downloads the full `letters` collection on load and on every change (real-time snapshot re-sends changed docs only, but the initial fetch is full).
- **Fix:** `limit()` + `startAfter` cursor; aggregate echo counts server-side (cloud function or denormalized counter).

### P-8 · Bundle size — 111k lines of textbook text (confirmed)
- `noteParser.js` dynamically imports `Mathematics-S{1,2,3}-SB.txt?raw` (23,810 / 14,730 / 25,852 lines). `dist/` is 7.7 MB total; the notes chunks dominate (each ~1.5–2 MB of text).
- **Impact:** Slow first paint for `/notes/*` on school bandwidth; Vite splits per level (good) but the S1 chunk is huge.
- **Fix:** preprocess to structured JSON (one build step), gzip served; or lazy-load sections.

### P-9 · MapCanvas re-render on every viewport change (confirmed)
- The canvas redraws all visible tiles + pins + threads + vignette each frame during pan/zoom/inertia (`useEffect` on `viewport`), and `tileVersion` bumps on every tile load — frequent full redraws while dragging. Tile cache (Map) prevents re-fetch, but **all loaded tiles are re-drawn per frame**.
- **Fix:** draw only the dirty region; keep pin layer on a separate canvas; throttle redraws to rAF (already rAF-driven for inertia) — acceptable for desktop, noticeable on low-end laptops.

### P-10 · `pinPositions` recompute per frame (minor)
- `useMemo` on `[letters, viewport]` — recomputed on every pan frame (letters × projection math); small N, fine.

### P-11 · Firestore rules overhead
- Public reads + client-side filtering: no server-side filtering by region; geo queries would need geohashing. Defer until collections grow.

## 3. Nested L2.0 app

### P-12 · In-memory rate-limit Map growth (confirmed)
- `requests` Map never expires entries older than 10 min (they're filtered but never deleted) → unbounded growth in long-running server.
- **Fix:** periodic pruning or TTL map.

### P-13 · `express.static` with `maxAge: 1h` — fine.

## 4. Build/data pipelines

### P-14 · `validate_curriculum.py` full traversal (accepted)
- Loads every reachable lesson (1,734) through the 3-entry cache with `clear_content_cache` — O(n) file reads; runs in minutes, not seconds. Acceptable for release gate; add a `--changed` mode.

### P-15 · `build_official_book_catalog.py` re-hashes every PDF (accepted)
- SHA-256 of all 106 PDFs on each run; `--no-hash` exists. Fine.

### P-16 · Curriculum loader cache thrash with legacy lookups
- `_find_math_unit_index` reads `data/curriculum/high_school.json` (large) on each quick-access lesson open — repeated full-file parse. Fix by caching or dropping legacy path (AP-03).

## 5. Priority

| # | Item | Impact | Effort |
|---|---|---|---|
| P-7 | Firestore pagination/limits | High (web growth) | Low |
| P-8 | Notes bundle (structured JSON) | Medium-High (first paint) | Medium |
| P-9 | Canvas dirty-rect | Medium (low-end machines) | Medium |
| P-1 | Path traversal memoization | Low-Medium (navigation latency) | Low |
| P-2 | Reconnect backoff | Low-Medium (resource burn) | Low |
| P-12 | Rate-map pruning | Low | Trivial |