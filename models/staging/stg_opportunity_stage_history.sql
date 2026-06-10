select history_id, opportunity_id, stage, entered_at, exited_at
from {{ ref('opportunity_stage_history') }}
