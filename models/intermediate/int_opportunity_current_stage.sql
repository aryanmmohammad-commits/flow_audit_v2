-- The stage each open opportunity is currently sitting in, and for how long.
select
    opportunity_id,
    stage,
    entered_at,
    date_diff('day', entered_at, date '{{ var("as_of_date") }}') as days_in_stage
from {{ ref('stg_opportunity_stage_history') }}
where exited_at is null
