{{ config(materialized='table') }}

select
    order_date,
    count(*) as order_count,
    count(*) filter (where is_completed) as completed_orders,
    sum(case when is_completed then order_total else 0 end)::decimal(12, 2) as gross_revenue,
    sum(net_revenue)::decimal(12, 2) as net_revenue,
    sum(refunded_amount)::decimal(12, 2) as refunded_amount,
    sum(leakage_amount)::decimal(12, 2) as leakage_amount,
    count(*) filter (where is_late) as late_orders,
    coalesce(
        round(
            100.0 * count(*) filter (where is_late and is_completed)
            / nullif(count(*) filter (where is_completed), 0),
            2
        ),
        0
    )::decimal(12, 2) as late_delivery_rate
from {{ ref('gold_fact_order') }}
group by order_date
order by order_date
