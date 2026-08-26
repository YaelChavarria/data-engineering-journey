{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='delete+insert'
    )
}}

with order_totals as (
    select
        order_id,
        sum(quantity * unit_price)::decimal(12, 2) as order_total
    from {{ source('ecommerce', 'silver_order_items') }}
    group by order_id
),
payment_totals as (
    select
        order_id,
        sum(case when payment_status = 'paid' then amount else 0 end)::decimal(12, 2) as paid_amount
    from {{ source('ecommerce', 'silver_payments') }}
    group by order_id
)
select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.order_status,
    coalesce(ot.order_total, 0)::decimal(12, 2) as order_total,
    coalesce(pt.paid_amount, 0)::decimal(12, 2) as paid_amount,
    o.order_status <> 'cancelled' as is_completed
from {{ source('ecommerce', 'silver_orders') }} o
left join order_totals ot on ot.order_id = o.order_id
left join payment_totals pt on pt.order_id = o.order_id
{% if is_incremental() %}
where o.order_id > coalesce((select max(order_id) from {{ this }}), 0)
{% endif %}
