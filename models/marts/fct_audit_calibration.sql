-- The audit auditing itself. Joins what detection FLAGGED against what was
-- PLANTED, at the individual-entity level, and scores precision and recall
-- per leak type. Because the data also contains planted legitimate exceptions
-- (approved accelerators, credit notes), zero false positives is a
-- non-trivial result: detection had innocents available to wrongly accuse.
-- This model references ground truth by design; for a real client engagement
-- (where no ground-truth file exists) it is simply excluded.
with detected as (
    select 'commission_overpayment' as leak_type,
           cast(commission_id as varchar) as entity_id
    from {{ ref('fct_commission_overpayments') }}
    union all
    select 'under_billing', cast(contract_id as varchar)
    from {{ ref('fct_underbilled_contracts') }}
    union all
    select 'silent_churn', cast(contract_id as varchar)
    from {{ ref('fct_silent_churn') }}
    union all
    select 'duplicate_revenue', cast(invoice_id as varchar)
    from {{ ref('fct_duplicate_invoices') }}
    union all
    select 'attribution_gap', cast(opportunity_id as varchar)
    from {{ ref('fct_attribution_gaps') }}
    union all
    select 'stalled_deal', cast(opportunity_id as varchar)
    from {{ ref('fct_stalled_deals') }}
),
planted as (
    select leak_type, cast(entity_id as varchar) as entity_id
    from {{ ref('ground_truth_leaks') }}
    where leak_type in ('commission_overpayment','under_billing','silent_churn',
                        'duplicate_revenue','attribution_gap','stalled_deal')
)
select
    coalesce(p.leak_type, d.leak_type) as leak_type,
    count(p.entity_id) as planted,
    count(d.entity_id) as detected,
    count(case when p.entity_id is not null and d.entity_id is not null then 1 end) as true_positives,
    count(case when p.entity_id is null then 1 end) as false_positives,
    count(case when d.entity_id is null then 1 end) as false_negatives,
    round(count(case when p.entity_id is not null and d.entity_id is not null then 1 end)
          * 1.0 / nullif(count(d.entity_id), 0), 4) as precision_rate,
    round(count(case when p.entity_id is not null and d.entity_id is not null then 1 end)
          * 1.0 / nullif(count(p.entity_id), 0), 4) as recall_rate
from planted p
full outer join detected d
  on p.leak_type = d.leak_type and p.entity_id = d.entity_id
group by 1
order by 1
