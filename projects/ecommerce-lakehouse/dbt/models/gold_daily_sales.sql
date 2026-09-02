{{ config(materialized='table') }}

select
    order_date,
    count(*) as order_count,
    sum(net_revenue)::decimal(12, 2) as revenue,
    round(avg(net_revenue), 2)::decimal(12, 2) as average_order_value,
    sum(order_total)::decimal(12, 2) as gross_revenue,
    sum(refunded_amount)::decimal(12, 2) as refunded_amount,
    sum(leakage_amount)::decimal(12, 2) as leakage_amount
from {{ ref('gold_fact_order') }}
where is_completed
group by order_date
order by order_date
