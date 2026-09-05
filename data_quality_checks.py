"""
Data quality validation layer for the analytics pipeline, in the spirit
of Great Expectations / Pydeequ: a declarative list of "expectations"
run against the canonical fact table, each producing a pass/fail result
plus a human-readable message so failures are actionable, not just a
stack trace.

Run: python3 data_quality_checks.py
"""
import sqlite3
import sys

DB_PATH = "analytics.db"


class Expectation:
    def __init__(self, name, sql, check_fn, description):
        self.name = name
        self.sql = sql
        self.check_fn = check_fn
        self.description = description

    def run(self, conn):
        result = conn.execute(self.sql).fetchone()
        passed = self.check_fn(result)
        return passed, result


EXPECTATIONS = [
    Expectation(
        name="fact_orders.order_id is unique",
        sql="SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM fact_orders",
        check_fn=lambda r: r[0] == 0,
        description="No duplicate order_id values after dedup step.",
    ),
    Expectation(
        name="fact_orders.subtotal_usd is non-negative",
        sql="SELECT COUNT(*) FROM fact_orders WHERE subtotal_usd < 0",
        check_fn=lambda r: r[0] == 0,
        description="No negative order subtotals should reach the canonical fact table.",
    ),
    Expectation(
        name="fact_orders.region is not null",
        sql="SELECT COUNT(*) FROM fact_orders WHERE region IS NULL",
        check_fn=lambda r: r[0] == 0,
        description="Every fact row must join cleanly to a region dimension value.",
    ),
    Expectation(
        name="fact_orders.restaurant_id has referential integrity",
        sql="""SELECT COUNT(*) FROM fact_orders f
               LEFT JOIN dim_restaurant d ON f.restaurant_id = d.restaurant_id
               WHERE d.restaurant_id IS NULL""",
        check_fn=lambda r: r[0] == 0,
        description="Every fact row's restaurant_id must exist in dim_restaurant.",
    ),
    Expectation(
        name="fact_orders.delivery_minutes null rate is under 5%",
        sql="""SELECT
                 ROUND(100.0 * SUM(CASE WHEN delivery_minutes IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
               FROM fact_orders""",
        check_fn=lambda r: r[0] < 5.0,
        description="Telemetry gaps in delivery_minutes should stay under a 5% threshold.",
    ),
    Expectation(
        name="fact_orders.delivery_minutes is within a plausible range",
        sql="SELECT COUNT(*) FROM fact_orders WHERE delivery_minutes < 0 OR delivery_minutes > 180",
        check_fn=lambda r: r[0] == 0,
        description="Delivery times should fall within 0-180 minutes; anything outside is a sensor error.",
    ),
    Expectation(
        name="mart_daily_region_metrics covers all 4 regions",
        sql="SELECT COUNT(DISTINCT region) FROM mart_daily_region_metrics",
        check_fn=lambda r: r[0] == 4,
        description="The daily mart should always report on Northeast, Midwest, South, and West.",
    ),
]


def run_all_checks():
    conn = sqlite3.connect(DB_PATH)
    results = []
    for exp in EXPECTATIONS:
        passed, raw_result = exp.run(conn)
        results.append((exp, passed, raw_result))
    conn.close()
    return results


def print_report(results):
    print("=" * 70)
    print("DATA QUALITY VALIDATION REPORT")
    print("=" * 70)
    n_passed = sum(1 for _, passed, _ in results if passed)
    for exp, passed, raw_result in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {exp.name}")
        print(f"       {exp.description}")
        print(f"       raw result: {raw_result}")
    print("-" * 70)
    print(f"{n_passed}/{len(results)} checks passed")
    print("=" * 70)
    return n_passed == len(results)


if __name__ == "__main__":
    results = run_all_checks()
    all_passed = print_report(results)
    sys.exit(0 if all_passed else 1)
