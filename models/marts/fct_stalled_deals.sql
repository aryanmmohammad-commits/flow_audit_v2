select
    o.opportunity_id, o.account_id, o.rep_id,
    s.stage, s.days_in_stage,
    o.amount as euro_impact,
    'stage_age_above_threshold' as reason_code
from {{ ref('int_opportunity_current_stage') }} s
join {{ ref('stg_opportunities') }} o on s.opportunity_id = o.opportunity_id
where not o.is_closed
  and s.stage not in ('Closed Won', 'Closed Lost')
  and s.days_in_stage > {{ var('stall_days', 100) }}
