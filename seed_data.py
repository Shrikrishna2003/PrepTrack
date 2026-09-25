"""
seed_data.py — populate PrepTrack with sample problems for TCS, Infosys and
Atidan so the dashboard, charts and streak heatmap have real data to show.

Usage:
    python seed_data.py your@email.com

If the email doesn't exist yet, a demo account is created for you:
    email:    (whatever you pass in, or demo@preptrack.local if omitted)
    password: preptrack123
"""

import sys
import datetime
import logging

import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("seed")


def get_db():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        port=Config.MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


# 10 sample problems spread across TCS, Infosys and Atidan, with dates
# staggered over the last 9 days so the streak + heatmap look alive.
SAMPLE_PROBLEMS = [
    {"title": "Reverse a Linked List", "company": "TCS", "topic": "Linked List",
     "difficulty": "Easy", "platform": "GeeksforGeeks", "status": "Solved",
     "days_ago": 8, "time_taken_min": 15},
    {"title": "Longest Common Subsequence", "company": "TCS", "topic": "DP",
     "difficulty": "Medium", "platform": "LeetCode", "status": "Solved",
     "days_ago": 7, "time_taken_min": 35},
    {"title": "Detect Cycle in a Graph", "company": "TCS", "topic": "Graphs",
     "difficulty": "Hard", "platform": "LeetCode", "status": "Revisit",
     "days_ago": 6, "time_taken_min": 50},
    {"title": "Two Sum", "company": "Infosys", "topic": "Arrays",
     "difficulty": "Easy", "platform": "LeetCode", "status": "Solved",
     "days_ago": 6, "time_taken_min": 10},
    {"title": "Merge Intervals", "company": "Infosys", "topic": "Arrays",
     "difficulty": "Medium", "platform": "LeetCode", "status": "Solved",
     "days_ago": 5, "time_taken_min": 25},
    {"title": "Word Break", "company": "Infosys", "topic": "DP",
     "difficulty": "Hard", "platform": "LeetCode", "status": "Attempted",
     "days_ago": 4, "time_taken_min": 45},
    {"title": "Valid Parentheses", "company": "Infosys", "topic": "Stack",
     "difficulty": "Easy", "platform": "HackerRank", "status": "Solved",
     "days_ago": 3, "time_taken_min": 8},
    {"title": "Binary Search on Rotated Array", "company": "Atidan", "topic": "Binary Search",
     "difficulty": "Medium", "platform": "LeetCode", "status": "Solved",
     "days_ago": 2, "time_taken_min": 20},
    {"title": "Lowest Common Ancestor of a BST", "company": "Atidan", "topic": "Trees",
     "difficulty": "Medium", "platform": "GeeksforGeeks", "status": "Solved",
     "days_ago": 1, "time_taken_min": 18},
    {"title": "Implement LRU Cache", "company": "Atidan", "topic": "Design",
     "difficulty": "Hard", "platform": "LeetCode", "status": "Solved",
     "days_ago": 0, "time_taken_min": 40},
]


def get_or_create_user(conn, email, name="Demo User", password="preptrack123"):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        if user:
            log.info("Using existing user: %s (id=%s)", email, user["id"])
            return user["id"]

        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s,%s,%s)",
            (name, email, generate_password_hash(password)),
        )
        user_id = cur.lastrowid
        log.info("Created demo user: %s / password: %s (id=%s)", email, password, user_id)
        return user_id


def get_company_ids(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM companies")
        return {row["name"]: row["id"] for row in cur.fetchall()}


def seed(email):
    conn = get_db()
    try:
        user_id = get_or_create_user(conn, email)
        companies = get_company_ids(conn)
        today = datetime.date.today()

        with conn.cursor() as cur:
            # skip problems that already exist for this user (avoid duplicates on re-run)
            cur.execute("SELECT title FROM problems WHERE user_id=%s", (user_id,))
            existing_titles = {row["title"] for row in cur.fetchall()}

            inserted = 0
            for p in SAMPLE_PROBLEMS:
                if p["title"] in existing_titles:
                    log.info("Skipping (already exists): %s", p["title"])
                    continue

                company_id = companies.get(p["company"])
                if not company_id:
                    log.warning("Unknown company '%s', skipping '%s'", p["company"], p["title"])
                    continue

                solved_date = today - datetime.timedelta(days=p["days_ago"])
                cur.execute(
                    """INSERT INTO problems
                       (user_id, title, company_id, topic, difficulty, platform,
                        problem_link, status, solved_date, time_taken_min)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (user_id, p["title"], company_id, p["topic"], p["difficulty"],
                     p["platform"], "", p["status"], solved_date, p["time_taken_min"]),
                )
                inserted += 1
                log.info(
                    "Added [%s] %-32s %-8s %-6s solved %s",
                    p["company"], p["title"], p["topic"], p["difficulty"], solved_date,
                )

        log.info("Done. %s new problem(s) added for user_id=%s.", inserted, user_id)
        log.info("Log in as %s (password: preptrack123 if this account was just created) "
                  "and open the dashboard to see the charts and streak fill in.", email)
    finally:
        conn.close()


if __name__ == "__main__":
    target_email = sys.argv[1] if len(sys.argv) > 1 else "demo@preptrack.local"
    seed(target_email)
