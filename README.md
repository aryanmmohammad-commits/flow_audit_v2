# Flow Audit v2 — a revenue reconciliation layer for B2B SaaS

[![dbt build & test](https://github.com/aryanmmohammad-commits/flow_audit_v2/actions/workflows/dbt_ci.yml/badge.svg)](https://github.com/aryanmmohammad-commits/flow_audit_v2/actions/workflows/dbt_ci.yml)

Flow Audit finds the financial truth between systems...


Flow Audit finds the financial truth between systems: what was sold (CRM), what was
contracted, what was billed (invoices), what was paid out (commissions) — and what
*should* have happened. Money leaks at the seams between those systems: commissions
overpaid, invoices under-billed, deals stalling, customers silently churned, revenue
double-counted. Each finding carries a euro figure, a reason code, and an impact class
a non-technical manager can act on.

The principle behind it, in one line: *growth comes from removing obstruction in the
value flow.* Flow Audit turns invisible obstruction into named, priced, fixable leakage.

Status: dual-warehouse (DuckDB + BigQuery) · CI on every push · dbt build green (24 models, 52 tests passing).
## The claim, made falsifiable

Synthetic test data is only convincing if the validation cannot be circular. "I planted
leaks and found them" proves recall and nothing else. So the dataset is a **mixed
field**: 267 discrete planted leaks *and* 37 planted **legitimate exceptions** —
finance-approved accelerators, spiffs, credit notes — that look exactly like leaks to a
naive query. Detection must consult the approval registers and net out approved
variance; leakage is defined as **unexplained variance only**.

The audit then audits itself. `fct_audit_calibration` joins what was flagged against
what was planted, entity by entity:

```
leak_type                planted detected   TP   FP   FN  precision  recall
attribution_gap               48       48   48    0    0       100%    100%
commission_overpayment        18       18   18    0    0       100%    100%
duplicate_revenue            137      137  137    0    0       100%    100%
silent_churn                  18       18   18    0    0       100%    100%
stalled_deal                  22       22   22    0    0       100%    100%
under_billing                 24       24   24    0    0       100%    100%
```

Zero false positives is the non-trivial half: 37 innocents were available to wrongly
accuse, and none were. A dbt test (`assert_zero_false_positives_or_negatives`) fails
the build if either number ever rises above zero.

## The leak catalog

| Leak | Reason code | Detection technique |
|---|---|---|
| Commission overpayment | `paid_above_plan_rate_unapproved` | reconciliation join, net of approvals |
| Under-billing | `contract_invoice_amount_mismatch` | expected-vs-billed, net of credits, after dedup |
| Attribution gap | `closed_won_missing_lead_source` / `closed_won_dangling_lead_reference` | anti-join (null + dangling keys) |
| Stalled deals | `stage_age_above_threshold` | window function: days-in-stage |
| Silent churn (phantom ARR) | `active_contract_no_invoice_90d` | active but billing stopped 90+ days |
| Duplicate revenue | `duplicate_invoice_same_period_amount` | `row_number()` dedup |
| NRR decay | cohort-level, reported not flagged | mature-cohort retention logic |

Every flagged row answers: what leaked, why (reason code), how much (euro impact),
and how real the money is (impact class).

## The exception layer

Approval registers (`commission_adjustments`, `billing_adjustments`) are first-class
inputs, because in a real company most "anomalies" are explainable. The operating
principle: **CRM is an input, not truth — billing, contracts, and approvals must
challenge it.** What survives the challenge is leakage.

## Impact classes — how real is the money?

| Impact class | Meaning | Current total |
|---|---|---|
| `potentially_recoverable_cash` | recoverable *pending finance/legal review* (overpaid / under-billed); at minimum it prices preventable future leakage | ~€152k |
| `overstated_revenue` | books / forecast overstated (double-billed / phantom ARR) | ~€1.40M |
| `revenue_at_risk` | not lost yet, but blind or fragile (attribution / stalls) | ~€3.05M |

These are deliberately separate. Conflating "cash you can claw back" with "revenue at
risk" is how audits lose CFO trust; the headline here is the smallest number.

## Data contract

The generator emits twelve CSVs (entities, pipeline motion, billing motion, comp
motion, approval registers, and the synthetic-only ground-truth ledger). Real client
onboarding requires a **mapping layer**: their CRM, billing, contract, and payout
exports are mapped into this canonical schema. Once mapped, the same detection models
run unchanged — the mapping is the engagement-specific work; the audit logic is the
reusable asset.

## Stack

Developed locally on **DuckDB** (instant, zero infra). The models are written to be
**warehouse-portable**; BigQuery/Snowflake deployment requires adapter configuration
(`profiles.yml`) and environment-specific validation of date functions, typing, and
seed loading. Portability is a design goal, not a free lunch.

## Scope and limitations — the hardening roadmap

This is a **controlled diagnostic engine with planted ground truth**. It proves the
reconciliation method, the modeling, and the calibration discipline. It does not yet
model the full mess of mature SaaS revenue operations. Real-data hardening, in rough
priority order: commission plan versioning and quota tiers (beyond flat approvals),
split crediting, clawbacks, payment-timing-based commissions, contract amendments and
proration, credits/refunds beyond flat credit notes, multi-currency reconciliation,
usage-based billing, exception approval workflows, and source-freshness monitoring.
The current model supports base-rate commission and flat-credit billing
reconciliation; the list above is the named path from diagnostic engine to production
control layer.

## The five questions every company has

Should money have come in that didn't? Did too much money go out? Was the same
economic event counted twice? Is anything called "active" that is actually dead?
Is future revenue silently blocked? Flow Audit is those five questions, made
mechanical and priced in euros.

## Run it

```bash
python generate_data.py      # writes the twelve seed CSVs + the score sheet
python validate.py           # plain-SQL detection, reconciled to ground truth
dbt build --profiles-dir .   # seeds + 24 models + 52 tests, incl. calibration
```

`fct_leak_summary` is the scorecard; `fct_audit_calibration` is the precision/recall
table; `int_contract_cohort_retention` holds the mature-cohort NRR trend.

## Roadmap

1. **Synthetic dataset + ground-truth leak ledger** — done
2. **dbt model layer** (staging → intermediate → marts) — done
3. **Exception layer + decoy calibration + reason codes** — done (this commit)
4. Early-warning layer — warn-severity alerts, source freshness
5. AI layer — an LLM writes the plain-language "what leaked, likely cause, euro impact"
6. Stakeholder output — Power BI dashboard + written impact narrative

— *By Aryan Mohammaddoost. Wishing you clarity and sustained focus.*
