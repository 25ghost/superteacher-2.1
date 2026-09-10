# Phase 5 — Authorization Audit

Analyzed separately from authentication. The system has **no formal authorization model**: no roles table, no permission matrix, no ownership fields. What exists is a mix of client-side gating and two rule files.

---

## 1. Desktop app

### What gates exist

| Gate | Enforced where | Checks |
|---|---|---|
| `student_mode` | `core/student_mode.py` (`is_student_mode`) | Reads `config/student_profile.json`: `student_mode` key, else `role == "student"`, **defaults to True (student)** on any error |
| Tool allowlist | `student_mode.filter_tool_declarations` + `_execute_tool.tool_allowed` | In student mode only `{web_search, file_processor, youtube_video, screen_process, reminder, weather_report, browser_control, file_controller, code_helper, open_app, save_memory, shutdown_rina}`; explicit blocklist includes `send_message, game_updater, flight_finder, desktop_control, computer_control, computer_settings, dev_agent, agent_task, cmd_control, generated_code` |
| **Effective tool set** | `main.py` | `ACTION_TOOLS_AVAILABLE = False` → only `save_memory` + `shutdown_rina` declared to the model; every other tool name maps to `_disabled_action` stub |

**Who can call what:** In the shipped build, the model (and therefore the student) can only call `save_memory` and `shutdown_rina`. All OS-control tools are both undeclared **and** stubbed. Student mode is therefore **defense in depth that is currently redundant** — but if `ACTION_TOOLS_AVAILABLE` is ever set True, `student_mode` becomes the only guard, and it is bypassable by editing `student_profile.json` (see AUTH-D2).

### Authorization gaps (desktop)

1. **AUTHZ-D1 (High): client-file trust.** `role` and `student_mode` live in an editable JSON. A student with file access can set `role: "teacher"` / `student_mode: false` and unlock every tool once the action pack is restored.
2. **AUTHZ-D2 (Medium): UI shows role-unaware content.** Classroom/Community/Missions pages are decorative (static cards) — no per-role data.
3. **AUTHZ-D3 (Low): quiz answers ship with content.** The "authorization" model for answers is client-side reveal; by design, but worth stating.

---

## 2. Letters web app

### Firestore rules (`firebase.rules`) — the *only* server-side enforcement

```
letters/{letterId}:
  read:  true
  write: request.auth != null        ← ANY signed-in user

echoes/{echoId}:
  read:  true
  create: request.resource.data.keys().hasOnly([letterId, authorName, textContent, type, lat, lng, createdAt])
          && letterId is string && textContent is string
          && textContent.size() <= 1600 && type in ['reply','independent_confession']
  update, delete: request.auth != null   ← ANY signed-in user
```

Storage rules (`storage.rules`):
```
letters/{allPaths=**}: read: true; write: request.auth != null
```

### Per-endpoint analysis

| Operation | Who can call | What they can access | What prevents unauthorized access |
|---|---|---|---|
| Read letters/echoes | Anyone (anonymous) | All letters + echoes, incl. `secretClueTags`, coordinates, audio URLs | Intended: public map |
| Create letter | Any signed-in user | New letter doc, arbitrary fields (rules only check `auth != null`, **no field allowlist for letters**) | Nothing beyond sign-in |
| Update/delete letter | Any signed-in user | Modify/delete any letter (no owner field exists) | Nothing |
| Create echo | Anyone | Create echoes on any letterId (validated fields only) | Field allowlist + type/len checks |
| Update/delete echo | Any signed-in user | Modify/delete any echo | Nothing |
| Upload asset | Any signed-in user | Write to `letters/**` (any folder/name) | Nothing but sign-in |
| Read asset | Anyone | All uploaded assets | Intended |

### Findings

