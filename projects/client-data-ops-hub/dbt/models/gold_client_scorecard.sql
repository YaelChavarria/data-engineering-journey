{{ config(materialized='table') }}

with invoice_metrics as (
    select
        count(*) as invoice_count,
        count(*) filter (where invoice_status = 'paid') as paid_invoice_count,
        sum(amount) as billed_revenue,
        sum(amount) filter (where invoice_status = 'paid') as paid_revenue,
        count(*) filter (where invoice_status = 'overdue') as overdue_invoice_count
    from {{ source('client_delivery', 'silver_invoices') }}
),
account_metrics as (
    select
        count(*) filter (where account_status = 'active') as active_accounts,
        count(*) filter (where account_status = 'churned') as churned_accounts,
        sum(monthly_recurring_revenue) filter (where account_status = 'active') as mrr
    from {{ source('client_delivery', 'silver_accounts') }}
),
event_metrics as (
    select
        count(*) filter (where event_type = 'trial_started') as trials_started,
        count(*) filter (where event_type = 'activated') as trials_activated
    from {{ source('client_delivery', 'silver_account_events') }}
),
ticket_metrics as (
    select
        count(*) as tickets_created,
        count(*) filter (where ticket_status = 'open') as open_tickets,
        count(*) filter (
            where ticket_status = 'resolved'
              and date_diff('day', created_date, resolved_date) <= 2
        ) as sla_compliant_tickets,
        count(*) filter (where ticket_status = 'resolved') as resolved_tickets
    from {{ source('client_delivery', 'silver_support_tickets') }}
)
select
    '{{ env_var("CLIENT_DATA_OPS_CLIENT_ID", "atlas-saas") }}' as client_id,
    date '2025-03-31' as reporting_period,
    am.active_accounts,
    am.churned_accounts,
    am.mrr::decimal(12, 2) as mrr,
    im.billed_revenue::decimal(12, 2) as billed_revenue,
    im.paid_revenue::decimal(12, 2) as paid_revenue,
    (100.0 * im.paid_invoice_count / nullif(im.invoice_count, 0))::decimal(12, 2) as collection_rate,
    (100.0 * am.churned_accounts / nullif(am.active_accounts + am.churned_accounts, 0))::decimal(12, 2) as logo_churn_rate,
    (100.0 * em.trials_activated / nullif(em.trials_started, 0))::decimal(12, 2) as trial_to_active_rate,
    im.overdue_invoice_count,
    tm.tickets_created,
    tm.open_tickets,
    (100.0 * tm.sla_compliant_tickets / nullif(tm.resolved_tickets, 0))::decimal(12, 2) as support_sla_rate
from invoice_metrics im
cross join account_metrics am
cross join event_metrics em
cross join ticket_metrics tm
