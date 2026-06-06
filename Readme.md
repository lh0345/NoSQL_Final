
## Technologies & NoSQL Concepts

### MongoDB
- **Document model**: `attributes` stored as nested documents, `categories` as arrays
- **Indexes**: Created on `categories`, `city`, `review_count`, `stars`, and individual attribute fields for fast queries
- **Aggregation pipelines**: Used exclusively for all analytical computations:
  - `$match` → filter restaurants
  - `$unwind` → split category arrays
  - `$group` → compute averages and counts
  - `$sort`, `$addFields`, `$switch` for clean output
- **No pandas groupby** was used for the core analysis

### Python (pymongo, pandas, matplotlib)
- Connects to MongoDB, executes the aggregation pipelines
- Converts the small aggregation results into DataFrames for easy plotting
- Generates charts and exports CSVs

## Analysis Performed

1. **Category Analysis** – Top restaurant categories by average rating (minimum 250 businesses)
2. **City Analysis** – Top cities by average restaurant rating (minimum 200 restaurants)
3. **Attribute Effects** – Rating difference for restaurants that have vs. do not have features like delivery, outdoor seating, reservations, etc.
4. **Review Count vs Rating** – Scatter plot (log scale) showing the relationship between popularity and rating

## How to Run

1. **Set up MongoDB** (local instance on default port 27017)
2. **Import the Yelp business dataset** into the `yelp_analysis` database, collection `businesses`
3. **Clean the data** (run once):
   - Convert `attributes` from string to sub-document
   - Convert `categories` from comma-separated string to array
4. **Run the analysis**:
   ```bash
   cd scripts
   python analysis.py