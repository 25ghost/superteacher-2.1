# Rahura AI Rina — Voma Ubwenge

**Rahura AI Rina** is a Windows desktop superteacher app for Rwandan students, aligned with the **Rwanda Education Board (REB)** curriculum. Voice tutoring uses **Gemini Live**; text tools use **OpenRouter**.

> See **[DEPLOYMENT.md](DEPLOYMENT.md)** for school setup, API costs, security, and offline limits.

---

## Features

| Feature | Description |
|---------|-------------|
| REB curriculum | Primary, S1–S6, TVET pathways in local JSON |
| Voice tutor (Rina) | Real-time Gemini Live conversation |
| Learn & quizzes | Structured lessons and knowledge checks |
| Student mode | Blocks games, messaging, and OS control tools |
| Local accounts | Username + password stored on this device only |
| Kinyarwanda support | Bilingual UI hints; Rina responds in the user's language |

---

## Quick start

```bash
pip install -r requirements.txt
playwright install
copy config\api_keys.example.json config\api_keys.json
```

Add your **Gemini** and **OpenRouter** keys to `config\api_keys.json`, then:

```bash
python main.py
```

Optional placeholder images:

```bash
python scripts\generate_assets.py
```

---

## Requirements

| Requirement | Details |
|-------------|---------|
| OS | Windows 10/11 (recommended) |
| Python | 3.11 or 3.12 |
| Microphone | For voice mode |
| Internet | Required for AI features |
| API keys | Gemini + OpenRouter (see DEPLOYMENT.md) |

---

## Configuration

| File | Purpose |
|------|---------|
| `config/api_keys.json` | Gemini + OpenRouter keys (not committed) |
| `config/accounts.json` | Local user accounts (not committed) |
| `config/student_profile.json` | XP, streak, completed lessons |
| `data/reb_resources.json` | REB daily subject order P4–S6 |
| `data/curriculum/` | Lesson trees |

---

## Security notes

- **Rotate API keys** if they were ever shared publicly
- Use **Sign out** on shared lab PCs (Settings)
- Student mode is enabled by default for `role: student`

---

## License

Personal and non-commercial use (CC BY-NC 4.0). Based on the MARK XXXIX-OR assistant framework.
