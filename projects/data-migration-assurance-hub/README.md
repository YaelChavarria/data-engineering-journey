# Data Migration Assurance Hub

An operational control room for client data migrations. It helps a migration team answer the question that matters before go-live:

> Can we prove that the data arrived complete, correct and reconciled?

The project simulates **Meridian Systems**, a company moving data from a legacy CRM and billing platform into an analytics warehouse. The default review scenario contains controlled discrepancies so the system intentionally returns `HOLD FOR CUTOVER` instead of hiding risk.

This is a synthetic case study. It demonstrates a delivery process and technical controls; it does not claim production migration experience.

## What the project delivers

- Source and target snapshot intake
- Typed Bronze and Silver layers
- Row-count and monetary reconciliation
- Exception queue with severity and owner
- Cutover readiness decision
- Go/no-go checklist
- Quality report and migration manifest
- Streamlit Migration Control Room
- dbt tests for reconciliation, exceptions and decision domains

## Architecture

```text
Legacy CRM and Billing snapshots       Target warehouse snapshot
              |                                  |
              +---------- Intake ---------------+
                             |
                  Source quality gate
                             |
                 Bronze source/target Parquet
                             |
                  Silver typed snapshots
                             |
             dbt reconciliation and exceptions
                             |
             Cutover readiness / manifest / UI
```

The pipeline separates source quality from migration assurance. A malformed source export fails intake. A difference between a valid source and target snapshot becomes a visible exception that can block cutover.

## Control Room preview

The dashboard is designed as an operations interface rather than a generic KPI dashboard:

- A single `READY` or `HOLD` decision at the top
- Source-to-target reconciliation by entity
- Blocking exception queue with owner and next action
- Cutover checklist with Finance, Data and Business ownership
- Demo/synthetic environment clearly labelled

## Technology

`Python 3.12` `DuckDB` `Parquet` `dbt-duckdb` `Streamlit` `Docker` `GitHub Actions`

## Run locally

Requirements: Python 3.12 or higher. Internet is not required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m data_migration_assurance
```

The default `review` scenario generates source and target snapshots, runs the source quality gate, builds the dbt models and writes the migration manifest.

Start the control room:

```powershell
streamlit run dashboard/app.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Run a clean scenario that can reach `READY`:

```powershell
python -m data_migration_assurance --scenario clean
```

Use an existing pair of snapshots:

```powershell
python -m data_migration_assurance --skip-generate
```

## Output package

```text
data/
├── source/                   # Legacy source snapshots
├── target/                   # Post-migration target snapshots
├── bronze/                   # Source-shaped Parquet
├── silver/                   # Typed source and target tables
├── gold/                     # Reconciliation and readiness models
├── warehouse/
│   └── migration_assurance.duckdb
├── quality_report.json       # Intake quality evidence
└── migration_manifest.json  # Decision, exceptions, SLA and checklist
```

Generated data and local databases are ignored by Git.

## Latest review run

The default review scenario generates 60 accounts, 180 invoices, 240 transactions and 180 contacts in the source snapshot. It introduces controlled target differences that produce a visible `HOLD` decision, including missing records, a duplicate key and a monetary mismatch.

The values are deterministic and reproducible. They are not production metrics.

## Documentation

- [Migration brief](docs/migration-brief.md)
- [Delivery plan](docs/delivery-plan.md)
- [Reconciliation contract](docs/reconciliation-contract.md)
- [Cutover runbook](docs/runbook.md)
- [Security and privacy](docs/security.md)
- [Recruiter-facing LinkedIn post](docs/linkedin-post.md)

## Limitations and next steps

- The snapshots are local CSVs; a production engagement would use governed object storage, SFTP or APIs.
- The demo compares a prepared target snapshot; a production migration would also manage transformation jobs and cutover windows.
- Exceptions are generated at record level but do not yet include a client ticketing integration.
- The local SLA clock measures pipeline runtime; production SLAs would include intake, review and sign-off timestamps.
- Production work would require access controls, retention rules, audit logs and a data-processing agreement.
