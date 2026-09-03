{{ config(materialized='table') }}

with dates as (
    select invoice_date as metric_date from {{ source('client_delivery', 'silver_invoices') }}
    union
    select created_date as metric_date from {{ source('client_delivery', 'silver_support_tickets') }}
),
invoice_daily as (
    select
        invoice_date as metric_date,
        sum(amount)::decimal(12, 2) as billed_revenue,
        sum(amount) filter (where invoice_status = 'paid')::decimal(12, 2) as paid_revenue,
        count(*) filter (where invoice_status = 'overdue') as overdue_invoices
    from {{ source('client_delivery', 'silver_invoices') }}
    group by invoice_date
),
ticket_daily as (
    select
        created_date as metric_date,
        count(*) as tickets_created,
        count(*) filter (where ticket_status = 'open') as open_tickets
    from {{ source('client_delivery', 'silver_support_tickets') }}
    group by created_date
)
select
    d.metric_date,
    coalesce(i.billed_revenue, 0)::decimal(12, 2) as billed_revenue,
    coalesce(i.paid_revenue, 0)::decimal(12, 2) as paid_revenue,
    coalesce(i.overdue_invoices, 0) as overdue_invoices,
    coalesce(t.tickets_created, 0) as tickets_created,
    coalesce(t.open_tickets, 0) as open_tickets
from dates d
left join invoice_daily i on i.metric_date = d.metric_date
left join ticket_daily t on t.metric_date = d.metric_date
order by d.metric_date
