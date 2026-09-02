# Product Requirements

## Context

The simulated e-commerce business has commercial and operational data in separate source systems. Finance can see sales, while Operations can see shipments and refunds, but there is no consistent view of revenue leakage.

## Problem statement

Decision-makers need a daily, trusted answer to two questions:

1. How much revenue was retained after refunds?
2. Which operational issue should be investigated first?

## Users and decisions

| User | Decision enabled |
|---|---|
| Finance lead | Reconcile gross, refunded and net revenue |
| Operations lead | Prioritize late-delivery and refund causes |
| Data team | Verify freshness, integrity and pipeline health |

## MVP scope

- Ingest orders, payments, shipments and refunds
- Enforce typed and referentially valid Silver tables
- Produce one-row-per-order and daily operational models
- Rank leakage causes by amount and priority
- Expose the result in a dashboard
- Document ownership, assumptions, quality checks and incidents

## Out of scope

- Real payment provider integration
- Automated refund decisions
- Personalization or customer-facing features
- Production cloud deployment
- Claims about real-world savings

## Metric definitions

- **Gross revenue:** order item value for completed orders before refunds.
- **Refunded amount:** processed refunds associated with an order.
- **Net revenue:** gross revenue minus refunded amount, floored at zero.
- **Revenue leakage:** processed refunds plus shipping cost for completed late deliveries.
- **Late-delivery rate:** late completed orders divided by completed orders.

## Acceptance criteria

- A clean default run completes without manual data editing.
- Broken referential data fails before dbt executes.
- A full refresh materializes every Gold model and runs dbt tests.
- An incremental run appends only new order IDs to the order fact.
- The dashboard shows net revenue, leakage, late-delivery rate and causes.
- A new contributor can reproduce the result from the README.

## Success measures for this portfolio project

- Pipeline runtime and row counts are recorded in `pipeline_summary.json`.
- Data quality checks return zero incidents for the default dataset.
- The repository contains an executable test suite and CI workflow.
- A recruiter can understand the business problem and proof of execution from the README in under two minutes.
