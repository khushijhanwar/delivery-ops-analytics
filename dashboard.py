"""
Self-serve analytics dashboard on top of the canonical marts, built with
Streamlit to demonstrate the "design metrics and data visualizations"
part of the pipeline. Reads from analytics.db (produced by elt_pipeline.py).

Run: streamlit run dashboard.py
"""
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Delivery Analytics", layout="wide")

conn = sqlite3.connect("analytics.db")
daily = pd.read_sql("SELECT * FROM mart_daily_region_metrics", conn)
daily["order_date"] = pd.to_datetime(daily["order_date"])

st.title("Delivery Ops Analytics")
st.caption("Self-serve dashboard on top of a canonical daily-region mart, built from a validated ELT pipeline.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orders", f"{daily['order_count'].sum():,}")
col2.metric("GMV", f"${daily['gross_merchandise_value'].sum():,.0f}")
col3.metric("Avg Delivery Time", f"{daily['avg_delivery_minutes'].mean():.1f} min")
col4.metric("Avg On-Time %", f"{daily['on_time_pct'].mean():.1f}%")

st.divider()

regions = sorted(daily["region"].unique())
selected_regions = st.multiselect("Filter by region", regions, default=regions)
filtered = daily[daily["region"].isin(selected_regions)]

left, right = st.columns(2)
with left:
    st.subheader("Daily Order Volume by Region")
    pivot_orders = filtered.pivot_table(index="order_date", columns="region", values="order_count", aggfunc="sum")
    st.line_chart(pivot_orders)

with right:
    st.subheader("Avg Delivery Time by Region (min)")
    pivot_delivery = filtered.pivot_table(index="order_date", columns="region", values="avg_delivery_minutes")
    st.line_chart(pivot_delivery)

st.subheader("On-Time Delivery % by Region")
pivot_ontime = filtered.pivot_table(index="order_date", columns="region", values="on_time_pct")
st.bar_chart(pivot_ontime.mean().sort_values(ascending=False))

st.subheader("Underlying Daily-Region Mart")
st.dataframe(filtered.sort_values(["order_date", "region"]), use_container_width=True)

conn.close()
