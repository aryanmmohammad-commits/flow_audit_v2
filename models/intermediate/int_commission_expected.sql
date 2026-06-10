-- Reconcile what each rep was paid against what the plan rate says they were owed.
select
    c.commission_id,
    c.opportunity_id,
    c.rep_id,
    c.commission_amount                              as commission_paid,
    o.amount                                         as opportunity_amount,
    p.commission_rate,
    round(o.amount * p.commission_rate, 2)           as commission_expected,
    round(c.commission_amount - o.amount * p.commission_rate, 2) as variance
from {{ ref('stg_commissions') }} c
join {{ ref('stg_opportunities') }} o on c.opportunity_id = o.opportunity_id
join {{ ref('stg_reps') }} r           on c.rep_id = r.rep_id
join {{ ref('stg_commission_plans') }} p on r.commission_plan_id = p.commission_plan_id
