-- Finance-approved commission adjustments (accelerators, spiffs, overrides).
-- An approval register is operational data, not ground truth: detection nets
-- these out so only UNEXPLAINED variance is flagged as leakage.
select adjustment_id, commission_id, adjustment_type,
       adjustment_amount, approved_by, approved_date
from {{ ref('commission_adjustments') }}
