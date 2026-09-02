# Architecture and Data Flow

## Components

| Layer | Component | Responsibility |
|---|---|---|
| Source | `generator.py` | Creates deterministic orders, payments, shipments and refunds |
| Bronze | Python + Parquet | Preserves source-shaped snapshots |
| Silver | Python + DuckDB | Casts types, normalizes values and filters invalid records |
| Gold | dbt-duckdb | Applies documented business logic and tests |
| Serving | Streamlit | Presents decision-ready metrics |
| Observability | `pipeline_summary.json` | Records row counts, quality checks, mode and duration |

## Data flow

```text
customers.csv     orders.csv       payments.csv
products.csv      order_items.csv  shipments.csv  refunds.csv
       \              |                    /
        +-------- Bronze Parquet --------+
                       |
             Python + DuckDB validation
                       |
              Silver typed source tables
                       |
                     dbt
                       |
     gold_fact_order + daily decision models
                       |
           Streamlit control tower / Parquet
```

## Grain and ownership

- Source and Bronze retain source-system grain.
- `gold_fact_order` is one row per `order_id`.
- `gold_operations_daily` is one row per `order_date`.
- `gold_revenue_leakage` is one row per leakage cause.

Python owns ingestion and Silver transformations. dbt owns Gold business logic. The dashboard reads only Gold tables and the pipeline summary.

## Incremental behavior

`gold_fact_order` is incremental with `order_id` as the watermark. New IDs are loaded with `delete+insert`; aggregate models rebuild from the current fact table. This is safe for the demonstration's append-only source but does not capture late-arriving corrections to existing IDs.

## Cloud mapping

The local design can map to object storage plus a managed warehouse:

| Local | Cloud equivalent |
|---|---|
| Local Bronze Parquet | S3, GCS or Azure Blob |
| DuckDB | BigQuery, Snowflake, Redshift or Databricks SQL |
| Local command | Airflow, Dagster or Prefect task |
| Streamlit | Streamlit Cloud or an internal BI tool |
