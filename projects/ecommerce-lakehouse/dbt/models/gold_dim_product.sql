{{ config(materialized='table') }}

select
    product_id,
    product_name,
    category,
    unit_price
from {{ source('ecommerce', 'silver_products') }}
