# Reconciliation Contract

The reconciliation contract defines how source and target snapshots are compared for each migration wave.

## Entity checks

| Entity | Key | Count check | Amount check |
|---|---|---|---|
| Accounts | `account_id` | Exact | Monthly value total |
| Invoices | `invoice_id` | Exact | Invoice amount total |
| Transactions | `transaction_id` | Exact | Transaction amount total |
| Contacts | `contact_id` | Exact | Not applicable |

## Exception rules

- Missing source key in target: `high`
- Duplicate target key: `high`
- Monetary difference of at least `$0.01`: `high`
- Missing contact: `medium`
- Unresolved high-severity exception: blocks cutover.
- Unresolved medium-severity exception: requires review but does not independently block cutover.

## Status definitions

- `passed`: entity count and applicable amount totals reconcile.
- `review`: a count, key or amount difference needs an owner.
- `HOLD`: at least one high-severity exception remains open.
- `READY`: no high-severity exceptions remain and reconciliation checks pass.

Tolerance rules must be agreed with the client before the migration wave begins. This demonstration uses exact counts and a one-cent monetary tolerance.
