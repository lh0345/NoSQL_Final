import json
import sqlite3
import ast
import os

# Resolve project-relative data directory (scripts/ -> ../data)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "yelp_rel.db")
BUSINESS_FILE = os.path.join(DATA_DIR, "business.json")
REVIEW_FILE = os.path.join(DATA_DIR, "review.json")   # if you have it; otherwise skip reviews for now

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ---- Helper to parse attributes ----
def parse_attributes(attrs):
    if isinstance(attrs, dict):
        return attrs
    if isinstance(attrs, str):
        try:
            return ast.literal_eval(attrs)
        except:
            return {}
    return {}

# ---- 1. Load businesses ----
with open(BUSINESS_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        biz = json.loads(line)
        # Insert business
        cur.execute(
            "INSERT OR IGNORE INTO business VALUES (?,?,?,?,?,?,?)",
            (biz["business_id"], biz["name"], biz.get("city"), biz.get("state"),
             biz.get("stars", 0), biz.get("review_count", 0), biz.get("is_open", 1))
        )
        # Insert categories (comma-separated string in original JSON)
        cats = biz.get("categories", "")
        if cats:
            for cat in cats.split(", "):
                cat = cat.strip()
                if cat:
                    cur.execute(
                        "INSERT INTO category (business_id, category_name) VALUES (?,?)",
                        (biz["business_id"], cat)
                    )
        # Insert attributes
        attrs = parse_attributes(biz.get("attributes", {}))
        for k, v in attrs.items():
            cur.execute(
                "INSERT INTO attribute (business_id, attr_name, attr_value) VALUES (?,?,?)",
                (biz["business_id"], k, str(v))
            )
        # Insert hours
        hours = biz.get("hours") or {}
        if isinstance(hours, dict):
            for day, times in hours.items():
                if not times or not isinstance(times, str):
                    open_t, close_t = "", ""
                else:
                    parts = times.split("-")
                    if len(parts) >= 2:
                        open_t, close_t = parts[0].strip(), parts[1].strip()
                    else:
                        open_t, close_t = parts[0].strip(), ""
                cur.execute(
                    "INSERT INTO hours (business_id, day, open_time, close_time) VALUES (?,?,?,?)",
                    (biz["business_id"], day, open_t, close_t)
                )
    conn.commit()

print("Businesses loaded.")

# ---- 2. Load reviews (this gives 10k+ rows easily) ----
try:
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        batch = []
        for line in f:
            rev = json.loads(line)
            batch.append((
                rev["review_id"],
                rev["business_id"],
                rev["user_id"],
                rev["stars"],
                rev.get("text", ""),
                rev.get("date", "")
            ))
            if len(batch) >= 5000:
                cur.executemany(
                    "INSERT OR IGNORE INTO review VALUES (?,?,?,?,?,?)",
                    batch
                )
                batch = []
        if batch:
            cur.executemany(
                "INSERT OR IGNORE INTO review VALUES (?,?,?,?,?,?)",
                batch
            )
        conn.commit()
    print("Reviews loaded.")
except FileNotFoundError:
    print("review.json not found – skipping reviews.")
    print("You can still meet the 10k+ rows requirement with attributes/hours if needed.")

conn.close()