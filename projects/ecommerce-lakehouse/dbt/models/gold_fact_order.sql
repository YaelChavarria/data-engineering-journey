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
),
refund_totals as (
    select
        order_id,
        sum(case when refund_status = 'processed' then amount else 0 end)::decimal(12, 2) as refunded_amount
    from {{ source('ecommerce', 'silver_refunds') }}
    group by order_id
),
shipment_details as (
    select
        order_id,
        carrier,
        promised_delivery_date,
        actual_delivery_date,
        shipping_cost,
        shipment_status
    from {{ source('ecommerce', 'silver_shipments') }}
)
select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.order_status,
    coalesce(ot.order_total, 0)::decimal(12, 2) as order_total,
    coalesce(pt.paid_amount, 0)::decimal(12, 2) as paid_amount,
    o.order_status <> 'cancelled' as is_completed,
    coalesce(rt.refunded_amount, 0)::decimal(12, 2) as refunded_amount,
    case when o.order_status <> 'cancelled' then
        greatest(coalesce(ot.order_total, 0) - coalesce(rt.refunded_amount, 0), 0)
        else 0 end::decimal(12, 2) as net_revenue,
    coalesce(sd.carrier, 'not_shipped') as carrier,
    sd.promised_delivery_date,
    sd.actual_delivery_date,
    coalesce(sd.shipping_cost, 0)::decimal(12, 2) as shipping_cost,
    coalesce(sd.actual_delivery_date > sd.promised_delivery_date, false) as is_late,
    case when sd.actual_delivery_date > sd.promised_delivery_date then
        date_diff('day', sd.promised_delivery_date, sd.actual_delivery_date)
        else 0 end as days_late,
    (
        coalesce(rt.refunded_amount, 0)
        + case when sd.actual_delivery_date > sd.promised_delivery_date
               then coalesce(sd.shipping_cost, 0) else 0 end
    )::decimal(12, 2) as leakage_amount
from {{ source('ecommerce', 'silver_orders') }} o
left join order_totals ot on ot.order_id = o.order_id
left join payment_totals pt on pt.order_id = o.order_id
left join refund_totals rt on rt.order_id = o.order_id
left join shipment_details sd on sd.order_id = o.order_id
{% if is_incremental() %}
where o.order_id > coalesce((select max(order_id) from {{ this }}), 0)
{% endif %}
