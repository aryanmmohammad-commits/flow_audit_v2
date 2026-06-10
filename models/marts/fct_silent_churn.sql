-- Contract still marked Active and inside term, but billing stopped 90+ days
-- ago: phantom ARR still being counted.
select
    contract_id, account_id, status,
    acv as euro_impact,
    last_invoice_month,
    'active_contract_no_invoice_90d' as reason_code
from {{ ref('int_contract_billing_expected') }}
where status = 'Active'
  and end_date > date '{{ var("as_of_date") }}'
  and last_invoice_month < cast(date '{{ var("as_of_date") }}' - interval 90 day as date)
