# Incident Runbook

## Intake rejected

1. Confirm the delivery ID and source files received.
2. Compare columns and accepted domains with `docs/data-contract.md`.
3. Notify the client owner with the failed check and an example record.
4. Do not publish Gold outputs from the failed delivery.
5. Re-run after the client sends a corrected export.

## dbt build failed

1. Preserve the failed run information and error output.
2. Check whether the source contract changed.
3. Run `python -m unittest discover -s tests -v`.
4. Rebuild from a clean local warehouse when validating recovery.
5. Record the root cause and decision in the delivery notes.

## Dashboard unavailable

1. Confirm `data/warehouse/client_delivery.duckdb` exists.
2. Run `python -m client_data_ops` to produce a clean delivery.
3. Confirm `data/service_manifest.json` exists and is accepted.
4. Restart Streamlit and clear its cached data if necessary.

## Recovery principle

The demonstration uses deterministic source files, so recovery is a full replay from intake. A production service would preserve immutable source snapshots, isolate failed deliveries and replay the last known-good version without overwriting client history.
