# Projects

This directory contains original projects, not copies of course exercises.

## Project requirements

Each project should document:

- The project name and business problem
- An architecture diagram
- The data flow
- Data sources and licensing
- The technical stack and key decisions
- Setup and execution instructions
- Environment variables in `.env.example`, without real values
- Tests or data quality checks
- Screenshots, metrics, and results
- Limitations and possible improvements

## Projects

[NYC Taxi Data Pipeline](nyc-taxi-pipeline/) is a public-data batch pipeline built with Python, DuckDB, and SQL.

[Revenue Protection Data Platform](ecommerce-lakehouse/) is a local-first e-commerce platform that turns orders, payments, shipments and refunds into tested revenue-leakage and operational-priority signals. It includes product documentation, a control-tower dashboard, incremental dbt models and CI.

[Client Data Operations Hub](client-data-ops-hub/) is a managed data service blueprint that validates client exports, blocks unsafe deliveries, produces recurring KPI deliverables, and records quality and SLA evidence for every handoff.
