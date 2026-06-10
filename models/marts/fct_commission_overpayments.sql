select
    commission_id, opportunity_id, rep_id,
    commission_paid, commission_expected,
    variance as euro_impact
from {{ ref('int_commission_expected') }}
where variance > 1
