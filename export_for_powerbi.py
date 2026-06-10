"""Export audit marts to CSV for Power BI. Run after `dbt build`."""
import os, duckdb
DB, OUT = "flow_audit.duckdb", "exports"
TABLES = ["fct_leak_summary", "fct_audit_calibration", "int_contract_cohort_retention"]
os.makedirs(OUT, exist_ok=True)
con = duckdb.connect(DB)
for t in TABLES:
    con.execute(f"COPY (SELECT * FROM main.{t}) TO '{OUT}/{t}.csv' (FORMAT CSV, HEADER)")
    print("exported", t)
print("Done -> ./exports")