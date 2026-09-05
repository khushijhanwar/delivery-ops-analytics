"""
Generates a synthetic raw 'orders' event dataset that mimics what a
food-delivery platform's operational systems would emit: one row per
order, with restaurant, dasher (courier), consumer, and timing fields.
Deliberately includes realistic messiness (nulls, duplicates, a few
out-of-range values) so the data quality checks have something to catch.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

N = 20000

regions = ["Northeast", "Midwest", "South", "West"]
region_weights = [0.28, 0.22, 0.30, 0.20]

cuisines = ["American", "Mexican", "Italian", "Chinese", "Indian", "Thai", "Fast Food", "Cafe"]

start = datetime(2026, 6, 1)

order_ids = np.arange(1, N + 1)
restaurant_ids = np.random.randint(1, 800, size=N)
dasher_ids = np.random.randint(1, 1500, size=N)
consumer_ids = np.random.randint(1, 12000, size=N)
region = np.random.choice(regions, size=N, p=region_weights)
cuisine = np.random.choice(cuisines, size=N)

order_ts = [start + timedelta(minutes=int(m)) for m in np.random.randint(0, 60 * 24 * 30, size=N)]

# subtotal in dollars, with a long tail
subtotal = np.round(np.random.gamma(shape=3.0, scale=8.0, size=N) + 5, 2)

# delivery time in minutes: base + region effect + noise, with some
# outliers and a chunk of missing values (sensor/telemetry gaps)
region_effect = {"Northeast": 4, "Midwest": 0, "South": -2, "West": 6}
base_delivery = 28 + np.array([region_effect[r] for r in region])
delivery_minutes = np.round(base_delivery + np.random.normal(0, 8, size=N), 1)
delivery_minutes = np.clip(delivery_minutes, 5, None)

df = pd.DataFrame({
    "order_id": order_ids,
    "restaurant_id": restaurant_ids,
    "dasher_id": dasher_ids,
    "consumer_id": consumer_ids,
    "region": region,
    "cuisine": cuisine,
    "order_ts": order_ts,
    "subtotal_usd": subtotal,
    "delivery_minutes": delivery_minutes,
    "is_on_time": (delivery_minutes <= 35).astype(int),
})

# --- inject realistic data quality issues ---

# 1. ~2% missing delivery_minutes (telemetry gaps)
missing_idx = np.random.choice(df.index, size=int(0.02 * N), replace=False)
df.loc[missing_idx, "delivery_minutes"] = np.nan
df.loc[missing_idx, "is_on_time"] = np.nan

# 2. ~0.5% duplicate order_id rows (upstream retry bug)
dupe_idx = np.random.choice(df.index, size=int(0.005 * N), replace=False)
dupes = df.loc[dupe_idx].copy()
df = pd.concat([df, dupes], ignore_index=True)

# 3. a handful of impossible negative subtotals (bad refund logic)
neg_idx = np.random.choice(df.index, size=15, replace=False)
df.loc[neg_idx, "subtotal_usd"] = -df.loc[neg_idx, "subtotal_usd"]

# 4. a few null region values (missing dimension join)
null_region_idx = np.random.choice(df.index, size=25, replace=False)
df.loc[null_region_idx, "region"] = None

df.to_csv("raw_orders.csv", index=False)
print(f"Wrote raw_orders.csv with {len(df)} rows (includes intentional data quality issues).")
