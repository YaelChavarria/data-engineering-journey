{{ config(materialized='table') }}

select
    p.category,
    sum(i.quantity) as units_sold,
    sum(i.quantity * i.unit_price)::decimal(12, 2) as revenue
from {{ source('ecommerce', 'silver_order_items') }} i
join {{ source('ecommerce', 'silver_orders') }} o on o.order_id = i.order_id
join {{ ref('gold_dim_product') }} p on p.product_id = i.product_id
where o.order_status <> 'cancelled'
group by p.category
order by revenue desc
