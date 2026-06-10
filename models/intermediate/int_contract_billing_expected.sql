-- Per contract: expected billing (ACV prorated over elapsed months) vs what
-- was actually invoiced (after dedup), netting approved credits/discounts,
-- plus the last month we saw any billing.
with billed as (
    select contract_id, sum(amount) as amount_billed
    from {{ ref('int_invoices_ranked') }}
    where rn = 1
    group by contract_id
),
last_inv as (
    select contract_id, max(period_month) as last_invoice_month
    from {{ ref('int_invoices_ranked') }}
    where rn = 1
    group by contract_id
),
adj as (
    select contract_id, sum(adjustment_amount) as approved_reduction
    from {{ ref('stg_billing_adjustments') }}
    group by contract_id
)
select
    c.contract_id,
    c.account_id,
    c.status,
    c.start_date,
    c.end_date,
    c.acv,
    round(c.acv / 12.0, 2) as monthly_amount,
    date_diff('month',
        date_trunc('month', c.start_date),
        date_trunc('month', least(c.end_date, date '{{ var("as_of_date") }}'))
    ) + 1 as months_expected,
    round((c.acv / 12.0) * (date_diff('month',
        date_trunc('month', c.start_date),
        date_trunc('month', least(c.end_date, date '{{ var("as_of_date") }}'))
    ) + 1), 2) as amount_expected,
    coalesce(b.amount_billed, 0) as amount_billed,
    coalesce(a.approved_reduction, 0) as approved_reduction,
    li.last_invoice_month
from {{ ref('stg_contracts') }} c
left join billed b   on c.contract_id = b.contract_id
left join last_inv li on c.contract_id = li.contract_id
left join adj a      on c.contract_id = a.contract_id
