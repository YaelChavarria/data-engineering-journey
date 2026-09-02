{{ config(materialized='table') }}

with leakage_events as (
    select
        order_date as event_date,
        order_id,
        'refund' as leakage_type,
        refunded_amount as leakage_amount
    from {{ ref('gold_fact_order') }}
    where refunded_amount > 0

    union all

    select
        order_date as event_date,
        order_id,
        'late_delivery' as leakage_type,
        shipping_cost as leakage_amount
    from {{ ref('gold_fact_order') }}
    where is_late and is_completed and shipping_cost > 0
)
select
    leakage_type,
    count(distinct order_id) as affected_orders,
    sum(leakage_amount)::decimal(12, 2) as leakage_amount,
    case
        when sum(leakage_amount) >= 100 then 'high'
        when sum(leakage_amount) >= 40 then 'medium'
        else 'low'
    end as priority
from leakage_events
group by leakage_type
order by leakage_amount desc
