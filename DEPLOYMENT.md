# SuperTeacher school deployment

## Runtime

- Windows 10/11
- Python 3.11 or 3.12
- 4 GB RAM minimum; 8 GB recommended
- Internet only for AI tutoring and learner-requested official resources

Install and start:

```powershell
python -m pip install -r requirements.txt
python main.py
```

The Learn catalog and reviewed lesson JSON work offline. No Playwright browser,
system-control package, installer script, or bulk PDF download is required.

## On-demand resource policy

Curriculum navigation reads only small JSON manifests. Opening one lesson reads
that lesson's JSON file and places it in a three-entry, 4 MB bounded cache.
Official REB/RTB URLs are launched only from a learner click. This avoids loading
all books, images, diagrams, and PDFs at startup.

For school networks, allow official HTTPS resources from:

- `elearning.reb.rw`
- `www.elearning.rtb.gov.rw`

Do not mirror or redistribute official books until the school has confirmed the
applicable permissions. Keep source attribution and distinguish official
material from SuperTeacher's extra explanations and exercises.

## Security checklist

1. Keep API keys out of Git and use separate keys per deployment.
2. Keep the removed shell, computer-control, shutdown, download, and browser
   automation modules disabled.
3. Use standard student Windows accounts without administrator rights.
4. Patch Python and dependencies regularly.
5. Review new curriculum JSON and source domains before release.
6. Back up `config/student_profile.json` according to the school's privacy
   policy.

## Content release checklist

Before changing a catalog node from `catalogued` to `ready`:

1. Verify its official REB or RTB source and syllabus.
2. Check every unit and module is represented in official order.
3. Review explanations for factual accuracy and clear source distinction.
4. Verify practice answers, experiments, assignments, and CheckBox answers.
5. Render every declared diagram type in the desktop app.
6. Run the curriculum validation and desktop smoke tests.
