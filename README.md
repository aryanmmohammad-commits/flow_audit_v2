# Flow Audit v2 — B2B SaaS revenue-leakage & reconciliation diagnostic

A production-style analytics-engineering project that points a dbt model layer at a
company's revenue data — deals, contracts, invoices, commissions — and finds where
money is **quietly leaking at the seams between systems**: commissions overpaid,
invoices under-billed, deals stalling, customers silently churned, revenue double-counted.
Each finding is traced to its cause and given a euro figure a non-technical manager can act on.

The principle behind it, in one line: *growth comes from removing obstruction in the value flow.*
This project finds the obstructions and prices them.

## Why this project is unusual

Every leak in the test data is **planted with known ground truth**, so the audit can be
*scored* rather than just demoed:

```
leak type                 planted  detected   match
commission_overpayment         18        18     yes
duplicate_revenue             137       137     yes
attribution_gap                48        48     yes
stalled_deal                   22        22     yes
silent_churn                   18        18     yes
under_billing                  24        24     yes
ALL DETECTIONS RECONCILE TO GROUND TRUTH
```

Findings are split by how real the money is — and that distinction is the judgement
the work is really demonstrating:

| Impact class | Meaning | Planted total |
|---|---|---|
| `recoverable_cash` | money you can actually claw back (overpaid / under-billed) | ~€152k |
| `overstated_revenue` | books / forecast overstated (double-billed / phantom ARR) | ~€1.45M |
| `revenue_at_risk` | not lost yet, but blind or fragile (attribution / stalls) | ~€5.24M |

The credible headline is the **recoverable cash**; the rest is integrity and risk, labelled
honestly rather than rolled into one inflated number.

## The leak catalog

| Leak | Where it hides | Detection technique |
|---|---|---|
| Commission overpayment | `commissions` ↔ `commission_plans` ↔ `opportunities` | reconciliation join + tolerance |
| Under-billing | `invoices` ↔ `contracts` | expected-vs-billed, after dedup |
| Attribution gap | `opportunities` ↔ `leads` | anti-join (null + dangling keys) |
| Stalled deals | `opportunity_stage_history` | window function: days-in-stage |
| Silent churn (phantom ARR) | `contracts` ↔ `invoices` ↔ dates | active but billing stopped 90+ days |
| Duplicate revenue | `invoices` | `row_number()` dedup |
| NRR decay | `contracts` by signup cohort | cohort retention logic |

## Data contract (this is also the client onboarding spec)

The generator emits ten CSVs. To run the audit on a **real** company, you replace
`generate_data.py` with an extract of their systems in exactly this shape — nothing
else in the project changes. So the schema below doubles as "here is the data we need from you."

- `accounts`, `reps`, `commission_plans` — dimensions
- `leads` → `opportunities` → `opportunity_stage_history` — the pipeline motion (CRM)
- `contracts` → `invoices` — the billing motion
- `commissions` — the comp motion
- `ground_truth_leaks` — the planted-truth ledger (synthetic only; a real client has no such file — that is the point)

## Stack

Runs locally on **DuckDB** (instant, zero infra) and is written **warehouse-agnostic**, so the
swap to **BigQuery** is a one-line change in `profiles.yml`. Snowflake is the same shape.

## Run it

```bash
python generate_data.py     # writes the ten seed CSVs + the score sheet
python validate.py          # runs detection in SQL and reconciles to ground truth
```

`validate.py` is the embryo of the audit — every query in it becomes a dbt model in stage 2.

## Roadmap

1. **Synthetic dataset + ground-truth leak ledger** — done
2. **dbt model layer** — done: 9 staging + 5 intermediate + 7 marts; 44 tests pass, including a calibration test that proves the marts reconcile to ground truth (`dbt build` is green end to end)
3. **Early-warning layer** — warn-severity alerts (a leak surfaces as a build warning), source freshness, and the richer reconciliation suite
4. **AI layer** — an LLM reads the flagged anomalies and writes the plain-language "what leaked, likely cause, euro impact"
5. **Stakeholder output** — Power BI dashboard + a written impact narrative + the recovered-vs-planted score

## Run the model layer

```bash
python generate_data.py                 # (re)generate the seeds
dbt seed  --profiles-dir .              # load CSVs into DuckDB
dbt run   --profiles-dir .              # build staging -> intermediate -> marts
dbt test  --profiles-dir .              # 44 tests incl. ground-truth reconciliation
```

`fct_leak_summary` is the scorecard; `int_contract_cohort_retention` holds the
mature-cohort NRR trend. To run on BigQuery, change the target in `profiles.yml`
to `bigquery` — no model changes.

— *By Aryan Mohammaddoost. Wishing you clarity and sustained focus.*
