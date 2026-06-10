select
    invoice_id, contract_id, account_id, period_month,
    amount as euro_impact
from {{ ref('int_invoices_ranked') }}
where rn > 1
