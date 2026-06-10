select
    contract_id,
    opportunity_id,
    account_id,
    nullif(renewal_of, '') as renewal_of,
    start_date,
    end_date,
    term_months,
    acv,
    status
from {{ ref('contracts') }}
