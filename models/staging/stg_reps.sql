select rep_id, rep_name, region, commission_plan_id, hire_date
from {{ ref('reps') }}
