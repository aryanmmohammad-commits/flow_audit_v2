-- Billed less than expected, but NOT a silent-churn case (that is reported
-- separately). A churned contract has stopped billing 90+ days ago.
select
    contract_id, account_id,
    amount_expected, amount_billed,
    round(amount_expected - amount_billed, 2) as euro_impact,
    last_invoice_month
from {{ ref('int_contract_billing_expected') }}
where amount_expected - amount_billed > 1
  and not (
        status = 'Active'
    and end_date > date '{{ var("as_of_date") }}'
    and last_invoice_month < cast(date '{{ var("as_of_date") }}' - interval 90 day as date)
  )
