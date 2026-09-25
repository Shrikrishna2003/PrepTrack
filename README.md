# PrepTrack

A coding-interview preparation tracker built with Flask + MySQL. Log solved
problems, track company-wise prep (TCS / Infosys / Atidan), keep a daily
streak, and review progress with Chart.js.

## Features

- **Auth** — register / login / logout with hashed passwords (Werkzeug)
- **Problem log** — add, edit, delete: title, company, topic, difficulty, platform, link, status, date, time taken
- **Search, filter, sort, paginate** — full problem log with search-by-title and filters for company/difficulty/topic
- **Company-wise view** — filter your log per company with a difficulty breakdown and top topics
- **Practice + judge** — write Python in an in-browser editor, run it, and submit for automatic grading against test cases (see Practice section below)
- **Progress charts** — 30-day trend, difficulty split, company split (Chart.js, bundled locally)
- **Daily streak** — current streak, longest streak, and a GitHub-style contribution heatmap
- **Weekly goal** — set a weekly target, dashboard shows a live progress bar
- **Interview countdown** — set a target interview date, see days remaining on the dashboard and profile
- **Profile page** — name, email, totals, streaks, settings
- **CSV export** — download your full problem log as a spreadsheet-ready CSV
- **Dark / light toggle** — persisted per-browser via localStorage
- **Notes** — freeform notes, optionally linked to a specific problem, with inline editing
- **Logging** — every action (register, login, add/edit/delete, submissions) logs to console + `preptrack.log`

## Tech stack

Python · Flask · MySQL (PyMySQL) · Jinja2 · vanilla CSS/JS · Chart.js

## Project structure

```
PrepTrack/
├── app.py                 # routes, auth, streak logic, JSON API
├── config.py               # env-based configuration
├── schema.sql               # MySQL schema + seed companies
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html            # sidebar app shell
│   ├── login.html / register.html
│   ├── dashboard.html
│   ├── company.html
│   ├── add_problem.html
│   └── notes.html
└── static/
    ├── css/style.css        # design system (dark, amber/teal accents)
    └── js/
        ├── charts.js         # dashboard charts + heatmap
        └── company_chart.js
```

## Setup

1. **Create the database**

   ```bash
   mysql -u root -p < schema.sql
   ```

   If you already have an existing PrepTrack database from before, instead run the
   two migration files to add the new tables/columns without losing your data:

   ```bash
   mysql -u root -p preptrack < feature_schema.sql
   mysql -u root -p preptrack < practice_schema.sql
   ```

2. **Install dependencies** (a virtualenv is recommended)

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables** — copy `.env.example` to `.env` and
   fill in your MySQL credentials, or export the same variables directly:

   ```bash
   cp .env.example .env
   ```

   If you use `python-dotenv`, add `from dotenv import load_dotenv; load_dotenv()`
   near the top of `app.py`, or export the variables in your shell before running.

4. **Run the app**

   ```bash
   python app.py
   ```

   Visit `http://127.0.0.1:5000`, register an account, and start logging problems.

## Notes on the design

The UI leans into the subject matter — a commit-log / terminal aesthetic
(dark canvas, monospace stat numbers, a GitHub-style streak heatmap) rather
than a generic light dashboard, since the audience is students already
comfortable in that visual language from LeetCode/GitHub. Amber marks the
streak and "in-progress" state; teal marks completion and easy problems;
rose marks hard problems — used consistently across charts, tags, and stats
so the color coding is legible at a glance across every page.

## Practice / judge feature — how it works

- Problems live in `practice_problems` + `practice_test_cases` (stdin/stdout judged).
- The in-browser editor (CodeMirror, bundled locally, no CDN) posts code to
  `/api/practice/<id>/run` for a quick sanity check, or `/api/practice/<id>/submit`
  to be graded against every test case for that problem.
- `judge.py` runs submitted code as a plain Python subprocess with a 5-second
  timeout. **This is not a real sandbox** — submitted code has the same
  filesystem/network access as the Flask process. Fine for practicing on your
  own machine; do **not** deploy this publicly or for multiple untrusted users
  without adding real isolation (Docker per run, a restricted OS user,
  seccomp/gVisor, or a hosted judge API like Judge0).
- Add more problems by inserting rows into `practice_problems` and
  `practice_test_cases` — see `practice_schema.sql` for the pattern.

## Extending it further

- Password reset + email verification (needs an SMTP/email provider — a genuinely separate integration)
- More languages in the judge (currently Python only)
- Admin/teacher role with a batch-wide leaderboard
- PDF export alongside CSV
