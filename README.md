# Data Engineering Journey

An open, reproducible workspace for strengthening my data engineering practice and documenting the systems I build along the way.

## Purpose

This repository records practical work in:

- Python and SQL
- Docker and Git
- Cloud concepts and data storage
- Data modeling and transformations with dbt
- Workflow orchestration with Airflow
- Data processing with PySpark
- Data quality, observability, and CI/CD

It includes technical notes, decisions, learning logs, and original projects. It is not a copy or mirror of any course repository.

## Current progress

- Development environment configured and verified
- First batch pipeline completed with Python, DuckDB, and SQL
- Local e-commerce lakehouse completed with a Medallion architecture
- Next: add dbt and automated validation for analytical models

Progress is updated as each deliverable is completed and tested.

## Repository structure

```text
.
├── learning-log/       # Learning notes and progress updates
├── notes/              # Short, sanitized technical notes
├── projects/           # Original projects
├── roadmap/            # Learning plan
├── resources.md        # External learning resources
└── ATTRIBUTION.md      # Sources and attribution
```

## Roadmap

See [roadmap/30-day-plan.md](roadmap/30-day-plan.md) for the working plan and planned deliverables.

## Projects

Each original project includes its own README with:

- The problem it addresses
- Architecture and data flow
- Data sources and licensing
- Technology choices
- Setup and execution instructions
- Tests and validation checks
- Results, costs, and limitations

The project template is available at [projects/README.md](projects/README.md).

## Learning sources

External sources are documented in [resources.md](resources.md) and [ATTRIBUTION.md](ATTRIBUTION.md). Original authors and licenses are preserved.

## Privacy and reproducibility

Credentials, tokens, `.env` files, personal paths, private configuration, and large datasets are not published. Data is downloaded from its official source when required.

## License

The license for this repository will be defined when the first stable version is published. Third-party materials retain their original licenses and are not covered by a future license for my notes or code.

## Featured projects

[NYC Taxi Data Pipeline](projects/nyc-taxi-pipeline/) is a reproducible batch pipeline that downloads public data, validates it, and produces daily metrics with DuckDB.

[E-Commerce Lakehouse](projects/ecommerce-lakehouse/) is a local, reproducible lakehouse that generates synthetic e-commerce data and transforms it into Bronze, Silver, and Gold layers with DuckDB and Parquet.
