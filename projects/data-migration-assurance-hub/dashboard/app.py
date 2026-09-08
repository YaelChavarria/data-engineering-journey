"""Migration Control Room for the Data Migration Assurance Hub."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_DIR / "data" / "warehouse" / "migration_assurance.duckdb"

st.set_page_config(
    page_title="Migration Control Room",
    page_icon=":material/transfer_within_a_station:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #f3f1ea; }
        [data-testid="stSidebar"] { background: #18221e; }
        [data-testid="stSidebar"] * { color: #e9eee8; }
        .masthead { align-items: end; border-bottom: 1px solid #c9c8bf; display: flex; justify-content: space-between; margin-bottom: 24px; padding: 12px 0 18px; }
        .masthead h1 { color: #18221e; font-family: 'IBM Plex Sans', sans-serif; font-size: 2.15rem; letter-spacing: -.05em; margin: 0; }
        .masthead p { color: #657069; font-family: 'IBM Plex Mono', monospace; font-size: .75rem; margin: 0; }
        .decision { border-left: 7px solid #b24a42; background: #fffaf5; border-radius: 2px; padding: 22px 25px; margin: 12px 0 24px; }
        .decision.ready { border-left-color: #4f8064; }
        .decision h2 { color: #18221e; font-family: 'IBM Plex Sans', sans-serif; font-size: 1.8rem; letter-spacing: -.04em; margin: 0 0 5px; }
        .decision p { color: #52605a; margin: 0; }
        .section-label { color: #526b79; font-family: 'IBM Plex Mono', monospace; font-size: .68rem; font-weight: 700; letter-spacing: .12em; margin: 22px 0 8px; text-transform: uppercase; }
        div[data-testid="stMetric"] { background: #fff; border: 1px solid #d8d8cf; border-radius: 2px; padding: 12px 15px; }
        .stDataFrame { border: 1px solid #d8d8cf; }
        .mono { color: #657069; font-family: 'IBM Plex Mono', monospace; font-size: .76rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def database_path() -> Path:
    return Path(os.environ.get("DATA_MIGRATION_DB_PATH", str(DEFAULT_DATABASE))).resolve()


@st.cache_data(show_spinner=False)
def load_data(path: str, modified_at: float) -> dict:
    connection = duckdb.connect(path, read_only=True)
    try:
        reconciliation = connection.execute(
            """SELECT entity, source_count, target_count, row_count_delta,
                      source_amount, target_amount, amount_delta, reconciliation_status
               FROM gold_reconciliation ORDER BY entity"""
        ).fetchdf()
        exceptions = connection.execute(
            """SELECT entity, record_key, issue_type, severity, description, owner, status
               FROM gold_exception_queue
               ORDER BY CASE severity WHEN 'high' THEN 1 ELSE 2 END, entity, record_key"""
        ).fetchdf()
        readiness = connection.execute("SELECT * FROM gold_cutover_readiness").fetchdf().iloc[0].to_dict()
    finally:
        connection.close()
    return {"reconciliation": reconciliation, "exceptions": exceptions, "readiness": readiness}


path = database_path()
if not path.exists():
    st.error("Warehouse not found. Run `python -m data_migration_assurance` first.")
    st.stop()

manifest_path = path.parent.parent / "migration_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
data = load_data(str(path), path.stat().st_mtime)
readiness = data["readiness"]
decision = readiness["cutover_decision"]
last_run = manifest.get("quality_gate", {}).get("generated_at_utc", "not available").replace("T", " ")[:19]

with st.sidebar:
    st.markdown("## Migration Control Room")
    st.caption("Data Migration Assurance Hub")
    st.divider()
    st.markdown("**Migration**")
    st.write(manifest.get("migration_id", readiness.get("migration_id", "unknown")))
    st.markdown("**Wave**")
    st.write(manifest.get("wave", readiness.get("wave", "03")))
    st.markdown("**Environment**")
    st.write("Demo / synthetic snapshots")
    st.divider()
    st.caption("Source: Legacy CRM and Billing")
    st.caption("Target: Analytics Warehouse")

st.markdown(
    """
    <div class="masthead">
        <div><p class="section-label">Migration assurance</p><h1>Migration Control Room</h1></div>
        <p>LAST RUN · {last_run} / UTC</p>
    </div>
    """,
    unsafe_allow_html=True,
)

decision_class = "ready" if decision == "READY" else ""
st.markdown(
    f"""
    <div class="decision {decision_class}">
        <h2>{decision} FOR CUTOVER</h2>
        <p>{readiness['decision_reason']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Decision evidence</div>', unsafe_allow_html=True)
metrics = st.columns(4)
source_rows = sum(manifest.get("quality_gate", {}).get("source_rows", {}).values())
target_rows = sum(manifest.get("quality_gate", {}).get("target_rows", {}).values())
metrics[0].metric("Source records", f"{source_rows:,}")
metrics[1].metric("Target records", f"{target_rows:,}")
metrics[2].metric("High exceptions", f"{int(readiness['high_exceptions']):,}")
metrics[3].metric("Entities passed", f"{int(readiness['passed_entities'])} / {int(readiness['entity_count'])}")

st.markdown('<div class="section-label">Reconciliation</div>', unsafe_allow_html=True)
reconciliation = data["reconciliation"].copy()
reconciliation["source_amount"] = reconciliation["source_amount"].map(lambda value: "-" if value != value else f"${float(value):,.2f}")
reconciliation["target_amount"] = reconciliation["target_amount"].map(lambda value: "-" if value != value else f"${float(value):,.2f}")
reconciliation["amount_delta"] = reconciliation["amount_delta"].map(lambda value: f"${float(value):,.2f}")
reconciliation = reconciliation.rename(
    columns={
        "entity": "Entity",
        "source_count": "Source rows",
        "target_count": "Target rows",
        "row_count_delta": "Row delta",
        "source_amount": "Source amount",
        "target_amount": "Target amount",
        "amount_delta": "Amount delta",
        "reconciliation_status": "Status",
    }
)
st.dataframe(reconciliation, width="stretch", hide_index=True)

tab_exceptions, tab_checklist = st.tabs(["Exception queue", "Cutover checklist"])
with tab_exceptions:
    st.markdown('<div class="section-label">Open issues requiring an owner</div>', unsafe_allow_html=True)
    exceptions = data["exceptions"].rename(
        columns={
            "entity": "Entity",
            "record_key": "Record key",
            "issue_type": "Issue",
            "severity": "Severity",
            "description": "Description",
            "owner": "Owner",
            "status": "Status",
        }
    )
    if exceptions.empty:
        st.success("No open exceptions. Migration can proceed to sign-off.")
    else:
        st.dataframe(exceptions, width="stretch", hide_index=True)
with tab_checklist:
    st.markdown('<div class="section-label">Go / no-go controls</div>', unsafe_allow_html=True)
    checklist = manifest.get("checklist", [])
    checklist_rows = [
        {"Check": item["check"].replace("_", " ").title(), "Status": item["status"].upper(), "Owner": item["owner"]}
        for item in checklist
    ]
    st.dataframe(checklist_rows, width="stretch", hide_index=True)
    st.caption("A HOLD decision is intentional when unresolved high-severity issues remain.")
