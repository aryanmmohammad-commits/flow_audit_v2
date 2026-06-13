select
    opportunity_id,
    account_id,
    nullif(lead_id, '')        as lead_id,
    rep_id,
    created_date,
    close_date,
    stage,
    cast(amount as {{ type_float() }})     as amount,
    cast(is_closed as boolean) as is_closed,
    cast(is_won as boolean)    as is_won
from {{ ref('opportunities') }}
