select
    commission_id,
    opportunity_id,
    rep_id,
    nullif(contract_id, '') as contract_id,
    commission_amount,
    paid_date
from {{ ref('commissions') }}
