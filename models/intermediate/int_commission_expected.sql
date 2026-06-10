-- Reconcile what each rep was paid against what the plan rate says they were
-- owed, netting out finance-approved adjustments. Leakage is the variance the
-- approval register cannot explain.
with adj as (
    select commission_id, sum(adjustment_amount) as approved_adjustment
    from {{ ref('stg_commission_adjustments') }}
    group by commission_id
)
select
    c.commission_id,
    c.opportunity_id,
    c.rep_id,
    c.commission_amount                              as commission_paid,
    o.amount                                         as opportunity_amount,
    p.commission_rate,
    round(o.amount * p.commission_rate, 2)           as commission_expected,
    coalesce(a.approved_adjustment, 0)               as approved_adjustment,
    round(c.commission_amount - o.amount * p.commission_rate, 2) as raw_variance,
    round(c.commission_amount - o.amount * p.commission_rate
          - coalesce(a.approved_adjustment, 0), 2)   as unexplained_variance
from {{ ref('stg_commissions') }} c
join {{ ref('stg_opportunities') }} o on c.opportunity_id = o.opportunity_id
join {{ ref('stg_reps') }} r           on c.rep_id = r.rep_id
join {{ ref('stg_commission_plans') }} p on r.commission_plan_id = p.commission_plan_id
left join adj a on c.commission_id = a.commission_id
