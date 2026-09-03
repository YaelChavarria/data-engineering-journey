# Client Data Operations Hub

A reproducible blueprint for a managed data service. It demonstrates how an external data partner can receive client exports, validate them against an agreed contract, produce decision-ready deliverables, and provide evidence that the delivery met its quality and SLA gates.

The simulated client is **Atlas SaaS**, a North American subscription business. The system is intentionally local and uses deterministic synthetic data. It is a service blueprint, not a claim of production client work.

## The service promise

> The client should not have to manage every data task internally to trust its numbers. We take the agreed inputs, operate the pipeline, communicate exceptions, and return a documented delivery package.

The delivery answers:

- How much recurring revenue is active?
- What is billed, collected and overdue?
- Which accounts need attention?
- Is support meeting its response expectation?
- Did this delivery pass its data quality and SLA gates?

## Client-facing deliverables

- Executive client scorecard
- Account health table for Customer Success
- Daily operations table for recurring reporting
- Data quality report with all checks and evidence
- Service manifest with delivery ID, period, SLA and status
- Runbook for failed deliveries and recovery

## Architecture

```text
Client exports
    |
    v
Intake and contract validation
    |
    +--> Quality gate: reject the delivery if critical checks fail
    |
    v
Bronze: source-shaped Parquet snapshots
    |
    v
Silver: typed, normalized client tables
    |
    v
Gold: dbt scorecard, account health and daily operations
    |
    +--> Client delivery package
    +--> Streamlit service dashboard
    +--> Quality report and SLA manifest
```

## What this project demonstrates

- Requirements translated into acceptance criteria
- A repeatable client onboarding and delivery workflow
- Data contracts and quality gates before business reporting
- Clear ownership between intake, transformation and delivery review
- Finance, Customer Success and Operations metrics in one scorecard
- Evidence for every delivery, not just a screenshot of a dashboard
- A realistic failure and recovery path

## Technology

`Python 3.12` `DuckDB` `Parquet` `dbt-duckdb` `Streamlit` `Docker` `GitHub Actions`

## Run locally

Requirements: Python 3.12 or higher. Internet is not required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m client_data_ops
```

The command creates a deterministic Atlas SaaS export, runs the quality gate, builds dbt models and writes the service manifest.

Start the service dashboard:

```powershell
streamlit run dashboard/app.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Use existing exports instead of generating the sample:

```powershell
python -m client_data_ops --skip-generate
```

## Output package

```text
data/
├── source/                 # Client export intake
├── bronze/                 # Immutable source-shaped snapshots
├── silver/                 # Typed and validated tables
├── gold/                   # Client deliverables in Parquet
├── warehouse/
│   └── client_delivery.duckdb
├── quality_report.json     # Quality gate evidence
└── service_manifest.json   # Delivery, SLA and output manifest
```

Generated files and local databases are ignored by Git. The source generator makes the delivery repeatable without exposing real client data.

## Latest local delivery

The default delivery generates 24 accounts, 54 invoices, 72 support tickets and 35 account events. It produces a passed quality gate with a score of 100 and an accepted delivery manifest within the 24-hour target.

Run the command locally to record the exact runtime for the current machine; runtime is intentionally not treated as a business outcome.

## Documentation

- [Service catalogue](docs/service-catalog.md)
- [Engagement plan](docs/engagement-plan.md)
- [Data contract](docs/data-contract.md)
- [Security and privacy](docs/security.md)
- [Incident runbook](docs/runbook.md)
- [Recruiter-facing LinkedIn post](docs/linkedin-post.md)

## Limitations and next steps

- The client export is generated locally instead of arriving through SFTP, object storage or an API.
- The project uses one simulated client; a production service would isolate clients by account and storage boundary.
- The quality gate fails the entire delivery; a future version could quarantine non-critical rows and produce a partial-delivery protocol.
- The SLA clock is represented in the manifest; production scheduling and alerting would be handled by an orchestrator.
- A production implementation would add secrets management, access logging, retention policies and formal data-processing agreements.
