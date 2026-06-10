-- Rank invoices within (contract, period, amount). rn = 1 is the true invoice;
-- rn > 1 is a duplicate. Everything downstream dedups on rn = 1.
select
    invoice_id, contract_id, account_id, invoice_date, period_month, amount,
    row_number() over (
        partition by contract_id, period_month, amount
        order by invoice_id
    ) as rn
from {{ ref('stg_invoices') }}