1. **AUTHZ-W1 (CRITICAL if deployed): Broken object-level authorization — no ownership.** Firestore documents carry **no `ownerUid`**. Any authenticated user can overwrite/delete *any* letter and *any* echo. There is no `request.auth.uid == resource.data.ownerUid` anywhere. Because the admin desk is a real, deployable surface (`/admin` + `.env.example`), this is the most severe finding in the web app.
2. **AUTHZ-W2 (High): Letters `write` has no field validation.** Unlike echoes, letters accepts arbitrary fields, arbitrary text length (e.g., 10 MB `textContent`), and arbitrary `lat`/`lng` (could be NaN/out-of-range → Firestore rejects NaN but accepts ±inf-free invalid geo data). Client sanitizes filenames only.
3. **AUTHZ-W3 (High): No admin-role check.** "Admin" is a UI label, not a permission. Firebase custom claims or an admin-uid allowlist in rules is required.
4. **AUTHZ-W4 (Medium): Anonymous echo spam.** Unauthenticated create with no rate limit → collection flooding, storage/read cost abuse (public reads amplify).
5. **AUTHZ-W5 (Low): `lat`/`lng` accepted from client for echoes** — trivial to falsify, enabling map vandalism (pins anywhere).
6. **AUTHZ-W6 (Low): storage rules allow any authenticated user to write anywhere under `letters/`** including overwriting existing blobs (no per-owner path check).

---

## 3. Nested L2.0 app

| Endpoint | Who can call | Access | Prevention |
|---|---|---|---|
| `/api/ai/status` | Anyone on localhost | Knows model + whether key is configured | None (benign) |
| `/api/ai/tutor` | Anyone on localhost | Uses the OpenAI key budget (cost), sends arbitrary prompts/images | In-memory 20 req/10 min per `sessionId` (client-supplied → **spoofable**), no Origin check, no auth |

- AUTHZ-L1 (Low-Medium, local-only): a malicious webpage opened by the user could `fetch('http://127.0.0.1:8787/api/ai/tutor')` and drain the OpenAI quota (no CORS preflight protection; no Origin validation).

---

## 4. IDOR / privilege-escalation sweep

| Check | Result |
|---|---|
| IDOR (access by id) | Desktop: curriculum JSON paths are **path-traversal-safe** (`_safe_json_path` resolves + `relative_to` check; `resolve_lesson_media` checks allowed roots) 🟢. Web: echoes keyed by public `letterId` — readable by all (by design); update/delete of any doc by any user 🔴 |
| Horizontal privilege escalation | Desktop: single-user machine — n/a. Web: any user = any doc 🔴 |
| Vertical privilege escalation | Desktop: edit `student_profile.json` → teacher 🔴. Web: any signed-in user → admin functions 🔴 |
| Client-controlled role fields | Desktop: `student_profile.json` (local file) 🔴. Web: none (roles don't exist) |
| Admin endpoints exposed to normal users | Web: `/admin` requires auth but **not admin** 🔴 |
| Frontend-only checks | Web: `canSubmit` gating is UX only; rules are the enforcement (and they're weak) |
| Duplicated/inconsistent authorization | Desktop: `filter_tool_declarations` + `tool_allowed` + `ACTION_TOOLS_AVAILABLE` are three overlapping layers with **different tool lists** (e.g., `filter_tool_declarations` uses ALLOWED_TOOLS while `_execute_tool` has its own `if name == …` chain) — the declarations and the dispatcher can drift |

---

## 5. Summary & recommended model

| Surface | Current model | Recommended |
|---|---|---|
| Desktop tools | 3 overlapping client-side layers | Single source of truth: one tool-policy table keyed by role, checked once in `_execute_tool`; keep stubs as the final backstop |
| Desktop roles | Editable JSON flag | Password-verified role at startup (token), or role signed at account creation (store HMAC of role) |
| Web letters | Auth-only write | Add `ownerUid` to letters/echoes; rules: `write if request.auth.uid == resource.data.ownerUid` (create: `== request.auth.uid`); admin allowlist for delete/update-any |
| Web echoes create | Public with field allowlist | Keep public (product), add size caps on authorName (≤80), lat/lng range checks, and (Firebase-supported) per-IP throttling where possible |
| Web storage | Auth-only write | Restrict path to `letters/{uid}/{rest}` and require `request.auth.uid == path` segment |
| L2.0 server | In-memory per-session | Validate `Origin` header against `http://127.0.0.1:8787`/`5173`; cap the requests Map; add a lightweight bearer token in `.env.local` |