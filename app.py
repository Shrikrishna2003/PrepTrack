import datetime
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from judge import run_code, judge_submission

app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------------------------------------------------------
# Logging setup — prints to the terminal AND writes to preptrack.log
# ---------------------------------------------------------------------------

log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

file_handler = RotatingFileHandler("preptrack.log", maxBytes=1_000_000, backupCount=3)
file_handler.setFormatter(log_formatter)

app.logger.setLevel(logging.INFO)
app.logger.handlers.clear()
app.logger.addHandler(console_handler)
app.logger.addHandler(file_handler)
app.logger.propagate = False
# quiet down Flask's default request logger duplicate noise
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app.logger.info("PrepTrack starting up")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    try:
        return pymysql.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DB"],
            port=app.config["MYSQL_PORT"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    except pymysql.err.OperationalError as e:
        app.logger.error("Database connection failed: %s", e)
        raise


def query(sql, params=None, fetch="all"):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            if fetch == "id":
                return cur.lastrowid
            return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user_id():
    return session.get("user_id")


# ---------------------------------------------------------------------------
# Streak calculation
# ---------------------------------------------------------------------------

def compute_streak(user_id):
    rows = query(
        "SELECT DISTINCT solved_date FROM problems WHERE user_id=%s ORDER BY solved_date DESC",
        (user_id,),
    )
    dates = {r["solved_date"] for r in rows}
    if not dates:
        return 0, 0, []

    today = datetime.date.today()
    current = 0
    cursor_date = today if today in dates else today - datetime.timedelta(days=1)
    while cursor_date in dates:
        current += 1
        cursor_date -= datetime.timedelta(days=1)

    longest = 0
    run = 0
    prev = None
    for d in sorted(dates):
        if prev is not None and (d - prev).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = d

    return current, longest, sorted(dates)


def heatmap_data(user_id, days=182):
    rows = query(
        """SELECT solved_date, COUNT(*) AS cnt
           FROM problems WHERE user_id=%s
           GROUP BY solved_date""",
        (user_id,),
    )
    counts = {r["solved_date"].isoformat(): r["cnt"] for r in rows}
    today = datetime.date.today()
    result = []
    for i in range(days - 1, -1, -1):
        d = today - datetime.timedelta(days=i)
        result.append({"date": d.isoformat(), "count": counts.get(d.isoformat(), 0)})
    return result


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        existing = query("SELECT id FROM users WHERE email=%s", (email,), fetch="one")
        if existing:
            flash("An account with that email already exists.", "error")
            return redirect(url_for("register"))

        pw_hash = generate_password_hash(password)
        user_id = query(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, pw_hash),
            fetch="id",
        )
        session["user_id"] = user_id
        session["user_name"] = name
        app.logger.info("New user registered: %s (id=%s)", email, user_id)
        flash("Account created. Let's get you prepping.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query("SELECT * FROM users WHERE email=%s", (email,), fetch="one")
        if not user or not check_password_hash(user["password_hash"], password):
            app.logger.warning("Failed login attempt for: %s", email)
            flash("Incorrect email or password.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        app.logger.info("User logged in: %s (id=%s)", email, user["id"])
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    app.logger.info("User logged out: id=%s", session.get("user_id"))
    session.clear()
    flash("Signed out. See you tomorrow for the streak.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if current_user_id():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    uid = current_user_id()

    total_solved = query(
        "SELECT COUNT(*) AS c FROM problems WHERE user_id=%s AND status='Solved'",
        (uid,), fetch="one",
    )["c"]

    by_difficulty = query(
        """SELECT difficulty, COUNT(*) AS c FROM problems
           WHERE user_id=%s GROUP BY difficulty""",
        (uid,),
    )

    by_company = query(
        """SELECT c.name AS company, COUNT(p.id) AS c
           FROM companies c LEFT JOIN problems p
             ON p.company_id = c.id AND p.user_id=%s
           GROUP BY c.id, c.name ORDER BY c.name""",
        (uid,),
    )

    last_30 = query(
        """SELECT solved_date, COUNT(*) AS c FROM problems
           WHERE user_id=%s AND solved_date >= %s
           GROUP BY solved_date ORDER BY solved_date""",
        (uid, datetime.date.today() - datetime.timedelta(days=29)),
    )

    recent = query(
        """SELECT p.*, c.name AS company_name FROM problems p
           JOIN companies c ON c.id = p.company_id
           WHERE p.user_id=%s ORDER BY p.solved_date DESC, p.id DESC LIMIT 6""",
        (uid,),
    )

    current_streak, longest_streak, _ = compute_streak(uid)
    heatmap = heatmap_data(uid)

    user = query("SELECT weekly_goal, interview_date FROM users WHERE id=%s", (uid,), fetch="one")
    week_start = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
    this_week_count = query(
        "SELECT COUNT(*) AS c FROM problems WHERE user_id=%s AND solved_date >= %s",
        (uid, week_start), fetch="one",
    )["c"]
    weekly_goal = user["weekly_goal"] or 20
    goal_pct = min(100, round(100 * this_week_count / weekly_goal)) if weekly_goal else 0

    days_to_interview = None
    if user["interview_date"]:
        days_to_interview = (user["interview_date"] - datetime.date.today()).days

    return render_template(
        "dashboard.html",
        total_solved=total_solved,
        by_difficulty=by_difficulty,
        by_company=by_company,
        last_30=last_30,
        recent=recent,
        current_streak=current_streak,
        longest_streak=longest_streak,
        heatmap=heatmap,
        weekly_goal=weekly_goal,
        this_week_count=this_week_count,
        goal_pct=goal_pct,
        days_to_interview=days_to_interview,
    )


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------

@app.route("/problems/add", methods=["GET", "POST"])
@login_required
def add_problem():
    companies = query("SELECT * FROM companies ORDER BY name")

    if request.method == "POST":
        uid = current_user_id()
        title = request.form.get("title", "").strip()
        company_id = request.form.get("company_id")
        topic = request.form.get("topic", "").strip()
        difficulty = request.form.get("difficulty", "Medium")
        platform = request.form.get("platform", "").strip()
        link = request.form.get("problem_link", "").strip()
        status = request.form.get("status", "Solved")
        solved_date = request.form.get("solved_date") or datetime.date.today().isoformat()
        time_taken = request.form.get("time_taken_min") or None

        if not title or not company_id:
            flash("Problem title and company are required.", "error")
            return redirect(url_for("add_problem"))

        query(
            """INSERT INTO problems
               (user_id, title, company_id, topic, difficulty, platform,
                problem_link, status, solved_date, time_taken_min)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (uid, title, company_id, topic, difficulty, platform,
             link, status, solved_date, time_taken),
            fetch=None,
        )
        app.logger.info("Problem added by user %s: '%s' (%s)", uid, title, difficulty)
        flash(f'"{title}" logged. Nice work.', "success")
        return redirect(url_for("dashboard"))

    prefill = {
        "title": request.args.get("title", ""),
        "topic": request.args.get("topic", ""),
        "difficulty": request.args.get("difficulty", "Medium"),
    }

    return render_template("add_problem.html", companies=companies,
                            today=datetime.date.today().isoformat(),
                            prefill=prefill)


@app.route("/problems/<int:problem_id>/delete", methods=["POST"])
@login_required
def delete_problem(problem_id):
    query("DELETE FROM problems WHERE id=%s AND user_id=%s",
          (problem_id, current_user_id()), fetch=None)
    app.logger.info("Problem deleted by user %s: id=%s", current_user_id(), problem_id)
    flash("Entry removed.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/problems/<int:problem_id>/edit", methods=["GET", "POST"])
@login_required
def edit_problem(problem_id):
    uid = current_user_id()
    companies = query("SELECT * FROM companies ORDER BY name")

    problem = query(
        "SELECT * FROM problems WHERE id=%s AND user_id=%s",
        (problem_id, uid), fetch="one",
    )
    if not problem:
        flash("That entry doesn't exist.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company_id = request.form.get("company_id")
        topic = request.form.get("topic", "").strip()
        difficulty = request.form.get("difficulty", "Medium")
        platform = request.form.get("platform", "").strip()
        link = request.form.get("problem_link", "").strip()
        status = request.form.get("status", "Solved")
        solved_date = request.form.get("solved_date") or datetime.date.today().isoformat()
        time_taken = request.form.get("time_taken_min") or None

        if not title or not company_id:
            flash("Problem title and company are required.", "error")
            return redirect(url_for("edit_problem", problem_id=problem_id))

        query(
            """UPDATE problems SET
                 title=%s, company_id=%s, topic=%s, difficulty=%s, platform=%s,
                 problem_link=%s, status=%s, solved_date=%s, time_taken_min=%s
               WHERE id=%s AND user_id=%s""",
            (title, company_id, topic, difficulty, platform, link, status,
             solved_date, time_taken, problem_id, uid),
            fetch=None,
        )
        app.logger.info("Problem edited by user %s: id=%s ('%s')", uid, problem_id, title)
        flash(f'"{title}" updated.', "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "edit_problem.html", companies=companies, problem=problem,
        solved_date=problem["solved_date"].isoformat(),
    )


@app.route("/company/<company_name>")
@login_required
def company_view(company_name):
    uid = current_user_id()
    company = query("SELECT * FROM companies WHERE name=%s", (company_name,), fetch="one")
    if not company:
        flash("Unknown company.", "error")
        return redirect(url_for("dashboard"))

    problems = query(
        """SELECT p.* FROM problems p
           WHERE p.user_id=%s AND p.company_id=%s
           ORDER BY p.solved_date DESC""",
        (uid, company["id"]),
    )

    by_difficulty = query(
        """SELECT difficulty, COUNT(*) AS c FROM problems
           WHERE user_id=%s AND company_id=%s GROUP BY difficulty""",
        (uid, company["id"]),
    )

    by_topic = query(
        """SELECT COALESCE(NULLIF(topic,''),'Uncategorized') AS topic, COUNT(*) AS c
           FROM problems WHERE user_id=%s AND company_id=%s
           GROUP BY topic ORDER BY c DESC LIMIT 8""",
        (uid, company["id"]),
    )

    companies = query("SELECT * FROM companies ORDER BY name")

    return render_template(
        "company.html",
        company=company,
        problems=problems,
        by_difficulty=by_difficulty,
        by_topic=by_topic,
        companies=companies,
    )


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

SORT_COLUMNS = {
    "date": "p.solved_date",
    "title": "p.title",
    "difficulty": "FIELD(p.difficulty,'Easy','Medium','Hard')",
    "company": "c.name",
}
PAGE_SIZE = 10


@app.route("/problems")
@login_required
def problems_list():
    uid = current_user_id()

    search = request.args.get("q", "").strip()
    company_filter = request.args.get("company", "").strip()
    difficulty_filter = request.args.get("difficulty", "").strip()
    topic_filter = request.args.get("topic", "").strip()
    sort_key = request.args.get("sort", "date")
    direction = request.args.get("dir", "desc")
    page = max(1, request.args.get("page", 1, type=int))

    where = ["p.user_id=%s"]
    params = [uid]

    if search:
        where.append("p.title LIKE %s")
        params.append(f"%{search}%")
    if company_filter:
        where.append("c.name=%s")
        params.append(company_filter)
    if difficulty_filter:
        where.append("p.difficulty=%s")
        params.append(difficulty_filter)
    if topic_filter:
        where.append("p.topic=%s")
        params.append(topic_filter)

    where_sql = " AND ".join(where)
    sort_col = SORT_COLUMNS.get(sort_key, SORT_COLUMNS["date"])
    dir_sql = "ASC" if direction == "asc" else "DESC"

    total = query(
        f"""SELECT COUNT(*) AS c FROM problems p
            JOIN companies c ON c.id = p.company_id
            WHERE {where_sql}""",
        tuple(params), fetch="one",
    )["c"]

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE

    problems = query(
        f"""SELECT p.*, c.name AS company_name FROM problems p
            JOIN companies c ON c.id = p.company_id
            WHERE {where_sql}
            ORDER BY {sort_col} {dir_sql}
            LIMIT %s OFFSET %s""",
        tuple(params) + (PAGE_SIZE, offset),
    )

    companies = query("SELECT * FROM companies ORDER BY name")
    topics = query(
        """SELECT DISTINCT topic FROM problems
           WHERE user_id=%s AND topic IS NOT NULL AND topic != ''
           ORDER BY topic""",
        (uid,),
    )

    return render_template(
        "problems_list.html",
        problems=problems, companies=companies, topics=topics,
        search=search, company_filter=company_filter,
        difficulty_filter=difficulty_filter, topic_filter=topic_filter,
        sort_key=sort_key, direction=direction,
        page=page, total_pages=total_pages, total=total,
    )


@app.route("/export/csv")
@login_required
def export_csv():
    import csv
    import io

    uid = current_user_id()
    problems = query(
        """SELECT p.title, c.name AS company, p.topic, p.difficulty, p.platform,
                  p.problem_link, p.status, p.solved_date, p.time_taken_min
           FROM problems p JOIN companies c ON c.id = p.company_id
           WHERE p.user_id=%s ORDER BY p.solved_date DESC""",
        (uid,),
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Title", "Company", "Topic", "Difficulty", "Platform",
                      "Link", "Status", "Solved Date", "Time Taken (min)"])
    for p in problems:
        writer.writerow([p["title"], p["company"], p["topic"], p["difficulty"],
                          p["platform"], p["problem_link"], p["status"],
                          p["solved_date"], p["time_taken_min"]])

    app.logger.info("CSV export by user %s: %s rows", uid, len(problems))

    from flask import Response
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=preptrack_problems.csv"},
    )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    uid = current_user_id()

    if request.method == "POST":
        weekly_goal = request.form.get("weekly_goal", "20")
        interview_date = request.form.get("interview_date") or None
        try:
            weekly_goal = max(1, int(weekly_goal))
        except ValueError:
            weekly_goal = 20

        query(
            "UPDATE users SET weekly_goal=%s, interview_date=%s WHERE id=%s",
            (weekly_goal, interview_date, uid),
            fetch=None,
        )
        app.logger.info("Profile updated by user %s: goal=%s, interview_date=%s",
                         uid, weekly_goal, interview_date)
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    user = query("SELECT * FROM users WHERE id=%s", (uid,), fetch="one")
    total_solved = query(
        "SELECT COUNT(*) AS c FROM problems WHERE user_id=%s AND status='Solved'",
        (uid,), fetch="one",
    )["c"]
    current_streak, longest_streak, _ = compute_streak(uid)

    days_to_interview = None
    if user["interview_date"]:
        days_to_interview = (user["interview_date"] - datetime.date.today()).days

    return render_template(
        "profile.html", user=user, total_solved=total_solved,
        current_streak=current_streak, longest_streak=longest_streak,
        days_to_interview=days_to_interview,
    )


@app.route("/notes")
@login_required
def notes():
    uid = current_user_id()
    all_notes = query(
        """SELECT n.*, p.title AS problem_title FROM notes n
           LEFT JOIN problems p ON p.id = n.problem_id
           WHERE n.user_id=%s ORDER BY n.updated_at DESC""",
        (uid,),
    )
    problems = query(
        "SELECT id, title FROM problems WHERE user_id=%s ORDER BY solved_date DESC",
        (uid,),
    )
    return render_template("notes.html", notes=all_notes, problems=problems)


@app.route("/notes/add", methods=["POST"])
@login_required
def add_note():
    uid = current_user_id()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    problem_id = request.form.get("problem_id") or None

    if not title:
        flash("Give your note a title.", "error")
        return redirect(url_for("notes"))

    query(
        "INSERT INTO notes (user_id, problem_id, title, content) VALUES (%s,%s,%s,%s)",
        (uid, problem_id, title, content),
        fetch=None,
    )
    app.logger.info("Note added by user %s: '%s'", uid, title)
    flash("Note saved.", "success")
    return redirect(url_for("notes"))


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    query("DELETE FROM notes WHERE id=%s AND user_id=%s",
          (note_id, current_user_id()), fetch=None)
    app.logger.info("Note deleted by user %s: id=%s", current_user_id(), note_id)
    flash("Note deleted.", "success")
    return redirect(url_for("notes"))


@app.route("/notes/<int:note_id>/edit", methods=["POST"])
@login_required
def edit_note(note_id):
    uid = current_user_id()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    problem_id = request.form.get("problem_id") or None

    if not title:
        flash("Give your note a title.", "error")
        return redirect(url_for("notes"))

    query(
        "UPDATE notes SET title=%s, content=%s, problem_id=%s WHERE id=%s AND user_id=%s",
        (title, content, problem_id, note_id, uid),
        fetch=None,
    )
    app.logger.info("Note edited by user %s: id=%s", uid, note_id)
    flash("Note updated.", "success")
    return redirect(url_for("notes"))


# ---------------------------------------------------------------------------
# JSON API (for Chart.js)
# ---------------------------------------------------------------------------

@app.route("/api/stats")
@login_required
def api_stats():
    uid = current_user_id()

    last_30 = query(
        """SELECT solved_date, COUNT(*) AS c FROM problems
           WHERE user_id=%s AND solved_date >= %s
           GROUP BY solved_date ORDER BY solved_date""",
        (uid, datetime.date.today() - datetime.timedelta(days=29)),
    )
    by_difficulty = query(
        "SELECT difficulty, COUNT(*) AS c FROM problems WHERE user_id=%s GROUP BY difficulty",
        (uid,),
    )
    by_company = query(
        """SELECT co.name AS company, COUNT(p.id) AS c
           FROM companies co LEFT JOIN problems p
             ON p.company_id = co.id AND p.user_id=%s
           GROUP BY co.id, co.name ORDER BY co.name""",
        (uid,),
    )

    return jsonify({
        "last_30": [{"date": r["solved_date"].isoformat(), "count": r["c"]} for r in last_30],
        "by_difficulty": {r["difficulty"]: r["c"] for r in by_difficulty},
        "by_company": {r["company"]: r["c"] for r in by_company},
    })


# ---------------------------------------------------------------------------
# Practice — code editor + judge
# ---------------------------------------------------------------------------

@app.route("/practice")
@login_required
def practice_list():
    uid = current_user_id()

    problems = query(
        """SELECT p.*, c.name AS company_name,
                  (SELECT s.status FROM submissions s
                   WHERE s.user_id=%s AND s.problem_id=p.id
                   ORDER BY (s.status='Accepted') DESC, s.submitted_at DESC LIMIT 1) AS best_status
           FROM practice_problems p
           LEFT JOIN companies c ON c.id = p.company_id
           ORDER BY FIELD(p.difficulty,'Easy','Medium','Hard'), p.title""",
        (uid,),
    )
    return render_template("practice_list.html", problems=problems)


@app.route("/practice/<slug>")
@login_required
def practice_solve(slug):
    uid = current_user_id()

    problem = query(
        """SELECT p.*, c.name AS company_name FROM practice_problems p
           LEFT JOIN companies c ON c.id = p.company_id
           WHERE p.slug=%s""",
        (slug,), fetch="one",
    )
    if not problem:
        flash("That problem doesn't exist.", "error")
        return redirect(url_for("practice_list"))

    samples = query(
        "SELECT * FROM practice_test_cases WHERE problem_id=%s AND is_sample=TRUE",
        (problem["id"],),
    )

    last_submission = query(
        """SELECT * FROM submissions WHERE user_id=%s AND problem_id=%s
           ORDER BY submitted_at DESC LIMIT 1""",
        (uid, problem["id"]), fetch="one",
    )
    starting_code = last_submission["code"] if last_submission else problem["starter_code"]

    return render_template(
        "practice_solve.html",
        problem=problem,
        samples=samples,
        starting_code=starting_code,
        last_submission=last_submission,
    )


@app.route("/api/practice/<int:problem_id>/run", methods=["POST"])
@login_required
def api_practice_run(problem_id):
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    stdin_data = data.get("stdin", "")

    if not code.strip():
        return jsonify({"error": "No code submitted."}), 400

    result = run_code(code, stdin_data)
    return jsonify(result)


@app.route("/api/practice/<int:problem_id>/submit", methods=["POST"])
@login_required
def api_practice_submit(problem_id):
    uid = current_user_id()
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "No code submitted."}), 400

    problem = query("SELECT * FROM practice_problems WHERE id=%s", (problem_id,), fetch="one")
    if not problem:
        return jsonify({"error": "Problem not found."}), 404

    test_cases = query(
        "SELECT input, expected_output, is_sample FROM practice_test_cases WHERE problem_id=%s",
        (problem_id,),
    )
    if not test_cases:
        return jsonify({"error": "This problem has no test cases configured yet."}), 400

    verdict = judge_submission(code, test_cases)

    query(
        """INSERT INTO submissions (user_id, problem_id, code, status, passed_count, total_count)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        (uid, problem_id, code, verdict["status"], verdict["passed"], verdict["total"]),
        fetch=None,
    )
    app.logger.info(
        "Submission by user %s for '%s': %s (%s/%s)",
        uid, problem["title"], verdict["status"], verdict["passed"], verdict["total"],
    )

    verdict["problem_title"] = problem["title"]
    verdict["problem_topic"] = problem["topic"]
    verdict["problem_difficulty"] = problem["difficulty"]
    return jsonify(verdict)


if __name__ == "__main__":
    app.run(debug=True)
