-- Net revenue retention by signup cohort, restricted to cohorts mature enough to
-- have faced a renewal decision (12+ months before as_of). Newer, still-in-term
-- cohorts are excluded so the trend is not flattered by contracts that simply
-- have not renewed yet.
with originals as (
    select contract_id, acv, status,
           strftime(start_date, '%Y-%m') as cohort_month
    from {{ ref('stg_contracts') }}
    where renewal_of is null
),
renewals as (
    select renewal_of as contract_id, acv as renewal_acv
    from {{ ref('stg_contracts') }}
    where renewal_of is not null
),
kept as (
    select o.cohort_month, o.acv,
        case
            when o.status = 'Churned'  then 0
            when o.status = 'Renewed'  then coalesce(rn.renewal_acv, 0)
            else o.acv
        end as retained_acv
    from originals o
    left join renewals rn on o.contract_id = rn.contract_id
)
select
    cohort_month,
    count(*)                                      as cohort_n,
    round(sum(acv), 2)                            as original_acv,
    round(sum(retained_acv), 2)                   as retained_acv,
    round(sum(retained_acv) / nullif(sum(acv), 0), 4) as nrr
from kept
where cohort_month <= strftime(
    cast(date '{{ var("as_of_date") }}' - interval 12 month as date), '%Y-%m')
group by cohort_month
