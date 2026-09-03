{{ config(materialized='table') }}

with invoice_rollup as (
    select
        account_id,
        sum(amount)::decimal(12, 2) as billed_revenue,
        sum(amount) filter (where invoice_status = 'paid')::decimal(12, 2) as paid_revenue,
        count(*) filter (where invoice_status = 'overdue') as overdue_invoices
    from {{ source('client_delivery', 'silver_invoices') }}
    group by account_id
),
ticket_rollup as (
    select
        account_id,
        count(*) as tickets_created,
        count(*) filter (where ticket_status = 'open') as open_tickets,
        round(
            100.0 * count(*) filter (
                where ticket_status = 'resolved'
                  and date_diff('day', created_date, resolved_date) <= 2
            ) / nullif(count(*) filter (where ticket_status = 'resolved'), 0),
            2
        )::decimal(12, 2) as support_sla_rate
    from {{ source('client_delivery', 'silver_support_tickets') }}
    group by account_id
)
select
    a.account_id,
    a.account_name,
    a.plan,
    a.country,
    a.account_status,
    a.monthly_recurring_revenue,
    coalesce(i.billed_revenue, 0)::decimal(12, 2) as billed_revenue,
    coalesce(i.paid_revenue, 0)::decimal(12, 2) as paid_revenue,
    coalesce(i.overdue_invoices, 0) as overdue_invoices,
    coalesce(t.tickets_created, 0) as tickets_created,
    coalesce(t.open_tickets, 0) as open_tickets,
    coalesce(t.support_sla_rate, 100)::decimal(12, 2) as support_sla_rate,
    case
        when a.account_status = 'churned' then 'churned'
        when coalesce(i.overdue_invoices, 0) > 0 or coalesce(t.open_tickets, 0) > 0 then 'needs_attention'
        when a.account_status = 'trial' then 'trial'
        else 'healthy'
    end as health_segment
from {{ source('client_delivery', 'silver_accounts') }} a
left join invoice_rollup i on i.account_id = a.account_id
left join ticket_rollup t on t.account_id = a.account_id
