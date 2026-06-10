-- Billed less than expected after netting approved credits, and NOT a
-- silent-churn case (reported separately).
select
    contract_id, account_id,
    amount_expected, amount_billed, approved_reduction,
    round(amount_expected - amount_billed - approved_reduction, 2) as euro_impact,
    last_invoice_month,
    'contract_invoice_amount_mismatch' as reason_code
from {{ ref('int_contract_billing_expected') }}
where amount_expected - amount_billed - approved_reduction > 1
  and not (
        status = 'Active'
    and end_date > date '{{ var("as_of_date") }}'
    and last_invoice_month < cast(date '{{ var("as_of_date") }}' - interval 90 day as date)
  )
