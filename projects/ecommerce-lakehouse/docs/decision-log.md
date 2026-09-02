# Decision Log

## 1. Local-first execution

**Decision:** Use DuckDB and Parquet instead of a managed cloud warehouse for the MVP.

**Reason:** The project must be reproducible without credentials or unexpected cloud spend. The layer boundaries still map cleanly to S3, BigQuery, Snowflake or Databricks.

## 2. Deterministic synthetic data

**Decision:** Generate source records locally with fixed rules.

**Reason:** The portfolio needs repeatable tests and must not expose personal, customer or payment data. The README labels the case study as simulated.

## 3. Revenue leakage definition

**Decision:** Define leakage as processed refunds plus shipping cost for completed late deliveries.

**Reason:** This is explainable to Finance and Operations and avoids presenting a speculative machine-learning score as a financial fact.

## 4. Order ID watermark

**Decision:** Use `order_id` as the incremental watermark for the MVP.

**Reason:** The generated source is append-only. The limitation is explicit: historical corrections require a full refresh or CDC.

## 5. Separate executive and operational views

**Decision:** Keep the control tower focused on leakage and add supporting product/customer views.

**Reason:** The primary experience should answer the stated business question rather than become a generic sales dashboard.
