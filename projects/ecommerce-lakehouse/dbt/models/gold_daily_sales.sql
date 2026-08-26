{{ config(materialized='table') }}

select
    order_date,
    count(*) as order_count,
    sum(order_total)::decimal(12, 2) as revenue,
    round(avg(order_total), 2)::decimal(12, 2) as average_order_value
from {{ ref('gold_fact_order') }}
where is_completed
group by order_date
order by order_date
