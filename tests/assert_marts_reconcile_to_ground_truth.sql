-- Calibration test: every discrete leak the marts find must equal what was
-- planted. Returns rows only on mismatch, so a passing test = the audit is
-- correctly calibrated. (For a real client there is no ground_truth seed, and
-- this test is simply dropped.)
with detected as (
    select leak_type, leak_count from {{ ref('fct_leak_summary') }}
),
planted as (
    select leak_type, count(*) as planted_count
    from {{ ref('ground_truth_leaks') }}
    where leak_type in (
        'commission_overpayment','under_billing','duplicate_revenue',
        'silent_churn','attribution_gap','stalled_deal'
    )
    group by leak_type
)
select
    p.leak_type,
    p.planted_count,
    coalesce(d.leak_count, 0) as detected_count
from planted p
left join detected d on p.leak_type = d.leak_type
where p.planted_count <> coalesce(d.leak_count, 0)
