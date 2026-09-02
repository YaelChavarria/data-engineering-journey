# Revenue Protection Data Platform

An end-to-end, local-first data platform for a simulated North American e-commerce company. It helps Finance and Operations answer:

> Where are we losing revenue, and what should Operations prioritize today?

This is a simulated case study. It uses deterministic synthetic source data and does not claim production business savings.

## Business outcome

The platform turns orders, payments, shipments, and refunds into decision-ready signals:

- Net revenue after processed refunds
- Revenue leakage by cause and priority
- Late-delivery rate and affected orders
- Refund exposure and operational trend
- Tested daily metrics for Finance and Operations

## Architecture

```text
Deterministic source CSVs
        |
        v
Bronze: raw source snapshots in Parquet
        |
        v
Silver: typed, normalized and referentially checked tables
        |
        v
Gold: dbt facts, dimensions and decision models
        |
        +--> Streamlit control tower
        +--> pipeline_summary.json
```

The project runs locally with DuckDB and Parquet to keep it reproducible and inexpensive. The boundaries map to a cloud architecture without requiring cloud credentials.

## What is included

- Python ingestion and deterministic source generator
- Bronze, Silver and Gold Medallion layers
- dbt incremental order fact with `delete+insert` strategy
- Revenue leakage model for refunds and late deliveries
- Daily Operations model with late-delivery rate
- Referential integrity checks before dbt runs
- dbt tests for keys, relationships, domains and critical metrics
- Streamlit dashboard for executive and operational views
- Dockerfile and GitHub Actions CI
- Product requirements, architecture, data contract and incident runbook

## Technology

`Python 3.12` `DuckDB` `Parquet` `dbt-duckdb` `Streamlit` `Docker` `GitHub Actions`

## Latest local run

The deterministic default run produced 209 source records in approximately 16 seconds, passed 23 dbt data tests and recorded zero referential-quality incidents. It calculated `$5,785.30` in completed net revenue and `$731.85` in simulated revenue leakage.

## Models

- `gold_fact_order`: one row per order with gross revenue, refunds, net revenue, delivery status and leakage amount
- `gold_operations_daily`: daily operational KPIs for Finance and Operations
- `gold_revenue_leakage`: leakage grouped by cause with affected orders and priority
- `gold_daily_sales`: daily net revenue and supporting commercial metrics
- `gold_category_sales`: units and gross revenue by category
- `gold_customer_sales`: customer order count and net lifetime value
- `gold_product_sales`: units and gross revenue by product

## Run locally

Requirements: Python 3.12 or higher. Internet is not required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m ecommerce_lakehouse
```

The default command generates 36 deterministic orders, runs ingestion, builds Silver, executes dbt, runs data tests, and writes the local warehouse and summary.

Start the dashboard:

```powershell
streamlit run dashboard/app.py
```

Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

Simulate an append-only incremental load:

```powershell
python -m ecommerce_lakehouse --order-count 40 --incremental
```

## Generated files

```text
data/
├── source/              # Generated source CSVs
├── bronze/              # Raw Parquet snapshots
├── silver/              # Typed and validated Parquet
├── gold/                # dbt analytical Parquet
├── warehouse/
│   └── ecommerce.duckdb
└── pipeline_summary.json
```

Generated data and local databases are ignored by Git. The source generator makes every run reproducible.

## Data quality and operating assumptions

The pipeline fails before dbt when it finds duplicate dimension keys or orphan orders, order items, products, shipments or refunds. dbt adds uniqueness, not-null, relationship, accepted-value and daily-grain tests.

The incremental example assumes an append-only order source and uses `order_id` as the watermark. A correction to an existing order requires a full refresh or a future change-data-capture strategy. This is intentional and documented rather than hidden.

## Product documentation

- [Product requirements](docs/PRD.md)
- [Architecture and data flow](docs/architecture.md)
- [Data contract](docs/data-contract.md)
- [Incident runbook](docs/runbook.md)
- [Decision log](docs/decision-log.md)
- [Recruiter-facing LinkedIn post](docs/linkedin-post.md)

## Limitations and next steps

- Replace the deterministic generator with authenticated source connectors
- Store Bronze in S3, GCS or Azure Blob
- Run orchestration on Airflow, Dagster or Prefect
- Add freshness monitoring and notification delivery
- Add actual unit economics and warehouse cost data
- Add CDC handling for updates to existing orders

## License and attribution

All demonstration records are synthetic and owned by this project. No customer, payment or production data is included.
