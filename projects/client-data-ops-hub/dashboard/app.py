"""Client-facing dashboard for the managed data delivery demonstration."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_DIR / "data" / "warehouse" / "client_delivery.duckdb"

st.set_page_config(
    page_title="Client Data Operations Hub",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #f4f6f5; }
        [data-testid="stSidebar"] { background: #13231d; }
        [data-testid="stSidebar"] * { color: #edf5ef; }
        .hero { background: linear-gradient(120deg, #13231d 0%, #245543 70%, #afc96b 140%); border-radius: 18px; padding: 28px 32px; margin-bottom: 22px; color: white; }
        .hero h1 { margin: 0 0 6px 0; font-size: 2.25rem; }
        .hero p { margin: 0; color: #d7e5da; font-size: 1.05rem; }
        div[data-testid="stMetric"] { background: white; border: 1px solid #dfe7e1; border-radius: 14px; padding: 14px 16px; }
        .section-label { color: #35765c; font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; margin: 20px 0 8px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


def database_path() -> Path:
    return Path(os.environ.get("CLIENT_DATA_OPS_DB_PATH", str(DEFAULT_DATABASE))).resolve()


@st.cache_data(show_spinner=False)
def load_data(path: str, modified_at: float) -> dict:
    connection = duckdb.connect(path, read_only=True)
    try:
        scorecard = connection.execute("SELECT * FROM gold_client_scorecard").fetchdf().iloc[0].to_dict()
        accounts = connection.execute(
            """SELECT account_name, plan, account_status, paid_revenue, overdue_invoices,
                      open_tickets, support_sla_rate, health_segment
               FROM gold_account_health
               ORDER BY overdue_invoices DESC, open_tickets DESC, paid_revenue DESC"""
        ).fetchdf()
        daily = connection.execute(
            """SELECT metric_date, billed_revenue, paid_revenue, overdue_invoices, open_tickets
               FROM gold_daily_operations ORDER BY metric_date"""
        ).fetchdf()
    finally:
        connection.close()
    return {"scorecard": scorecard, "accounts": accounts, "daily": daily}


def money(value: object) -> str:
    return f"${float(value):,.2f}"


path = database_path()
if not path.exists():
    st.error("Warehouse not found. Run `python -m client_data_ops` first.")
    st.stop()

manifest_path = path.parent.parent / "service_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
data = load_data(str(path), path.stat().st_mtime)
scorecard = data["scorecard"]

with st.sidebar:
    st.markdown("## Client DataOps")
    st.caption("Managed delivery evidence")
    st.divider()
    st.markdown("**Client**")
    st.write(manifest.get("client_id", scorecard.get("client_id", "unknown")))
    st.markdown("**Delivery status**")
    st.success(manifest.get("delivery_status", "unknown").title())
    st.markdown("**Quality gate**")
    st.write(f"{manifest.get('quality_gate', {}).get('score', 0)} / 100")
    st.caption(f"Warehouse: `{path.name}`")

st.markdown(
    """
    <div class="hero">
        <h1>Client Data Operations Hub</h1>
        <p>A trusted delivery layer between client exports and business decisions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Client scorecard · March 2025</div>', unsafe_allow_html=True)
metrics = st.columns(4)
metrics[0].metric("Active MRR", money(scorecard["mrr"]))
metrics[1].metric("Collected revenue", money(scorecard["paid_revenue"]))
metrics[2].metric("Collection rate", f"{float(scorecard['collection_rate']):.1f}%")
metrics[3].metric("Support SLA", f"{float(scorecard['support_sla_rate']):.1f}%")

st.markdown('<div class="section-label">Delivery review</div>', unsafe_allow_html=True)
left, right = st.columns([1.4, 1])
with left:
    st.subheader("Revenue operations trend")
    daily = data["daily"].set_index("metric_date")
    st.line_chart(daily[["billed_revenue", "paid_revenue"]], y_label="USD", height=310)
with right:
    st.subheader("Client risks")
    risk = data["accounts"].query("health_segment == 'needs_attention'").copy()
    risk = risk.rename(columns={"account_name": "Account", "overdue_invoices": "Overdue invoices", "open_tickets": "Open tickets"})
    st.dataframe(risk[["Account", "Overdue invoices", "Open tickets"]], width="stretch", hide_index=True)

tab_accounts, tab_quality = st.tabs(["Account health", "Quality and SLA"])
with tab_accounts:
    st.subheader("Account health for Customer Success")
    accounts = data["accounts"].copy()
    accounts["paid_revenue"] = accounts["paid_revenue"].map(money)
    accounts = accounts.rename(
        columns={
            "account_name": "Account",
            "plan": "Plan",
            "account_status": "Status",
            "paid_revenue": "Paid revenue",
            "overdue_invoices": "Overdue invoices",
            "open_tickets": "Open tickets",
            "support_sla_rate": "Support SLA",
            "health_segment": "Health segment",
        }
    )
    st.dataframe(accounts, width="stretch", hide_index=True)
with tab_quality:
    st.subheader("Evidence attached to this delivery")
    quality = manifest.get("quality_gate", {})
    if quality.get("status") == "passed":
        st.success("Quality gate passed. Delivery is accepted.")
    checks = quality.get("checks", {})
    rows = [{"Check": name.replace("_", " ").title(), "Incidents": value} for name, value in checks.items()]
    st.dataframe(rows, width="stretch", hide_index=True)
    sla = manifest.get("sla", {})
    st.write(f"SLA target: {sla.get('target_hours', 'n/a')} hours")
    st.write(f"SLA status: {sla.get('status', 'unknown').replace('_', ' ').title()}")
