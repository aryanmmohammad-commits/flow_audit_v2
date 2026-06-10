-- The scorecard: one row per leak type, with its euro total and impact class.
-- potentially_recoverable_cash = may be recovered after finance/legal review;
-- at minimum it prices preventable future leakage.
with parts as (
    select 'commission_overpayment' as leak_type, 'potentially_recoverable_cash' as impact_class,
           count(*) as leak_count, round(sum(euro_impact), 2) as euro_impact
    from {{ ref('fct_commission_overpayments') }}
    union all
    select 'under_billing', 'potentially_recoverable_cash',
           count(*), round(sum(euro_impact), 2) from {{ ref('fct_underbilled_contracts') }}
    union all
    select 'duplicate_revenue', 'overstated_revenue',
           count(*), round(sum(euro_impact), 2) from {{ ref('fct_duplicate_invoices') }}
    union all
    select 'silent_churn', 'overstated_revenue',
           count(*), round(sum(euro_impact), 2) from {{ ref('fct_silent_churn') }}
    union all
    select 'attribution_gap', 'revenue_at_risk',
           count(*), round(sum(euro_impact), 2) from {{ ref('fct_attribution_gaps') }}
    union all
    select 'stalled_deal', 'revenue_at_risk',
           count(*), round(sum(euro_impact), 2) from {{ ref('fct_stalled_deals') }}
)
select * from parts
order by impact_class, leak_type
