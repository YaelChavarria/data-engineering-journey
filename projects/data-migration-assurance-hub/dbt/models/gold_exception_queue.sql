{{ config(materialized='table') }}

with exceptions as (
    select
        'accounts' as entity,
        cast(s.account_id as varchar) as record_key,
        'missing_in_target' as issue_type,
        'high' as severity,
        'Source account has no matching target record.' as description,
        'Migration lead' as owner
    from {{ source('migration', 'silver_source_accounts') }} s
    left join {{ source('migration', 'silver_target_accounts') }} t on t.account_id = s.account_id
    where t.account_id is null

    union all

    select
        'accounts',
        cast(account_id as varchar),
        'duplicate_target_key',
        'high',
        'Target contains more than one record for the same account key.',
        'CRM owner'
    from {{ source('migration', 'silver_target_accounts') }}
    group by account_id
    having count(*) > 1

    union all

    select
        'invoices',
        cast(s.invoice_id as varchar),
        'missing_in_target',
        'high',
        'Source invoice has no matching target record.',
        'Finance'
    from {{ source('migration', 'silver_source_invoices') }} s
    left join {{ source('migration', 'silver_target_invoices') }} t on t.invoice_id = s.invoice_id
    where t.invoice_id is null

    union all

    select
        'invoices',
        cast(s.invoice_id as varchar),
        'amount_mismatch',
        'high',
        'Invoice amount differs between source and target.',
        'Finance'
    from {{ source('migration', 'silver_source_invoices') }} s
    join {{ source('migration', 'silver_target_invoices') }} t on t.invoice_id = s.invoice_id
    where abs(s.amount - t.amount) >= 0.01

    union all

    select
        'contacts',
        cast(s.contact_id as varchar),
        'missing_in_target',
        'medium',
        'Source contact has no matching target record.',
        'CRM owner'
    from {{ source('migration', 'silver_source_contacts') }} s
    left join {{ source('migration', 'silver_target_contacts') }} t on t.contact_id = s.contact_id
    where t.contact_id is null
)
select
    row_number() over (order by severity desc, entity, record_key) as exception_id,
    entity,
    record_key,
    issue_type,
    severity,
    description,
    owner,
    'open' as status
from exceptions
