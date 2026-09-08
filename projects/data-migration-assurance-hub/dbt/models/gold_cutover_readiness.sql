{{ config(materialized='table') }}

with exception_counts as (
    select
        count(*) as total_exceptions,
        count(*) filter (where severity = 'high') as high_exceptions,
        count(*) filter (where severity = 'medium') as medium_exceptions
    from {{ ref('gold_exception_queue') }}
),
reconciliation_counts as (
    select
        count(*) as entity_count,
        count(*) filter (where reconciliation_status = 'passed') as passed_entities
    from {{ ref('gold_reconciliation') }}
)
select
    '{{ env_var("DATA_MIGRATION_ID", "MIG-2026-09-W03") }}' as migration_id,
    '03' as wave,
    case when ec.high_exceptions > 0 then 'HOLD' else 'READY' end as cutover_decision,
    ec.total_exceptions,
    ec.high_exceptions,
    ec.medium_exceptions,
    rc.entity_count,
    rc.passed_entities,
    case
        when ec.high_exceptions > 0 then 'Resolve high-severity exceptions before cutover.'
        when rc.passed_entities < rc.entity_count then 'Review reconciliation differences before sign-off.'
        else 'All reconciliation checks passed. Obtain business sign-off.'
    end as decision_reason
from exception_counts ec
cross join reconciliation_counts rc
