# E-Commerce Lakehouse

A local, reproducible lakehouse for analyzing e-commerce sales. The project uses synthetic data, DuckDB, Parquet, and a Medallion architecture.

## Business problem

The business team needs a reliable source for revenue, completed orders, best-selling products, and customer lifetime value. Operational data is separated across customers, products, orders, order lines, and payments.

## Arquitectura

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
Gold: dimensions, facts, and analytical metrics
       |
       v
Future dashboard: Metabase or Streamlit
```

DuckDB maintains the local catalog and queries Parquet. This makes it possible to practice lakehouse patterns without a cloud account or cluster.

## Layers and models

- `bronze_*`: DuckDB-typed copy of each source file
- `silver_*`: normalized dates, amounts, and keys with explicit types
- `gold_dim_customer`: customer dimension
- `gold_dim_product`: product dimension
- `gold_fact_order`: one row per order with amount and completion status
- `gold_daily_sales`: orders, revenue, and average order value by day
- `gold_category_sales`: units and revenue by category
- `gold_customer_sales`: orders and lifetime value by customer

Cancelled orders remain in the fact table for traceability, but are excluded from revenue metrics.

## Requirements

- Python 3.12 o superior.
- Internet is not required because the demonstration source is generated locally.

## Installation and execution

Desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m ecommerce_lakehouse
```

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

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests use a temporary directory, check all three layers, validate table relationships, and verify that cancelled orders do not generate revenue.

## Docker

```powershell
docker build -t ecommerce-lakehouse .
docker run --rm -v "${PWD}\data:/app/data" ecommerce-lakehouse
```

## Data quality

El pipeline comprueba:

- No duplicate customer or product keys
- No orders without a customer
- No order lines without an order or product
- Positive quantities and non-negative amounts
- Order statuses within the expected domain

Execution fails if a referential check returns any violations.

## Decisions and next steps

- A small synthetic source keeps the project inexpensive and reproducible.
- DuckDB replaces a managed warehouse initially and keeps execution local.
- The next iteration could add dbt, MinIO, incremental loads, and a dashboard.
- A cloud version could move Bronze to Azure Blob or S3 and Gold to Snowflake, BigQuery, or Databricks.
