# Migration Brief

## Client context

Meridian Systems is consolidating a legacy CRM and billing environment into a modern analytics warehouse. The business wants to use the new platform for Finance and Operations reporting without losing historical records or changing financial meaning.

## Business risk

A migration can appear successful while still containing missing entities, duplicate keys or changed amounts. Those errors are expensive because they often surface after reports, downstream systems or customer workflows depend on the new data.

## Objective

Provide a repeatable assurance process that gives the client a documented `READY` or `HOLD` decision before cutover.

## Users

| User | Decision |
|---|---|
| Migration lead | Whether the next wave can proceed |
| Finance owner | Whether invoice totals are preserved |
| CRM owner | Whether account and contact mappings are valid |
| Data team | Whether source, target and tests are trustworthy |
| Business owner | Whether the migration is acceptable for go-live |

## Acceptance criteria

- Source snapshot passes structural and relationship checks.
- Source and target counts are reconciled by entity.
- Financial amount differences are visible and explained.
- Every blocking exception has a severity and owner.
- The control room returns `HOLD` when high-severity issues remain.
- The manifest records the decision, checklist, quality gate and SLA evidence.
