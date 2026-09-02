{{ config(materialized='table') }}

select
    c.customer_id,
    c.full_name,
    count(f.order_id) as order_count,
    sum(f.net_revenue)::decimal(12, 2) as lifetime_value
from {{ ref('gold_dim_customer') }} c
join {{ ref('gold_fact_order') }} f on f.customer_id = c.customer_id
where f.is_completed
group by c.customer_id, c.full_name
order by lifetime_value desc
