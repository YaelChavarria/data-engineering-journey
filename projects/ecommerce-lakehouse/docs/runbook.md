# Incident Runbook

## Pipeline fails before dbt

1. Read the exception and inspect `data/pipeline_summary.json` from the previous successful run.
2. Check the relevant source CSV for missing keys, invalid dates or negative amounts.
3. Run `python -m unittest discover -s tests -v`.
4. Remove generated `data/` and run a full refresh if the local warehouse is stale.

## dbt test failure

1. Run `dbt build --project-dir dbt --profiles-dir dbt --target local` from the project directory.
2. Identify whether the failure is a key, relationship, domain or metric issue.
3. Never weaken a test to make CI green without recording the business reason in `docs/decision-log.md`.

## Dashboard cannot open the warehouse

1. Run `python -m ecommerce_lakehouse` from the project directory.
2. Confirm `data/warehouse/ecommerce.duckdb` exists.
3. If using another database, set `ECOMMERCE_DB_PATH` to its absolute path.
4. Restart Streamlit to clear the cached query result.

## Recovery strategy

The demonstration is local and deterministic. The recovery action is a full refresh, which rebuilds Bronze, Silver and Gold from source CSVs. A production version would retain immutable Bronze snapshots and replay from a known-good partition.
