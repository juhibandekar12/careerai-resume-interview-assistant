"""
scripts/seed_db.py
-------------------
Seeds the database with:
  - A demo user (username: demo / password: demo123)
  - All 25 job roles loaded from data/job_roles.json
Run once after setting up the project:
    python scripts/seed_db.py
"""

import sys
import os
import json
import logging

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, execute, fetchone, to_json
from utils.auth import hash_password

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


# ── 1. Initialise database schema ─────────────────────────────────────────────
logger.info("Initialising database…")
init_db()


# ── 2. Seed demo user ──────────────────────────────────────────────────────────
DEMO_USERNAME = "demo"
DEMO_EMAIL    = "demo@careerai.com"
DEMO_PASSWORD = "demo123"
DEMO_NAME     = "Demo User"

existing = fetchone("SELECT id FROM users WHERE username=?", (DEMO_USERNAME,))
if existing:
    logger.info("Demo user already exists (id=%s). Skipping.", existing["id"])
else:
    uid = execute(
        "INSERT INTO users (username, email, password_hash, full_name) VALUES (?,?,?,?)",
        (DEMO_USERNAME, DEMO_EMAIL, hash_password(DEMO_PASSWORD), DEMO_NAME),
    )
    logger.info("✅ Demo user created  id=%s  username=%s  password=%s", uid, DEMO_USERNAME, DEMO_PASSWORD)


# ── 3. Seed job roles ──────────────────────────────────────────────────────────
DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "job_roles.json"
)

if not os.path.exists(DATA_PATH):
    logger.error("job_roles.json not found at %s", DATA_PATH)
    sys.exit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    jobs = json.load(f)

inserted = 0
skipped  = 0
for job in jobs:
    exists = fetchone("SELECT id FROM job_roles WHERE title=?", (job["title"],))
    if exists:
        skipped += 1
        continue
    execute(
        """INSERT INTO job_roles
           (title, category, required_skills, description, avg_salary, experience_level)
           VALUES (?,?,?,?,?,?)""",
        (
            job["title"],
            job.get("category", ""),
            to_json(job.get("required_skills", [])),
            job.get("description", ""),
            job.get("avg_salary", ""),
            job.get("experience_level", ""),
        ),
    )
    inserted += 1

logger.info("✅ Job roles: %d inserted, %d already existed.", inserted, skipped)
logger.info("🎉 Database seeded successfully!")
print("\n" + "="*50)
print("  Seed complete. You can now start the application.")
print("  Demo login → username: demo | password: demo123")
print("="*50)
