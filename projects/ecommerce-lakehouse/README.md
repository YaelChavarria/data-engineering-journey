# E-Commerce Lakehouse

A local, reproducible lakehouse for analyzing e-commerce sales. Version 2 uses synthetic data, DuckDB, Parquet, dbt, and a Streamlit dashboard in a Medallion architecture.

## Business problem

The business team needs a reliable source for revenue, completed orders, best-selling products, and customer lifetime value. Operational data is separated across customers, products, orders, order lines, and payments.

## Architecture

```text
CSV source system
       |
       v
Bronze: raw CSV -> Parquet, no business changes
       |
       v
Silver: typed, normalized, and filtered invalid records
       |
       v
Gold: dimensions, facts, and analytical metrics (dbt)
       |
       v
Executive dashboard: Streamlit
```

DuckDB maintains the local warehouse and queries Parquet. dbt materializes and tests the Gold models. This makes it possible to practice lakehouse patterns without a cloud account or cluster.

## Layers and models

- `bronze_*`: DuckDB-typed copy of each source file
- `silver_*`: normalized dates, amounts, and keys with explicit types
- `gold_dim_customer`: customer dimension
- `gold_dim_product`: product dimension
- `gold_fact_order`: one row per order with amount and completion status
- `gold_daily_sales`: orders, revenue, and average order value by day
- `gold_category_sales`: units and revenue by category
- `gold_customer_sales`: orders and lifetime value by customer
- `gold_product_sales`: units and revenue by product

Cancelled orders remain in the fact table for traceability, but are excluded from revenue metrics.

## Requirements

- Python 3.12 or higher.
- Internet is not required because the demonstration source is generated locally.

## Installation and execution

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m ecommerce_lakehouse
```

The default execution performs a `full-refresh`: it regenerates the demo source, rebuilds Bronze and Silver, and rebuilds Gold with dbt. dbt also runs the tests defined in `dbt/models/schema.yml`.

Execution generates deterministic synthetic data and creates:

```text
data/
├── source/              # Locally generated input CSV
├── bronze/              # Raw Parquet
├── silver/              # Clean Parquet
├── gold/                # Analytical Parquet
├── warehouse/
│   └── ecommerce.duckdb
└── pipeline_summary.json
```

To process existing CSV files:

```powershell
python -m ecommerce_lakehouse --skip-generate
```

## Incremental loads

To simulate an incremental load, generate a source with more orders while preserving the existing Gold fact table:

```powershell
python -m ecommerce_lakehouse --order-count 40 --incremental
```

The `gold_fact_order` model incorporates only orders with a new `order_id`. Aggregate tables are rebuilt from the updated fact table. This example assumes an append-only source; historical changes require a merge strategy or a full refresh.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests use a temporary directory, check all three layers, validate table relationships, verify that cancelled orders do not generate revenue, and confirm that dbt materializes the Gold models.

## Dashboard

After running the pipeline, start the dashboard from this directory:

```powershell
streamlit run dashboard/app.py
```

The dashboard shows net revenue, completed orders, average order value, active customers, daily revenue, category revenue, product ranking, customer lifetime value, and quality checks. To use another warehouse:

```powershell
$env:ECOMMERCE_DB_PATH = "C:\ruta\ecommerce.duckdb"
streamlit run dashboard/app.py
```

## Docker

```powershell
docker build -t ecommerce-lakehouse .
docker run --rm -v "${PWD}\data:/app/data" ecommerce-lakehouse
```

## Data quality

The pipeline checks:

- No duplicate customer or product keys
- No orders without a customer
- No order lines without an order or product
- Positive quantities and non-negative amounts
- Order statuses within the expected domain
- dbt tests for keys, relationships, accepted values, and daily uniqueness

Execution fails if a referential check returns any violations.

## Decisions and next steps

- A small synthetic source keeps the project inexpensive and reproducible.
- DuckDB replaces a managed warehouse initially and keeps execution local.
- The local architecture is ready for MinIO or cloud object storage.
- A cloud version could move Bronze to Azure Blob or S3 and Gold to Snowflake, BigQuery, or Databricks.

This version already includes dbt, incremental loads, and the local dashboard. The recommended next evolution is to run Bronze in object storage and automate the pipeline with Kestra or Airflow.
