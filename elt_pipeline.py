"""
ELT pipeline: loads the raw orders CSV into SQLite (standing in for a
data warehouse / lake table), then runs SQL transformations to build
canonical, analytics-ready fact and dimension tables.

Run: python3 elt_pipeline.py
"""
import sqlite3
import pandas as pd

DB_PATH = "analytics.db"

TRANSFORM_SQL = """
-- ============================================================
-- Canonical dimension: restaurants (one row per restaurant_id)
-- ============================================================
DROP TABLE IF EXISTS dim_restaurant;
CREATE TABLE dim_restaurant AS
SELECT
    restaurant_id,
    -- most frequent cuisine tagged to this restaurant in raw data
    (
        SELECT cuisine
        FROM raw_orders r2
        WHERE r2.restaurant_id = r1.restaurant_id AND cuisine IS NOT NULL
        GROUP BY cuisine
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ) AS primary_cuisine,
    COUNT(DISTINCT order_id) AS lifetime_orders
FROM raw_orders r1
WHERE restaurant_id IS NOT NULL
GROUP BY restaurant_id;

-- ============================================================
-- Canonical dimension: date (one row per calendar date in range)
-- ============================================================
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
SELECT DISTINCT
    DATE(order_ts) AS order_date,
    CAST(strftime('%w', order_ts) AS INTEGER) AS day_of_week,
    CASE WHEN CAST(strftime('%w', order_ts) AS INTEGER) IN (0, 6)
         THEN 1 ELSE 0 END AS is_weekend
FROM raw_orders;

-- ============================================================
-- Canonical fact table: orders
-- Deduplicated on order_id, nulls/invalid rows excluded, one
-- clean grain of "one row per completed order."
-- ============================================================
DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders AS
SELECT
    order_id,
    restaurant_id,
    dasher_id,
    consumer_id,
    region,
    cuisine,
    DATE(order_ts) AS order_date,
    order_ts,
    subtotal_usd,
    delivery_minutes,
    is_on_time
FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_ts) AS rn
    FROM raw_orders
    WHERE subtotal_usd >= 0        -- drop the negative-refund bad rows
      AND region IS NOT NULL       -- drop rows missing the join key
)
WHERE rn = 1;                      -- dedupe retried order_ids

-- ============================================================
-- Aggregate mart: daily region-level metrics for the dashboard
-- ============================================================
DROP TABLE IF EXISTS mart_daily_region_metrics;
CREATE TABLE mart_daily_region_metrics AS
SELECT
    order_date,
    region,
    COUNT(*) AS order_count,
    ROUND(SUM(subtotal_usd), 2) AS gross_merchandise_value,
    ROUND(AVG(delivery_minutes), 2) AS avg_delivery_minutes,
    ROUND(AVG(is_on_time) * 100, 1) AS on_time_pct
FROM fact_orders
WHERE delivery_minutes IS NOT NULL
GROUP BY order_date, region
ORDER BY order_date, region;
"""


def run_pipeline():
    raw = pd.read_csv("raw_orders.csv")

    conn = sqlite3.connect(DB_PATH)
    raw.to_sql("raw_orders", conn, if_exists="replace", index=False)

    conn.executescript(TRANSFORM_SQL)
    conn.commit()

    counts = {}
    for table in ["raw_orders", "dim_restaurant", "dim_date", "fact_orders", "mart_daily_region_metrics"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    conn.close()
    return counts


if __name__ == "__main__":
    counts = run_pipeline()
    print("ELT pipeline complete. Row counts:")
    for table, n in counts.items():
        print(f"  {table}: {n:,} rows")
