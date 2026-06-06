import sqlite3
import os
from pymongo import MongoClient
import sys
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "yelp_rel.db")

# Connect to source (SQLite)
sql_conn = sqlite3.connect(DB_PATH)
sql_conn.row_factory = sqlite3.Row   # so we can access by column name
sql_cur = sql_conn.cursor()

# Connect to target (MongoDB)
mongo_client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000,
    socketTimeoutMS=5000
)
# Fail fast if MongoDB is not reachable
try:
    mongo_client.admin.command('ping')
except Exception as e:
    print("ERROR: cannot connect to MongoDB at mongodb://localhost:27017/:", e)
    print("Start MongoDB or adjust the connection string in scripts/migrate.py and try again.")
    sys.exit(1)

mongo_db = mongo_client["yelp_analysis"]
mongo_col = mongo_db["businesses"]   # same collection as before

# ---- 1. Fetch all businesses ----
sql_cur.execute("SELECT * FROM business")
businesses = sql_cur.fetchall()

# ---- 2. Prepare data structures for categories, attributes, hours, reviews ----
# We'll fetch them all and group by business_id for efficient embedding.

# Categories
sql_cur.execute("SELECT business_id, category_name FROM category")
cat_rows = sql_cur.fetchall()
cats_by_biz = defaultdict(list)
for row in cat_rows:
    cats_by_biz[row["business_id"]].append(row["category_name"])

# Attributes
sql_cur.execute("SELECT business_id, attr_name, attr_value FROM attribute")
attr_rows = sql_cur.fetchall()
attrs_by_biz = defaultdict(dict)
for row in attr_rows:
    attrs_by_biz[row["business_id"]][row["attr_name"]] = row["attr_value"]

# Hours
sql_cur.execute("SELECT business_id, day, open_time, close_time FROM hours")
hour_rows = sql_cur.fetchall()
hours_by_biz = defaultdict(dict)
for row in hour_rows:
    hours_by_biz[row["business_id"]][row["day"]] = f"{row['open_time']}-{row['close_time']}"

# Reviews: compute count and average rating per business (derived fields!)
sql_cur.execute("SELECT business_id, COUNT(*) as cnt, AVG(stars) as avg_stars FROM review GROUP BY business_id")
review_stats = {row["business_id"]: (row["cnt"], row["avg_stars"]) for row in sql_cur.fetchall()}

# ---- 3. Build and insert MongoDB documents ----
inserted_count = 0
error_count = 0

try:
    for biz in businesses:
        bid = biz["business_id"]
        try:
            # Skip if no name (malformed)
            if not biz["name"]:
                error_count += 1
                print(f"WARNING: Business {bid} has no name – skipping.")
                continue

            # Use derived review stats if available, otherwise fallback to original fields
            if bid in review_stats:
                review_count, avg_rating = review_stats[bid]
                # We can use the computed average rating instead of the original 'stars' field
                # to prove we derived it during migration. Keep both for comparison.
                derived_stars = round(avg_rating, 2) if avg_rating else biz["stars"]
            else:
                review_count = biz["review_count"]
                derived_stars = biz["stars"]

            doc = {
                "business_id": bid,
                "name": biz["name"],
                "city": biz["city"],
                "state": biz["state"],
                "stars": biz["stars"],            # original
                "derived_stars": derived_stars,    # NEW derived field
                "review_count": review_count,      # NEW derived field (from actual reviews)
                "is_open": biz["is_open"],
                "categories": cats_by_biz.get(bid, []),          # transformation: embedded array
                "attributes": attrs_by_biz.get(bid, {}),         # transformation: embedded document
                "hours": hours_by_biz.get(bid, {})               # transformation: embedded document
            }

            # Idempotent upsert
            mongo_col.replace_one(
                {"business_id": bid},
                doc,
                upsert=True
            )
            inserted_count += 1
        except Exception as e:
            error_count += 1
            print(f"ERROR processing business {bid}: {e}")
except KeyboardInterrupt:
    print("\nMigration interrupted by user (KeyboardInterrupt).")
    print(f"Progress so far — Inserted/updated: {inserted_count}, errors: {error_count}")

print(f"Migration complete. Inserted/updated: {inserted_count}, errors: {error_count}")
sql_conn.close()
mongo_client.close()