# Data Contract

The contract represents the minimum information expected from the Atlas SaaS client. In a real engagement, the client owns the source definitions and approves changes.

## Inputs

| File | Grain | Primary key | Required relationships |
|---|---|---|---|
| `accounts.csv` | One row per account | `account_id` | None |
| `invoices.csv` | One row per invoice | `invoice_id` | `account_id` must exist |
| `support_tickets.csv` | One row per ticket | `ticket_id` | `account_id` must exist |
| `account_events.csv` | One row per account event | `event_id` | `account_id` must exist |

## Accepted domains

- Account status: `active`, `trial`, `churned`
- Invoice status: `paid`, `overdue`
- Ticket priority: `low`, `medium`, `high`
- Ticket status: `open`, `resolved`
- Event type: `account_created`, `trial_started`, `activated`, `cancelled`

## Quality gate

- Required files and columns exist.
- Primary keys are unique and non-null.
- Foreign keys resolve to `accounts`.
- Amounts and recurring revenue are non-negative.
- Dates are parseable.
- Domain values are approved.

Critical failures block publication. The delivery manifest must show `accepted` only after every critical check passes.

## Change management

The client must notify the data partner before changing a field name, type, accepted value or source cadence. The partner updates the contract, tests, transformations and release notes before accepting the new export.
