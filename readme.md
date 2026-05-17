# SuperTeacher desktop

SuperTeacher is a Python/PyQt desktop learning app for Rwanda's O Level,
A Level, and TVET pathways. Start it with `main.py`.

## Run

Use Python 3.11 or 3.12:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Gemini configuration is optional for browsing local lessons. Voice tutoring
needs a valid key in `config/api_keys.json`.

## Lazy curriculum layout

The Learn feature does not import one large curriculum file. It follows small
references and opens each file only when the learner reaches it:

```text
data/curriculum/index.json
  -> manifests/<pathway>.json
  -> manifests/<pathway>/<level>.json
  -> books/<pathway>/<level>/<book>/book.json
  -> books/<pathway>/<level>/<book>/units/<unit>.json
  -> books/<pathway>/<level>/<book>/lessons/<lesson>.json
```

Navigation manifests contain titles and references only. A lesson file contains
the reading, segmented explanation, examples, practice, experiment, assignment,
CheckBox answers, and diagram instructions for that lesson. Only the three most
recently opened lesson files are retained in the bounded in-memory cache.

Official REB or RTB books are not downloaded at startup. An official source URL
is opened only when the learner presses **Open official book** or
**Open syllabus**.

## Content status

Every O Level, A Level, and TVET catalog card now opens a study hierarchy:

- 73 subject books or trade pathways
- 408 units or competency modules
- 1,734 independently loaded lesson files

The full-access library preserves the repository's archived local lesson notes
where they exist. Topics that had titles but no written content receive a
clearly identified SuperTeacher structured study guide with objectives, deep
explanation prompts, practice, experiment, assignment, and CheckBox answers.
These guides should be reviewed against the linked official book or syllabus
before a high-stakes school release.

## Illustrations

Every lesson has a topic-selected visual such as a graph, Venn diagram, number
line, circuit, force diagram, wave, timeline, process flow, bar chart, or concept
map. These visuals are drawn only when that lesson is opened.

Lesson JSON may also reference local images under `assets/` or
`data/curriculum/media/`; those files are likewise opened only with the selected
lesson. When an approved official REB/RTB PDF is available, **Load official
visuals** downloads it only after a learner click and renders one requested page
at a time. Downloads are restricted to approved official HTTPS hosts, bounded
to 200 MB, signature-checked, and stored in the ignored `.cache/textbooks/`
folder.

## Security

The original repository included broad computer-control, shell, shutdown,
download, and browser-automation modules. Those modules are disabled/removed
from this working tree, and `main.py` exposes only the tutoring-safe tool subset.
Do not restore those modules on student computers without a separate security
review and explicit administrator approval.

Local secrets and student profiles must stay out of version control.
