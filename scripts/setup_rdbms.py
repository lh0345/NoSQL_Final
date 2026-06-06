import sqlite3
import os

DB_PATH = os.path.join("..", "data", "yelp_rel.db")   # SQLite file in data/ folder
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
    CREATE TABLE IF NOT EXISTS business (
        business_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT,
        state TEXT,
        stars REAL CHECK(stars >= 1 AND stars <= 5),
        review_count INTEGER,
        is_open INTEGER
    );

    CREATE TABLE IF NOT EXISTS category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id TEXT NOT NULL,
        category_name TEXT NOT NULL,
        FOREIGN KEY (business_id) REFERENCES business(business_id)
    );

    CREATE TABLE IF NOT EXISTS attribute (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id TEXT NOT NULL,
        attr_name TEXT NOT NULL,
        attr_value TEXT,
        FOREIGN KEY (business_id) REFERENCES business(business_id)
    );

    CREATE TABLE IF NOT EXISTS hours (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id TEXT NOT NULL,
        day TEXT NOT NULL,
        open_time TEXT,
        close_time TEXT,
        FOREIGN KEY (business_id) REFERENCES business(business_id)
    );

    CREATE TABLE IF NOT EXISTS review (
        review_id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        user_id TEXT,
        stars INTEGER CHECK(stars >= 1 AND stars <= 5),
        text TEXT,
        date TEXT,
        FOREIGN KEY (business_id) REFERENCES business(business_id)
    );
""")

conn.commit()
conn.close()
print(f"Relational database created at {DB_PATH}")