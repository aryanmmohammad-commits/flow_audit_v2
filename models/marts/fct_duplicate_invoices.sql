select
    invoice_id, contract_id, account_id, period_month,
    amount as euro_impact,
    'duplicate_invoice_same_period_amount' as reason_code
from {{ ref('int_invoices_ranked') }}
where rn > 1
