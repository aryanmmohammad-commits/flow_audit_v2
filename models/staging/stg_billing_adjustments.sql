-- Finance-approved billing adjustments (credit notes, approved discounts).
select adjustment_id, contract_id, adjustment_type,
       adjustment_amount, approved_by, approved_date
from {{ ref('billing_adjustments') }}
