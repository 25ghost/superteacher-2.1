# Phase 4 — Authentication Audit

Two authentication systems exist, plus two AI-key mechanisms. Each is analyzed separately. All findings are code-traced.

---

## 1. Desktop app — local file-based auth (`core/local_auth.py`)

### Mechanism

| Aspect | Implementation | Assessment |
|---|---|---|
| Credential storage | `config/accounts.json` — JSON array `{username, password_hash, role}` | Plaintext file on disk; gitignored, but world-readable by default on shared machines |
| Password hashing | `sha256(prefix + salt + ":" + password)` where prefix = `"rahura-rina-v1:"`, salt = `secrets.token_hex(8)` | **Unkeyed SHA-256, one round, no stretching (no PBKDF2/bcrypt/argon2)** — fast to brute-force offline; prefix is a static pepper-like string, not a secret |
| Hash format | `sha256:{salt}:{digest}` | Self-describing, but only "sha256" scheme supported |
| Password policy | min 4 characters | Very weak |
| Session | None. `student_profile.json` has `authenticated: true` | A boolean flag file **is** the session |
| Token/JWT | None | n/a |
| Expiry/refresh | None | Sessions never expire |
| MFA/2FA | None | n/a |
| Email verification | None (no email) | n/a |
| Password reset / recovery | None | **No recovery path** — losing the password locks the profile (but see below) |
| Rate limiting / brute-force protection | None — `authenticate()` iterates accounts with no delays, no attempt caps | Local process, so an attacker with shell access can read the file anyway; still, a GUI attacker can brute force 4-char passwords trivially |
| Account recovery bypass | `accounts.json` empty → **first caller auto-registers** as `student` | Anyone who deletes/renames the file becomes the new owner |
| Logout | `_sign_out()` flips the flag | No invalidation of anything |
| Roles | `register(u,p,role)` accepts role only if `"student"/"teacher"`; `ProfileOverlay` passes no role → always `student` | The `role` param is only reachable via direct file edit or code; UI always registers student. Teacher accounts must be hand-crafted in the JSON |

### Flow trace

```
LOGIN REQUEST  ProfileOverlay._submit (username, password)
→ VALIDATION   register(): username ≥2, password ≥4; authenticate(): non-empty
→ CREDENTIAL CHECK  _verify_hash() — constant-ish compare of hexdigest strings (not constant-time; timing side channel is minor locally)
→ SESSION CREATION  profile dict updated with authenticated:true, role, student_mode
→ STORAGE  config/student_profile.json
→ SUBSEQUENT REQUEST  MainWindow.__init__ reads profile; authenticated → _build_app_shell()
→ USER IDENTITY  self.profile["username"], self.profile["role"]
```

### Weaknesses (desktop)

1. **AUTH-D1 (High): SHA-256 with static prefix, single round.** Offline brute-force of 4-char passwords is trivial (billions of hashes/sec on GPU). `accounts.example.json` even ships an example hash string.
2. **AUTH-D2 (High): Session == mutable flag file.** `student_profile.json` can be edited to `"authenticated": true` with any role; `role: "teacher"` disables `student_mode`, which would enable the (currently stubbed) OS-control tools if restored.
3. **AUTH-D3 (Medium): First-run auto-account.** `authenticate()` registers the first caller as the sole account. On an unattended school machine, the first student to open the app owns the device profile.
4. **AUTH-D4 (Medium): No lockout/rate limit.** Unlimited local attempts.
5. **AUTH-D5 (Medium): No password recovery** and no admin path to reset — operational problem in classrooms.
6. **AUTH-D6 (Low): No hashing iteration or pepper** beyond a fixed string; no migration path if the scheme changes.

### Verified good practices (desktop)

- Salt is random per account (`secrets.token_hex(8)`).
- Passwords are never logged or stored in plaintext.
- The auth module is tiny, isolated, and has a single storage file.
- `ui.py` has a **fail-open fallback**: if `core.local_auth` import fails, `authenticate(u,p)` returns `(bool(u.strip()), "Signed in.", "student")` — any non-empty username logs in. (This is a safety valve that becomes a hole if imports break silently.)

---

## 2. Letters web app — Firebase Auth (email/password)

