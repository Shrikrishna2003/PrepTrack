
# 🚀 PrepTrack

<p align="center">
  <a href="https://preptrack.up.railway.app">
    <img src="https://img.shields.io/badge/🚀_Live_Demo-00C853?style=for-the-badge&logo=railway&logoColor=white"/>
  </a>

  <a href="https://github.com/Shrikrishna2003/PrepTrack">
    <img src="https://img.shields.io/badge/📂_GitHub-181717?style=for-the-badge&logo=github&logoColor=white"/>
  </a>

  <img src="https://img.shields.io/badge/Python-Flask-blue?style=for-the-badge&logo=python"/>
  <img src="https://img.shields.io/badge/Database-MySQL-orange?style=for-the-badge&logo=mysql"/>
</p>

<p align="center">
  <b>Full-Stack Coding Interview Preparation Platform</b><br>
  Track coding progress, maintain streaks, practice interview problems, and analyze preparation through an interactive dashboard.
</p>

PrepTrack is a full-stack coding interview preparation platform built with **Flask** and **MySQL** that helps students organize coding practice, monitor progress, prepare company-wise interview questions, and visualize performance through an interactive analytics dashboard.

---

## ✨ Features

- 🔐 **Authentication** — Register, Login, and Logout with secure password hashing (Werkzeug).
- 📝 **Problem Log** — Add, edit, and delete coding problems with company, topic, difficulty, platform, link, status, date, and time taken.
- 🔍 **Search, Filter & Sort** — Quickly find problems using title search, company, difficulty, and topic filters.
- 🏢 **Company Analytics** — Track preparation for companies like TCS, Infosys, and Atidan with topic and difficulty breakdowns.
- 💻 **Practice & Code Judge** — Solve Python coding problems in an in-browser editor and receive automatic grading.
- 📊 **Progress Dashboard** — View a 30-day trend, company-wise statistics, and difficulty distribution using Chart.js.
- 🔥 **Daily Streak** — Maintain current and longest coding streaks with a GitHub-style contribution heatmap.
- 🎯 **Weekly Goals** — Set weekly targets and monitor progress with a live progress bar.
- ⏳ **Interview Countdown** — Set a target interview date and track remaining days.
- 👤 **Profile Management** — Manage personal information, goals, and interview settings.
- 📝 **Notes** — Create personal notes linked to coding problems.
- 📤 **CSV Export** — Download your complete coding history as a CSV.
- 🌗 **Dark / Light Mode** — Theme preference persists using localStorage.
- ☁️ **Cloud Deployment** — Deployed on **Railway** with automatic **GitHub CI/CD** deployments.
- 📋 **Logging** — Every major user action is logged to both the console and `preptrack.log`.

---

## 🛠 Tech Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,flask,mysql,html,css,js,git,github,vscode"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Jinja2-Template_Engine-red?style=flat-square"/>
  <img src="https://img.shields.io/badge/Chart.js-Analytics-FF6384?style=flat-square"/>
  <img src="https://img.shields.io/badge/Railway-Deployed-purple?style=flat-square"/>
</p>

---

## 🏗 Architecture

```text
Browser
   │
   ▼
Flask (Gunicorn)
   │
   ├── Authentication
   ├── Dashboard
   ├── Notes
   ├── Practice Judge
   └── Analytics API
   │
   ▼
Railway MySQL
```

---

## 📂 Project Structure

```text
PrepTrack/
├── app.py                  # Routes, authentication, dashboard, APIs
├── config.py               # Environment-based configuration
├── schema.sql              # MySQL schema + seed companies
├── feature_schema.sql      # Database migration
├── practice_schema.sql     # Practice module schema
├── judge.py                # Python code execution & judging
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── company.html
│   ├── add_problem.html
│   └── notes.html
└── static/
    ├── css/style.css
    └── js/
        ├── charts.js
        └── company_chart.js
```

---

## 📸 Screenshots

| Dashboard | Practice |
|-----------|----------|
| ![Dashboard](Screenshots/Dashboard.png) | ![Practice](Screenshots/practice.png) |

| Company Analytics | All Problems |
|-------------------|--------------|
| ![Company](Screenshots/company-analytics.png) | ![Problems](Screenshots/all-problems.png) |

| Notes | Profile |
|--------|---------|
| ![Notes](Screenshots/notes.png) | ![Profile](Screenshots/profile-page.png) |

| Login | Log a Problem |
|--------|---------------|
| ![Login](Screenshots/login-page.png) | ![Log Problem](Screenshots/Log-problem.png) |

---

## 🌐 Live Demo

**🚀 Website:** `https://preptrack.up.railway.app`

### Demo Access

- Register a new account
- Or log in using your own account

> Hosted on Railway with MySQL and automatic GitHub deployments.

---

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Shrikrishna2003/PrepTrack.git
cd PrepTrack
```

### 2. Create the database

```bash
mysql -u root -p < schema.sql
```

If you already have an existing PrepTrack database, run the migration files instead:

```bash
mysql -u root -p preptrack < feature_schema.sql
mysql -u root -p preptrack < practice_schema.sql
```

### 3. Install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`.

```bash
cp .env.example .env
```

Add your database credentials:

```env
SECRET_KEY=your-secret-key
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DB=preptrack
```

### 5. Run the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Register an account and start tracking your coding preparation.

---

## 🎨 Design Philosophy

PrepTrack follows a **terminal-inspired UI** with a dark theme, GitHub-style contribution heatmap, and consistent color coding.

- 🟨 **Amber** — Streaks and in-progress work
- 🟩 **Teal** — Completed work and easy problems
- 🌹 **Rose** — Hard problems

The design focuses on readability for students already familiar with GitHub and LeetCode.

---

## 💻 Practice & Judge

- Problems are stored in `practice_problems` and `practice_test_cases`.
- CodeMirror powers the in-browser editor.
- `/api/practice/<id>/run` executes sample runs.
- `/api/practice/<id>/submit` grades submissions against all test cases.
- `judge.py` executes Python code with a **5-second timeout**.

### Security Note

The current implementation is designed for personal practice and is **not a production sandbox**. Multi-user deployments should use proper isolation such as Docker, gVisor, seccomp, or Judge0.

---

## 🚀 Future Improvements

- Password reset
- Email verification
- Multi-language code execution
- Admin/Teacher dashboard
- Batch-wise leaderboard
- PDF export
- Enhanced analytics

---

## 👨‍💻 Developer

**Shrikrishna Mokhashi**

- GitHub: https://github.com/Shrikrishna2003
- Live Demo: https://preptrack.up.railway.app
