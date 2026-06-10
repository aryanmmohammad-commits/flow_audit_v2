select
    commission_id, opportunity_id, rep_id,
    commission_paid, commission_expected, approved_adjustment,
    unexplained_variance as euro_impact,
    'paid_above_plan_rate_unapproved' as reason_code
from {{ ref('int_commission_expected') }}
where unexplained_variance > 1
