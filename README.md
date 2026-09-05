# Delivery Ops Analytics Pipeline

A small end-to-end analytics engineering pipeline: synthetic raw delivery
order events -> validated ELT into canonical fact/dimension tables in a SQL
warehouse (SQLite standing in for a warehouse) -> data quality checks ->
a self-serve Streamlit dashboard.

Built to mirror the core workflow of an Analytics Engineer: turn raw,
messy operational data into trusted, canonical datasets that support
decision-making, with data integrity checks and dashboarding on top.

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
  metrics, showing the "insights teams can self-serve" layer the role
  calls for.

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
