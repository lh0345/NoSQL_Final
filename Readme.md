# Yelp SQL to MongoDB Migration

A Python database project that moves Yelp Academic Dataset data from a relational SQLite database into MongoDB.

The project does more than copy rows. It changes the relational structure into MongoDB documents, calculates derived values, validates the migrated data, and analyzes the MongoDB collection.

## What I Implemented

* Created a relational SQLite schema
* Loaded Yelp JSON data into SQLite
* Read relational data from several tables
* Grouped categories by business
* Converted attributes into embedded documents
* Converted business hours into embedded documents
* Calculated review counts and average ratings from review data
* Created MongoDB business documents from the relational records
* Used `replace_one(..., upsert=True)` so the migration can run again without creating duplicate business records
* Added validation after migration
* Created MongoDB indexes
* Wrote MongoDB aggregation pipelines
* Analyzed categories, cities, review counts, ratings, and restaurant attributes
* Exported CSV summaries
* Created charts with Pandas and Matplotlib

## What I Learned

This project taught me the practical difference between relational and document database design.

In SQLite, related information sits across several normalized tables. During migration, I grouped that related data and embedded categories, attributes, and opening hours inside each MongoDB business document.

That helped me understand why moving from SQL to NoSQL is not simply changing database libraries. The data model itself changes.

I also learned how to make a migration repeatable by using upserts instead of blindly inserting the same records again.

The analysis stage taught me how MongoDB aggregation pipelines process data in stages. I worked with operations such as filtering, unwinding arrays, grouping, calculating averages, sorting, and examining nested attributes.

Creating indexes also helped me understand how database structure affects the work required to find and group records.

## What This Project Demonstrates

* Relational database design
* Document database design
* SQL-to-NoSQL migration
* Data transformation
* MongoDB embedded documents
* PyMongo
* Idempotent upserts
* MongoDB indexes
* Aggregation pipelines
* Migration validation
* Data analysis and visualization

## Tech Used

* Python
* SQLite
* MongoDB
* PyMongo
* Pandas
* Matplotlib

## Running the Project

Install the required Python packages:

```bash
pip install pymongo pandas matplotlib
```

Place the required Yelp dataset files in the `data/` directory, then run:

```bash
cd scripts
python setup_rdbms.py
python populate_rdbms.py
python migrate.py
python validate.py
python analysis.py
```

The generated charts are saved under `results/`, and CSV summaries are saved under `report/`.
