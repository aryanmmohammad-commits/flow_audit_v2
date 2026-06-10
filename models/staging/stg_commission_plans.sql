select commission_plan_id, plan_name, commission_rate, floor_price
from {{ ref('commission_plans') }}
