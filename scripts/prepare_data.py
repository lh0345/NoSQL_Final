from pymongo import MongoClient
import ast

client = MongoClient("mongodb://localhost:27017/")
db = client["yelp_analysis"]
col = db["businesses"]

# ---- Fix attributes (string → dict) ----
print("Fixing attributes...")
batch = []
for doc in col.find({"attributes": {"$type": "string"}}):
    try:
        parsed = ast.literal_eval(doc["attributes"])
        if isinstance(parsed, dict):
            doc["attributes"] = parsed
            batch.append(doc)
    except:
        pass
    if len(batch) >= 1000:
        for d in batch:
            col.replace_one({"_id": d["_id"]}, d)
        batch = []
for d in batch:
    col.replace_one({"_id": d["_id"]}, d)

# ---- Fix categories (string → array) ----
print("Fixing categories...")

batch = []
for doc in col.find({"categories": {"$exists": True}}):
    categories_value = doc.get("categories")

    if isinstance(categories_value, str):
        doc["categories"] = [category.strip() for category in categories_value.split(",") if category.strip()]
    elif isinstance(categories_value, list):
        doc["categories"] = [str(category).strip() for category in categories_value if str(category).strip()]
    else:
        continue

    batch.append(doc)

    if len(batch) >= 1000:
        for d in batch:
            col.replace_one({"_id": d["_id"]}, d)
        batch = []

for d in batch:
    col.replace_one({"_id": d["_id"]}, d)

print("Data cleanup complete.")