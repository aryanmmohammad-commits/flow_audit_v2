select lead_id, account_id, source, created_date, status
from {{ ref('leads') }}