| Aspect | Implementation | Assessment |
|---|---|---|
| Provider | `signInWithEmailAndPassword` (firebase/auth) | Standard; Google-managed |
| Credential storage | Google's servers | OK |
| Password policy | Firebase defaults (min 6 chars) | OK |
| Session | Firebase ID token + refresh token managed by SDK (localStorage/IndexedDB) | Standard |
| Token expiry/refresh | Automatic by SDK | OK |
| MFA | Not configured | n/a |
| Email verification | Not configured | Accounts created via console only; no self-signup flow in the app |
| Rate limiting | Firebase built-in (per-IP, temporary) | OK |
| Logout | `signOut(auth)` | OK |
| Password reset | Not wired in UI | n/a |
| **Critical gap** | **`isFirebaseConfigured` → auth is optional**; when unconfigured, `/admin` shows the login form but disables the button, and *the public map works with seed data*. When configured, **any** authenticated user (not just admins) gets full publish rights | See authorization audit |

### Flow trace

```
LOGIN REQUEST  LoginGate.handleLogin (email, password)
→ VALIDATION   Firebase SDK
→ CREDENTIAL CHECK  Firebase Auth backend
→ SESSION/TOKEN CREATION  SDK stores tokens
→ SUBSEQUENT REQUEST  onAuthStateChanged → user object → AdminWorkspace renders
→ USER IDENTITY  user (uid) — uid is never written to Firestore documents (no ownership field on letters/echoes!)
```

### Weaknesses (web)

1. **AUTH-W1 (High): No admin role, no ownership.** Authentication gates *access to the form* only. Firestore rules allow any authenticated user to `write` letters and `update/delete` echoes. There is no `customClaims`, no admin uid list, no per-document `ownerUid`.
2. **AUTH-W2 (Low): No email verification/self-service** — fine for a closed admin tool, but the admin account must be provisioned in the Firebase console.
3. **AUTH-W3 (Low): Echo creation is anonymous by design** (public write). This is a product decision; the risk is spam (no throttling in rules).

---

## 3. AI-key mechanisms (desktop)

- **Gemini + OpenRouter keys** live in `config/api_keys.json` (plaintext, gitignored). The app **busy-waits** (`wait_for_api_key`, 0.1 s sleep) until the file exists with both keys + `os_system`.
- `memory/config_manager.py` also writes/reads the same file (`save_api_keys`, `get_gemini_key`, `is_configured` — the latter requires key length > 15).
- **Key exposure surface:** any local process or user on the machine can read the file. There is no OS keychain integration, no encryption at rest. `SetupOverlay` collects keys in a password-masked `QLineEdit` (echo mode) — good, but they are then written plaintext.
- `scripts/generate_lesson_content.py` reads the same file for one-off generation.

---

## 4. Service-to-service / machine auth

- **None exists.** No service accounts, no API keys for the web app backend (there is no backend), no OAuth flows. The only "service" is the nested L2.0 Express server, which authenticates to OpenAI with a server-side API key (from `.env.local`).

---

## Summary table

| System | Method | Strength | Biggest risk |
|---|---|---|---|
| Desktop user auth | salted SHA-256 file | Weak (fast hash, 4-char policy, forgeable flag) | AUTH-D1/D2 |
| Web admin auth | Firebase email/password | Strong (Google-managed) | AUTH-W1 (no roles) |
| Desktop AI keys | plaintext JSON file | Weak at rest | Key theft |
| L2.0 AI key | `.env.local` server-side | Good (off browser) | Accidental commit |

## Recommended fixes (priority order)

1. Move desktop auth to **Argon2id or PBKDF2-HMAC-SHA256 (≥ 310k iterations)** with per-account random salt; keep the `scheme:...` format and migrate on read.
2. Replace the `authenticated` flag with a **local session token** (random 256-bit token stored in a user-only file, checked against a token record with expiry), or at minimum verify the password again at startup.
3. Enforce password policy ≥ 8 chars (NIST guidance) and add **exponential lockout** (e.g., 5 tries → 30 s, doubling).
4. Remove the fail-open `authenticate` fallback in `ui.py`; fail closed with a clear message.
5. For the web app: add **Firestore rules or Firebase custom claims** restricting `letters` writes and `echoes` update/delete to the admin uid(s); store `ownerUid` on documents.
6. Encrypt `api_keys.json` at rest or store keys in the OS keychain (Windows Credential Manager / macOS Keychain); at minimum set restrictive file ACLs.
7. Add an explicit "Change password" and "Reset (delete local account)" flow for classrooms.