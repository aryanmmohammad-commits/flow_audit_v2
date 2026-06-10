"""
Flow Audit v2 - validation harness
===================================

Loads the seed CSVs into DuckDB and runs the *detection* logic for each leak
type using ONLY the dirty data (never the ground-truth file). It then compares
what detection found to what was planted. A clean run means the audit logic that
stage 2 will move into dbt actually works: plant -> detect -> reconcile.

This is the embryo of the audit. Every query here becomes a dbt model later.

Run:  python validate.py
"""
import os
import duckdb

AS_OF = "DATE '2026-05-31'"
CHURN_CUTOFF = "DATE '2026-03-01'"   # ~90 days before as_of
STALL_DAYS = 100
SEEDS = os.path.join(os.path.dirname(__file__), "seeds")

con = duckdb.connect()
for t in ["commission_plans", "reps", "accounts", "leads", "opportunities",
          "opportunity_stage_history", "contracts", "invoices", "commissions",
          "ground_truth_leaks"]:
    con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('{SEEDS}/{t}.csv', header=true)")

# de-duplicated invoice base (a real reconciliation dedups before summing)
con.execute("""
CREATE VIEW invoices_dedup AS
SELECT * EXCLUDE (rn) FROM (
  SELECT *, row_number() OVER (PARTITION BY contract_id, period_month, amount
                               ORDER BY invoice_id) AS rn
  FROM invoices
) WHERE rn = 1
""")

# ---- detection queries: (count, euros) per leak type ----------------------
DETECT = {
"commission_overpayment": f"""
  SELECT count(*), round(sum(c.commission_amount - o.amount*p.commission_rate),2)
  FROM commissions c
  JOIN opportunities o ON c.opportunity_id=o.opportunity_id
  JOIN reps r          ON c.rep_id=r.rep_id
  JOIN commission_plans p ON r.commission_plan_id=p.commission_plan_id
  WHERE c.commission_amount - o.amount*p.commission_rate > 1
""",

"duplicate_revenue": """
  SELECT count(*), round(sum(amount),2) FROM (
    SELECT *, row_number() OVER (PARTITION BY contract_id, period_month, amount
                                 ORDER BY invoice_id) rn FROM invoices
  ) WHERE rn > 1
""",

"attribution_gap": """
  SELECT count(*), round(sum(o.amount),2)
  FROM opportunities o
  LEFT JOIN leads l ON o.lead_id=l.lead_id
  WHERE o.is_won = 1 AND (o.lead_id IS NULL OR o.lead_id = '' OR l.lead_id IS NULL)
""",

"stalled_deal": f"""
  WITH current_stage AS (
    SELECT opportunity_id, stage, entered_at
    FROM opportunity_stage_history WHERE exited_at IS NULL
  )
  SELECT count(*), round(sum(o.amount),2)
  FROM opportunities o
  JOIN current_stage s ON o.opportunity_id=s.opportunity_id
  WHERE o.is_closed = 0
    AND s.stage NOT IN ('Closed Won','Closed Lost')
    AND date_diff('day', s.entered_at, {AS_OF}) > {STALL_DAYS}
""",

"silent_churn": f"""
  WITH last_inv AS (
    SELECT contract_id, max(period_month) AS last_pm
    FROM invoices_dedup GROUP BY contract_id
  )
  SELECT count(*), round(sum(c.acv),2)
  FROM contracts c
  JOIN last_inv li ON c.contract_id=li.contract_id
  WHERE c.status = 'Active' AND c.end_date > {AS_OF}
    AND li.last_pm < {CHURN_CUTOFF}
""",

"under_billing": f"""
  WITH billed AS (
    SELECT contract_id, sum(amount) AS actual FROM invoices_dedup GROUP BY contract_id
  ),
  churned AS (
    SELECT c.contract_id
    FROM contracts c
    JOIN (SELECT contract_id, max(period_month) last_pm FROM invoices_dedup GROUP BY contract_id) li
      ON c.contract_id=li.contract_id
    WHERE c.status='Active' AND c.end_date > {AS_OF} AND li.last_pm < {CHURN_CUTOFF}
  )
  SELECT count(*), round(sum(expected-actual),2) FROM (
    SELECT c.contract_id,
      (c.acv/12.0) * (date_diff('month', date_trunc('month', c.start_date),
                                date_trunc('month', least(c.end_date, {AS_OF}))) + 1) AS expected,
      coalesce(b.actual,0) AS actual
    FROM contracts c
    LEFT JOIN billed b ON c.contract_id=b.contract_id
    WHERE c.contract_id NOT IN (SELECT contract_id FROM churned)
  ) WHERE expected - actual > 1
""",
}

planted = {r[0]: (r[1], r[2]) for r in con.execute(
    "SELECT leak_type, count(*), round(sum(euro_impact),2) FROM ground_truth_leaks GROUP BY leak_type"
).fetchall()}

print(f"{'leak type':<24}{'planted':>9}{'detected':>10}{'  match':>8}   euros detected")
print("-" * 78)
all_ok = True
for leak, sql in DETECT.items():
    dcount, deuro = con.execute(sql).fetchone()
    deuro = deuro or 0
    pcount, peuro = planted.get(leak, (0, 0))
    ok = (dcount == pcount)
    all_ok &= ok
    print(f"{leak:<24}{pcount:>9}{dcount:>10}{('  yes' if ok else '  NO'):>8}   "
          f"EUR {deuro:>13,.0f}")

print("-" * 78)
print("ALL DETECTIONS RECONCILE TO GROUND TRUTH" if all_ok
      else "MISMATCH - detection logic needs review")

# ---- NRR trend (engineered pattern, reported not pass/failed) -------------
print("\nNet revenue retention by signup cohort (should trend down for newer cohorts)")
print("-" * 78)
rows = con.execute(f"""
  WITH orig AS (
    SELECT strftime(start_date,'%Y-%m') cohort, contract_id, acv, status,
           opportunity_id, contract_id AS cid
    FROM contracts WHERE renewal_of = '' OR renewal_of IS NULL
  ),
  kept AS (
    SELECT o.cohort,
           sum(o.acv) AS orig_acv,
           sum(CASE WHEN o.status='Churned' THEN 0
                    WHEN o.status='Renewed' THEN coalesce(
                         (SELECT r.acv FROM contracts r WHERE r.renewal_of=o.cid), o.acv)
                    ELSE o.acv END) AS kept_acv,
           count(*) AS n
    FROM orig o GROUP BY o.cohort
  )
  SELECT cohort, n, orig_acv, kept_acv, kept_acv/orig_acv AS nrr
  FROM kept WHERE orig_acv > 0 ORDER BY cohort
""").fetchall()
for cohort, n, orig, kept, nrr in rows:
    bar = "#" * int(nrr * 30)
    print(f"  {cohort}  n={n:>3}  NRR {nrr:>5.0%}  {bar}")
