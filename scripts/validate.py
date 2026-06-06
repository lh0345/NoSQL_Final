import sqlite3
import hashlib
import json
import os
from pymongo import MongoClient

# Resolve repo-relative paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "yelp_rel.db")

# Connect to both
sql_conn = sqlite3.connect(DB_PATH)
sql_cur = sql_conn.cursor()
# Use a short server selection timeout so the script fails fast if MongoDB is down
mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
mongo_db = mongo_client["yelp_analysis"]
mongo_col = mongo_db["businesses"]

print("=== Validation Report ===\n")

# 1. Record count comparison
sql_cur.execute("SELECT COUNT(*) FROM business")
sql_biz_count = sql_cur.fetchone()[0]
mongo_biz_count = mongo_col.count_documents({})
print(f"[COUNT] Business: SQL={sql_biz_count}, MongoDB={mongo_biz_count} → {'PASS' if sql_biz_count == mongo_biz_count else 'FAIL'}")

# 2. Spot-check checksum on key fields for first 1000 businesses (to keep it fast)
sql_cur.execute("SELECT business_id, name, city, stars FROM business ORDER BY business_id LIMIT 1000")
sql_rows = sql_cur.fetchall()
data_str = ""
for row in sql_rows:
    data_str += f"{row[0]}{row[1]}{row[2]}{row[3]}"
sql_hash = hashlib.sha256(data_str.encode()).hexdigest()

mongo_docs = list(mongo_col.find({}, {"business_id":1, "name":1, "city":1, "stars":1}).sort("business_id",1).limit(1000))
mongo_data = ""
for doc in mongo_docs:
    mongo_data += f"{doc['business_id']}{doc.get('name','')}{doc.get('city','')}{doc.get('stars','')}"
mongo_hash = hashlib.sha256(mongo_data.encode()).hexdigest()

print(f"[CHECKSUM] First 1000 businesses: SQL={sql_hash[:12]}..., MongoDB={mongo_hash[:12]}... → {'PASS' if sql_hash == mongo_hash else 'FAIL'}")

# 3. Spot-check aggregate: average stars per city (top 5 cities)
print("\n[AGGREGATE SPOT-CHECK] Average stars per city (top 5 by count):")
sql_cur.execute("""
    SELECT city, AVG(stars) as avg_stars, COUNT(*) as cnt
    FROM business
    GROUP BY city
    HAVING cnt > 50
    ORDER BY cnt DESC
    LIMIT 5
""")
sql_agg = sql_cur.fetchall()

for row in sql_agg:
    city = row[0]
    mongo_pipeline = [
        {"$match": {"city": city}},
        {"$group": {"_id": None, "avg_stars": {"$avg": "$stars"}, "cnt": {"$sum": 1}}}
    ]
    mongo_res = list(mongo_col.aggregate(mongo_pipeline))
    if mongo_res:
        mongo_avg = mongo_res[0]["avg_stars"]
        mongo_cnt = mongo_res[0]["cnt"]
        match = abs(row[1] - mongo_avg) < 0.01
        print(f"  City: {city:20s} SQL: {row[1]:.2f} ({row[2]}), MongoDB: {mongo_avg:.2f} ({mongo_cnt}) → {'PASS' if match else 'FAIL'}")

sql_conn.close()
mongo_client.close()
print("\nValidation complete.")