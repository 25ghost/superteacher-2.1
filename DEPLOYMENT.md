# Rahura AI Rina — Deployment Guide (Rwanda Schools)

## What this app is

**Rahura AI Rina** is a **Windows desktop** Python app for Rwandan students. It is **not** a cloud web platform. Each computer stores profiles and progress locally.

- Voice tutor: Google **Gemini Live** (internet required)
- Text tools: **OpenRouter** free-tier models (internet required)
- Curriculum: local **REB-aligned JSON** (works offline for browsing lessons)

## Requirements

| Item | Details |
|------|---------|
| OS | Windows 10/11 (primary target) |
| Python | 3.11 or 3.12 |
| RAM | 4 GB minimum, 8 GB recommended |
| Microphone | Required for voice mode |
| Internet | Required for AI voice and search |
| Disk | ~2 GB with Playwright browsers |

### System binaries (optional but recommended)

- **ffmpeg** — video/audio processing in file uploads (`ffmpeg -version` to check)
- **Playwright browsers** — run `playwright install` after pip install

### Windows-only Python packages

These are in `requirements.txt` and fail on macOS/Linux:

- `comtypes`, `pycaw`, `win10toast`, `pywinauto`, `pygetwindow`

For non-Windows testing, use a trimmed requirements file without those packages.

## First-time setup

```bash
python setup.py
copy config\api_keys.example.json config\api_keys.json
```

Edit `config\api_keys.json` and add:

1. **Gemini API key** — [Google AI Studio](https://aistudio.google.com/apikey)
2. **OpenRouter API key** — [OpenRouter](https://openrouter.ai/keys)

Then run:

```bash
python main.py
```

On first launch, **create a local account** (username + password). Data stays on that PC only.

## API costs for schools

| Service | Cost model | Notes |
|---------|------------|-------|
| Gemini Live | Google free tier + paid overage | Voice uses more quota than text |
| OpenRouter | Free `:free` models + paid tiers | Free models can rate-limit in class |
| DuckDuckGo search | Free | Fallback when Gemini search fails |

**Plan for 30 students:** this desktop app does **not** share one API pool safely. Each PC needs its own keys, or a school IT policy for key rotation. Budget for paid tiers if free limits fail mid-lesson.

## Security checklist

1. **Never commit** `config/api_keys.json` or `config/accounts.json` (see `.gitignore`)
2. **Rotate keys** if they were ever shared or committed
3. **Student mode** is on by default — blocks games, messaging, desktop control, flights
4. Sign out when sharing a lab computer (Settings → Sign out)

## Assets folder

UI images live in `assets/rahura/`. If missing, the app shows gradient placeholders.

Generate simple placeholders:

```bash
python scripts/generate_assets.py
```

Replace with official Rahura branding images when available.

## Authentication model

This is **local single-machine auth**, not cloud SSO:

- Accounts in `config/accounts.json` (hashed passwords)
- Roles: `student` (default), `teacher` (manual edit in accounts file)
- No server, no email verification, no multi-school sync

For multi-school deployment, plan a future backend or MDM packaging — not included in this release.

## Offline limitations

- Lesson tree, quizzes UI, and profile work offline
- **Rina voice and AI tools require internet**
- No offline LLM is bundled

## Support links

- REB publications: https://www.reb.gov.rw/publications
- REB e-learning: https://elearning.reb.rw/

## License

Personal and non-commercial use (CC BY-NC 4.0). Confirm with Rahura before commercial school licensing.
