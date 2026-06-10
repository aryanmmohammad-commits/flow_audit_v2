select account_id, account_name, industry, segment, country, created_date
from {{ ref('accounts') }}
