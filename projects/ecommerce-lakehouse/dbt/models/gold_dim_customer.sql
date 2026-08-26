{{ config(materialized='table') }}

select
    customer_id,
    full_name,
    email,
    country,
    registered_date
from {{ source('ecommerce', 'silver_customers') }}
