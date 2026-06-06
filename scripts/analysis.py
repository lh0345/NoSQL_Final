from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import os

# ============================================================
# CONFIG
# ============================================================
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "yelp_analysis"
COLLECTION_NAME = "businesses"

MIN_CATEGORY_COUNT = 250
MIN_CITY_COUNT = 200
MIN_ATTRIBUTE_COUNT = 250

ATTRIBUTE_KEYS = [
    "RestaurantsDelivery",
    "RestaurantsTakeOut",
    "OutdoorSeating",
    "RestaurantsReservations",
    "GoodForKids",
    "WiFi",
]

GENERIC_CATEGORIES = [
    "restaurants", "restaurant", "food", "nightlife", "bars",
    "local flavor", "event planning & services", "arts & entertainment"
]

BOOL_TRUE = ["true", "yes", "free", "full_bar", "beer_and_wine", "valet"]
BOOL_FALSE = ["false", "no", "none", "nope"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)            # one level up = project root
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print(f"Script location   : {SCRIPT_DIR}")
print(f"Project root      : {PROJECT_DIR}")
print(f"Results will go to: {RESULTS_DIR}")

# ============================================================
# PLOTTING HELPERS
# ============================================================
def save_horizontal_bar(labels, values, title, xlabel, filename, value_fmt="{:.3f}"):
    if len(labels) == 0:
        return
    min_v = min(values)
    max_v = max(values)
    plt.figure(figsize=(12, max(5, 0.45 * len(labels) + 1.5)))
    bars = plt.barh(labels, values)
    plt.gca().invert_yaxis()
    plt.title(title)
    plt.xlabel(xlabel)
    pad = max(0.03, (max_v - min_v) * 0.20)
    plt.xlim(max(0, min_v - pad), min(5, max_v + pad))
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.005, bar.get_y() + bar.get_height()/2,
                 value_fmt.format(width), va="center", fontsize=9)
    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, filename)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.show()
    print(f"Saved: {path}")

def save_vertical_bar(labels, values, title, ylabel, filename, value_fmt="{:.3f}"):
    if len(labels) == 0:
        return
    min_v = min(values)
    max_v = max(values)
    pad = max(0.03, (max_v - min_v) * 0.20)
    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.ylim(max(0, min_v - pad), min(5, max_v + pad))
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                 value_fmt.format(height), ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, filename)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.show()
    print(f"Saved: {path}")

# ============================================================
# CONNECT & INDEX
# ============================================================
print("Connecting to MongoDB...")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
col = db[COLLECTION_NAME]

print("Creating indexes (if not already present)...")
col.create_index("categories")
col.create_index("city")
col.create_index("review_count")
col.create_index("stars")
for attr in ATTRIBUTE_KEYS:
    col.create_index(f"attributes.{attr}")

# ============================================================
# 1. CATEGORY AGGREGATION
# ============================================================
print("\nRunning category aggregation...")
pipeline_cat = [
    {"$match": {"categories": {"$regex": "Restaurant", "$options": "i"}}},
    {"$unwind": "$categories"},
    {"$addFields": {"cat_lower": {"$toLower": "$categories"}}},
    {"$match": {"cat_lower": {"$nin": GENERIC_CATEGORIES}}},
    {"$group": {"_id": "$cat_lower", "avg_rating": {"$avg": "$stars"}, "count": {"$sum": 1}}},
    {"$match": {"count": {"$gte": MIN_CATEGORY_COUNT}}},
    {"$sort": {"avg_rating": -1}}
]
cat_df = pd.DataFrame(list(col.aggregate(pipeline_cat))).rename(columns={"_id": "category"})

# ============================================================
# 2. CITY AGGREGATION
# ============================================================
print("Running city aggregation...")
pipeline_city = [
    {"$match": {"categories": {"$regex": "Restaurant", "$options": "i"}}},
    {"$group": {"_id": "$city", "avg_rating": {"$avg": "$stars"}, "business_count": {"$sum": 1}, "avg_review_count": {"$avg": "$review_count"}}},
    {"$match": {"business_count": {"$gte": MIN_CITY_COUNT}}},
    {"$sort": {"avg_rating": -1}}
]
city_df = pd.DataFrame(list(col.aggregate(pipeline_city))).rename(columns={"_id": "city"})

# ============================================================
# 3. ATTRIBUTE AGGREGATION
# ============================================================
print("Running attribute aggregations...")
attribute_effect_rows = []
attribute_group_rows = []

