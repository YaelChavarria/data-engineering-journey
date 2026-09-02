"""Streamlit dashboard for the Revenue Protection Gold models."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_DIR / "data" / "warehouse" / "ecommerce.duckdb"


st.set_page_config(
    page_title="Revenue Protection Control Tower",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #f5f7fb; }
        [data-testid="stSidebar"] { background: #101827; }
        [data-testid="stSidebar"] * { color: #e8edf5; }
         .hero {
            background: linear-gradient(120deg, #101827 0%, #1e3a5f 65%, #147d92 100%);
            border-radius: 18px;
            padding: 28px 32px;
            margin-bottom: 22px;
            color: white;
        }
        .hero h1 { margin: 0 0 6px 0; font-size: 2.35rem; }
        .hero p { margin: 0; color: #c9d7e8; font-size: 1.05rem; }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #e3e9f2;
            border-radius: 14px;
            padding: 14px 16px;
        }
        .section-label {
            color: #147d92;
            font-size: .75rem;
            font-weight: 700;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin: 20px 0 8px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def database_path() -> Path:
    return Path(os.environ.get("ECOMMERCE_DB_PATH", str(DEFAULT_DATABASE))).resolve()


@st.cache_data(show_spinner=False)
def load_data(path: str, modified_at: float) -> dict:
    connection = duckdb.connect(path, read_only=True)
    try:
        kpis = connection.execute(
            """
            SELECT COUNT(*) AS completed_orders,
                   COALESCE(SUM(net_revenue) FILTER (WHERE is_completed), 0) AS revenue,
                   COALESCE(AVG(net_revenue) FILTER (WHERE is_completed), 0) AS average_order_value,
                   COALESCE(SUM(refunded_amount), 0) AS refunded_amount,
                   COALESCE(SUM(leakage_amount), 0) AS leakage_amount,
                   COALESCE(100.0 * SUM(CASE WHEN is_late AND is_completed THEN 1 ELSE 0 END)
                       / NULLIF(SUM(CASE WHEN is_completed THEN 1 ELSE 0 END), 0), 0) AS late_delivery_rate,
                   COUNT(DISTINCT customer_id) FILTER (WHERE is_completed) AS active_customers
             FROM gold_fact_order
            """
        ).fetchdf().iloc[0].to_dict()
        daily = connection.execute(
            """SELECT order_date, order_count, revenue, average_order_value
               FROM gold_daily_sales ORDER BY order_date"""
        ).fetchdf()
        categories = connection.execute(
            """SELECT category, units_sold, revenue
               FROM gold_category_sales ORDER BY revenue DESC"""
        ).fetchdf()
        products = connection.execute(
            """SELECT product_name, category, units_sold, revenue
               FROM gold_product_sales ORDER BY revenue DESC"""
        ).fetchdf()
        customers = connection.execute(
            """SELECT full_name, order_count, lifetime_value
               FROM gold_customer_sales ORDER BY lifetime_value DESC"""
        ).fetchdf()
        operations = connection.execute(
            """SELECT order_date, net_revenue, leakage_amount, late_delivery_rate
               FROM gold_operations_daily ORDER BY order_date"""
        ).fetchdf()
        leakage = connection.execute(
            """SELECT leakage_type, affected_orders, leakage_amount, priority
               FROM gold_revenue_leakage ORDER BY leakage_amount DESC"""
        ).fetchdf()
    finally:
        connection.close()
    return {
        "kpis": kpis,
        "daily": daily,
        "categories": categories,
        "products": products,
        "customers": customers,
        "operations": operations,
        "leakage": leakage,
    }


def money(value: float) -> str:
    return f"${float(value):,.2f}"


path = database_path()
if not path.exists():
    st.error("Warehouse not found. Run `python -m ecommerce_lakehouse` first.")
    st.stop()

summary_path = path.parent.parent / "pipeline_summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
data = load_data(str(path), path.stat().st_mtime)
kpis = data["kpis"]

with st.sidebar:
    st.markdown("## Revenue Protection")
    st.caption("Decision layer powered by DuckDB + dbt")
    st.divider()
    st.markdown("**Pipeline**")
    st.write(summary.get("pipeline_mode", "unknown").replace("_", " ").title())
    st.markdown("**Last run (UTC)**")
    st.write(summary.get("generated_at_utc", "No disponible").replace("T", " ")[:19])
    st.divider()
    st.caption(f"Warehouse: `{path.name}`")

st.markdown(
    """
    <div class="hero">
             <h1>Revenue Protection Control Tower</h1>
             <p>Find revenue leakage and prioritize the next operational action.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Executive signal</div>', unsafe_allow_html=True)
metric_columns = st.columns(4)
metric_columns[0].metric("Net revenue", money(kpis["revenue"]))
metric_columns[1].metric("Revenue leakage", money(kpis["leakage_amount"]), delta=f"{kpis['refunded_amount']:.2f} refunded")
metric_columns[2].metric("Late delivery rate", f"{kpis['late_delivery_rate']:.1f}%")
metric_columns[3].metric("Completed orders", f"{int(kpis['completed_orders']):,}")

st.markdown('<div class="section-label">Revenue and operational risk</div>', unsafe_allow_html=True)
left, right = st.columns([1.5, 1])
with left:
    st.subheader("Net revenue by day")
    daily = data["daily"].set_index("order_date")
    st.line_chart(daily["revenue"], y_label="Revenue ($)", height=330)
with right:
    st.subheader("Leakage by cause")
    leakage = data["leakage"].set_index("leakage_type")
    st.bar_chart(leakage["leakage_amount"], y_label="Leakage ($)", height=330)

tab_operations, tab_products, tab_customers, tab_quality = st.tabs(["Operations", "Products", "Customers", "Pipeline quality"])
with tab_operations:
    st.subheader("Operational priorities")
    leakage = data["leakage"].copy()
    leakage["leakage_amount"] = leakage["leakage_amount"].map(money)
    leakage = leakage.rename(
        columns={
            "leakage_type": "Cause",
            "affected_orders": "Affected orders",
            "leakage_amount": "Leakage",
            "priority": "Priority",
        }
    )
    st.dataframe(leakage, width="stretch", hide_index=True)
    st.caption("Prioritize high-value causes first. Values are from the simulated case study.")

with tab_products:
    st.subheader("Top products by revenue")
    products = data["products"].head(8).copy()
    products["revenue"] = products["revenue"].map(money)
    products = products.rename(
        columns={
            "product_name": "Product",
            "category": "Category",
            "units_sold": "Units",
            "revenue": "Revenue",
        }
    )
    st.dataframe(products, width="stretch", hide_index=True)

with tab_customers:
    st.subheader("Customers by lifetime value")
    customers = data["customers"].head(10).copy()
    customers["lifetime_value"] = customers["lifetime_value"].map(money)
    customers = customers.rename(
        columns={
            "full_name": "Customer",
            "order_count": "Orders",
            "lifetime_value": "Lifetime value",
        }
    )
    st.dataframe(customers, width="stretch", hide_index=True)

with tab_quality:
    st.subheader("Quality controls")
    checks = summary.get("quality_checks", {})
    if checks and all(value == 0 for value in checks.values()):
        st.success("All integrity checks passed.")
    else:
        st.warning("Review the controls with incidents.")
    if checks:
        check_rows = [
            {"Control": name.replace("_", " ").title(), "Incidents": value}
            for name, value in checks.items()
        ]
        st.dataframe(check_rows, width="stretch", hide_index=True)
