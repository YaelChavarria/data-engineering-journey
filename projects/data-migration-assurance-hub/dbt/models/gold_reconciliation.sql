{{ config(materialized='table') }}

with reconciliation as (
    select
        'accounts' as entity,
        (select count(*) from {{ source('migration', 'silver_source_accounts') }}) as source_count,
        (select count(*) from {{ source('migration', 'silver_target_accounts') }}) as target_count,
        (select sum(monthly_value) from {{ source('migration', 'silver_source_accounts') }})::decimal(14, 2) as source_amount,
        (select sum(monthly_value) from {{ source('migration', 'silver_target_accounts') }})::decimal(14, 2) as target_amount
    union all
    select
        'invoices',
        (select count(*) from {{ source('migration', 'silver_source_invoices') }}),
        (select count(*) from {{ source('migration', 'silver_target_invoices') }}),
        (select sum(amount) from {{ source('migration', 'silver_source_invoices') }})::decimal(14, 2),
        (select sum(amount) from {{ source('migration', 'silver_target_invoices') }})::decimal(14, 2)
    union all
    select
        'transactions',
        (select count(*) from {{ source('migration', 'silver_source_transactions') }}),
        (select count(*) from {{ source('migration', 'silver_target_transactions') }}),
        (select sum(amount) from {{ source('migration', 'silver_source_transactions') }})::decimal(14, 2),
        (select sum(amount) from {{ source('migration', 'silver_target_transactions') }})::decimal(14, 2)
    union all
    select
        'contacts',
        (select count(*) from {{ source('migration', 'silver_source_contacts') }}),
        (select count(*) from {{ source('migration', 'silver_target_contacts') }}),
        cast(null as decimal(14, 2)),
        cast(null as decimal(14, 2))
)
select
    entity,
    source_count,
    target_count,
    target_count - source_count as row_count_delta,
    source_amount,
    target_amount,
    coalesce(target_amount - source_amount, 0)::decimal(14, 2) as amount_delta,
    case
        when target_count = source_count and abs(coalesce(target_amount - source_amount, 0)) < 0.01 then 'passed'
        else 'review'
    end as reconciliation_status
from reconciliation
