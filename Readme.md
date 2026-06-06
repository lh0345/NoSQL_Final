# Yelp Data Migration: SQL → MongoDB

## Overview
This project migrates the Yelp Academic Dataset from a relational (SQLite) database to MongoDB, applying meaningful transformations. The pipeline includes data validation and a visualization layer built on the NoSQL side.

## Project Structure
├── data/ # ignored by Git – contains raw JSON and SQLite DB
├── scripts/
│ ├── setup_rdbms.py # create relational schema
│ ├── populate_rdbms.py # load JSON data into SQLite
│ ├── migrate.py # migration script (SQL → MongoDB with transformations)
│ ├── validate.py # data validation checks
│ └── analysis.py # visualization layer (reads from MongoDB)
├── results/ # generated charts (PNG)
├── report/ # exported CSV files
├── ER_diagram.png # (add your ER diagram)
└── README.md

## Setup & Run
1. Install dependencies: `pymongo`, `pandas`, `matplotlib`, `sqlite3` (standard).
2. Place `business.json` and `review.json` in the `data/` folder.
3. Run the pipeline:
   ```bash
   cd scripts
   python setup_rdbms.py
   python populate_rdbms.py
   python migrate.py
   python validate.py
   python analysis.py
4. View charts in results/, CSVs in report/, and validation output in console.
