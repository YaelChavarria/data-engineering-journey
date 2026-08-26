"""Streamlit dashboard for the e-commerce Gold models."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_DIR / "data" / "warehouse" / "ecommerce.duckdb"


st.set_page_config(
    page_title="Commerce Pulse",
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
                   COALESCE(SUM(order_total), 0) AS revenue,
                   COALESCE(AVG(order_total), 0) AS average_order_value,
                   COUNT(DISTINCT customer_id) AS active_customers
            FROM gold_fact_order
            WHERE is_completed
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
    finally:
        connection.close()
    return {
        "kpis": kpis,
        "daily": daily,
        "categories": categories,
        "products": products,
        "customers": customers,
    }


def money(value: float) -> str:
    return f"€{float(value):,.2f}"


path = database_path()
if not path.exists():
    st.error("No existe el warehouse. Ejecuta primero: `python -m ecommerce_lakehouse`")
    st.stop()

summary_path = path.parent.parent / "pipeline_summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
data = load_data(str(path), path.stat().st_mtime)
kpis = data["kpis"]

with st.sidebar:
    st.markdown("## Commerce Pulse")
    st.caption("Gold layer powered by DuckDB + dbt")
    st.divider()
    st.markdown("**Pipeline**")
    st.write(summary.get("pipeline_mode", "unknown").replace("_", " ").title())
    st.markdown("**Última ejecución**")
    st.write(summary.get("generated_at_utc", "No disponible").replace("T", " ")[:19])
    st.divider()
    st.caption(f"Warehouse: `{path.name}`")

st.markdown(
    """
    <div class="hero">
        <h1>Commerce Pulse</h1>
        <p>Una vista ejecutiva de ventas, producto y clientes para la tienda online.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Resumen ejecutivo</div>', unsafe_allow_html=True)
metric_columns = st.columns(4)
metric_columns[0].metric("Ingresos netos", money(kpis["revenue"]))
metric_columns[1].metric("Pedidos completados", f"{int(kpis['completed_orders']):,}")
metric_columns[2].metric("Ticket medio", money(kpis["average_order_value"]))
metric_columns[3].metric("Clientes activos", f"{int(kpis['active_customers']):,}")

st.markdown('<div class="section-label">Evolución y mix comercial</div>', unsafe_allow_html=True)
left, right = st.columns([1.5, 1])
with left:
    st.subheader("Ingresos por día")
    daily = data["daily"].set_index("order_date")
    st.line_chart(daily["revenue"], y_label="Ingresos (€)", height=330)
with right:
    st.subheader("Ingresos por categoría")
    categories = data["categories"].set_index("category")
    st.bar_chart(categories["revenue"], y_label="Ingresos (€)", height=330)

tab_products, tab_customers, tab_quality = st.tabs(["Productos", "Clientes", "Calidad del pipeline"])
with tab_products:
    st.subheader("Productos con mayor facturación")
    products = data["products"].head(8).copy()
    products["revenue"] = products["revenue"].map(money)
    products = products.rename(
        columns={
            "product_name": "Producto",
            "category": "Categoría",
            "units_sold": "Unidades",
            "revenue": "Ingresos",
        }
    )
    st.dataframe(products, width="stretch", hide_index=True)

with tab_customers:
    st.subheader("Clientes por valor de vida")
    customers = data["customers"].head(10).copy()
    customers["lifetime_value"] = customers["lifetime_value"].map(money)
    customers = customers.rename(
        columns={
            "full_name": "Cliente",
            "order_count": "Pedidos",
            "lifetime_value": "Lifetime value",
        }
    )
    st.dataframe(customers, width="stretch", hide_index=True)

with tab_quality:
    st.subheader("Controles de calidad")
    checks = summary.get("quality_checks", {})
    if checks and all(value == 0 for value in checks.values()):
        st.success("Todos los controles de integridad pasaron correctamente.")
    else:
        st.warning("Revisa los controles que presentan incidencias.")
    if checks:
        check_rows = [
            {"Control": name.replace("_", " ").title(), "Incidencias": value}
            for name, value in checks.items()
        ]
        st.dataframe(check_rows, width="stretch", hide_index=True)