for key in ATTRIBUTE_KEYS:
    pipeline_attr = [
        {"$match": {"categories": {"$regex": "Restaurant", "$options": "i"}, f"attributes.{key}": {"$exists": True}}},
        {"$group": {
            "_id": {"$switch": {
                "branches": [
                    {"case": {"$in": [{"$toLower": f"$attributes.{key}"}, BOOL_TRUE]}, "then": "Yes"},
                    {"case": {"$in": [{"$toLower": f"$attributes.{key}"}, BOOL_FALSE]}, "then": "No"}
                ],
                "default": "Other"
            }},
            "avg_rating": {"$avg": "$stars"},
            "count": {"$sum": 1}
        }}
    ]
    results = list(col.aggregate(pipeline_attr))
    yes = next((r for r in results if r["_id"] == "Yes"), None)
    no  = next((r for r in results if r["_id"] == "No"), None)
    if yes and no and yes["count"] >= MIN_ATTRIBUTE_COUNT and no["count"] >= MIN_ATTRIBUTE_COUNT:
        delta = yes["avg_rating"] - no["avg_rating"]
        attribute_effect_rows.append({
            "attribute": key, "yes_avg": yes["avg_rating"], "no_avg": no["avg_rating"],
            "delta": delta, "yes_count": yes["count"], "no_count": no["count"]
        })
        attribute_group_rows.append({"attribute": key, "group": "Yes / Present", "avg_rating": yes["avg_rating"], "count": yes["count"]})
        attribute_group_rows.append({"attribute": key, "group": "No / Absent", "avg_rating": no["avg_rating"], "count": no["count"]})

attr_effect_df = pd.DataFrame(attribute_effect_rows)
attr_group_df = pd.DataFrame(attribute_group_rows)

# ============================================================
# 4. REVIEW COUNT vs RATING (simple projection)
# ============================================================
print("Loading review/rating data for scatter...")
review_df = pd.DataFrame(list(col.find(
    {"categories": {"$regex": "Restaurant", "$options": "i"}},
    {"review_count": 1, "stars": 1, "_id": 0}
)))

# ============================================================
# PLOT & SAVE
# ============================================================
print("\nGenerating charts...")

# Categories (top 10)
if not cat_df.empty:
    top_cat = cat_df.head(10).copy()
    save_horizontal_bar(top_cat["category"][::-1].tolist(), top_cat["avg_rating"][::-1].tolist(),
                        "Top 10 Restaurant Categories by Average Rating", "Average Rating", "top_categories.png")
    cat_df.to_csv(os.path.join(RESULTS_DIR, "category_summary.csv"), index=False)

# Cities (top 10)
if not city_df.empty:
    top_city = city_df.head(10).copy()
    save_horizontal_bar(top_city["city"][::-1].tolist(), top_city["avg_rating"][::-1].tolist(),
                        "Top 10 Cities by Average Restaurant Rating", "Average Rating", "top_cities.png")
    city_df.to_csv(os.path.join(RESULTS_DIR, "city_summary.csv"), index=False)

# Attribute effects
if not attr_effect_df.empty:
    plt.figure(figsize=(12, max(5, 0.5 * len(attr_effect_df) + 1.5)))
    bars = plt.barh(attr_effect_df["attribute"], attr_effect_df["delta"])
    plt.axvline(0, color="black", linewidth=1)
    plt.title("Restaurant Attribute Effect on Rating (Yes – No)")
    plt.xlabel("Difference in Average Rating")
    max_abs = attr_effect_df["delta"].abs().max()
    pad = max(0.02, max_abs * 0.35)
    plt.xlim(-(max_abs + pad), max_abs + pad)
    for bar, delta in zip(bars, attr_effect_df["delta"]):
        x = bar.get_width()
        y = bar.get_y() + bar.get_height()/2
        plt.text(x + (0.005 if x >= 0 else -0.005), y, f"{delta:+.3f}",
                 va="center", ha="left" if x >= 0 else "right", fontsize=9)
    plt.tight_layout()
    attr_path = os.path.join(RESULTS_DIR, "attribute_effects.png")
    plt.savefig(attr_path, dpi=200, bbox_inches="tight")
    plt.show()
    print(f"Saved: {attr_path}")
    attr_effect_df.to_csv(os.path.join(RESULTS_DIR, "attribute_effect_summary.csv"), index=False)
    attr_group_df.to_csv(os.path.join(RESULTS_DIR, "attribute_group_summary.csv"), index=False)

# Scatter: review count vs rating
if not review_df.empty:
    plt.figure(figsize=(10, 6))
    plt.scatter(review_df["review_count"], review_df["stars"], alpha=0.18, s=12)
    plt.xscale("log")
    plt.ylim(2.5, 5.0)
    plt.title("Review Count vs Rating (Restaurants Only)")
    plt.xlabel("Review Count (log scale)")
    plt.ylabel("Stars")
    plt.tight_layout()
    scatter_path = os.path.join(RESULTS_DIR, "review_count_vs_rating.png")
    plt.savefig(scatter_path, dpi=200, bbox_inches="tight")
    plt.show()
    print(f"Saved: {scatter_path}")

print("\n" + "="*60)
print(f"All results saved in: {RESULTS_DIR}")
print("="*60)