# Delivery Ops Analytics Pipeline

A small but complete analytics engineering pipeline that takes raw, messy
operational data (synthetic delivery order events, generated with
deliberate flaws like duplicates, nulls, and invalid values) and turns it
into trustworthy, decision-ready datasets. It's built to demonstrate the
full lifecycle of working with data professionally, not just querying it.

**SQL-based ELT.** Raw data is loaded into a warehouse (SQLite standing in
for something like Snowflake or BigQuery) and transformed with SQL window
functions, joins, and aggregations, deduplicating records, filtering out
invalid rows, and building clean fact and dimension tables at a
well-defined grain. This is the core skill of designing canonical
datasets: a single source of truth other tables and reports build on,
instead of everyone re-deriving their own version of the same numbers.

**Automated data quality validation.** Seven declarative checks (built in
the same pattern as tools like Great Expectations or Pydeequ) verify
uniqueness, referential integrity, null-rate thresholds, and plausible
value ranges. This is the discipline of proving data is correct before
anyone relies on it, in a way that's repeatable and CI-ready rather than
a one-time manual check.

**A self-serve dashboard.** Built in Streamlit on top of the validated
data, surfacing the metrics a business team would actually care about
(order volume, revenue, delivery times, on-time rates) with region-level
filtering. This closes the loop from raw data to something non-technical
stakeholders can use themselves.

Together, the project spans the full analytics engineering stack:
transforming raw data with SQL, validating it rigorously, and delivering
it in a form other people can act on.

## Architecture

```
raw_orders.csv (raw, messy event data)
        |
        v
  elt_pipeline.py  -- SQL transforms (SQLite)
        |
        v
  dim_restaurant / dim_date / fact_orders / mart_daily_region_metrics
        |
        +--> data_quality_checks.py  -- 7 automated integrity checks
        |
        +--> dashboard.py  -- Streamlit self-serve dashboard
```

## What it demonstrates

- **SQL-based ETL/ELT**: raw event data is loaded into a warehouse table
  and transformed with SQL (window functions for deduplication, joins,
  aggregation) into canonical fact and dimension tables at a clean,
  documented grain.
- **Canonical datasets**: `fact_orders` is deduplicated on `order_id`,
  filtered of invalid rows (negative subtotals, missing join keys), and
  is the single source of truth downstream consumers query instead of
  re-deriving logic themselves.
- **Data quality / integrity checks**: `data_quality_checks.py` runs
  7 declarative expectations against the canonical tables (uniqueness,
  referential integrity, null-rate thresholds, plausible-range checks),
  in the same spirit as Great Expectations / Pydeequ, and exits non-zero
  on failure so it's CI-pipeline-ready.
- **Dashboarding**: `dashboard.py` is a self-serve Streamlit app reading
  only from the canonical daily-region mart, with filters and headline
  metrics, letting non-technical stakeholders explore results themselves
  instead of requesting a custom report each time.

## Run it

```bash
pip install pandas numpy streamlit
python3 generate_data.py        # generates raw_orders.csv (~20k rows, intentionally messy)
python3 elt_pipeline.py         # builds analytics.db with canonical fact/dim tables
python3 data_quality_checks.py  # runs the 7 integrity checks, exits 0 if all pass
streamlit run dashboard.py      # launches the self-serve dashboard
```

## Results

- 20,100 raw rows -> 19,960 clean canonical fact rows after dedup and
  invalid-row filtering.
- 7/7 automated data quality checks passing.
- Daily-region mart powering a dashboard with order volume, GMV, average
  delivery time, and on-time delivery % by region.
