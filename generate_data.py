"""
Flow Audit v2 - synthetic B2B SaaS revenue dataset generator
=============================================================

Generates a realistic, internally-consistent B2B SaaS revenue dataset and
deliberately injects KNOWN revenue leaks. Because every leak is planted with
known ground truth (see seeds/ground_truth_leaks.csv), the audit models built
on top of this data can be *scored*:

    "recovered EUR X of EUR Y planted leakage, caught N of M anomalies."

This file is the ONLY place leaks are introduced. The schema it emits is also
the data contract for real clients: to run the audit on a real company, you
replace this generator with an extract of their CRM / billing / comp data in
the same shape (see README.md -> Data contract).

Stack-agnostic: emits plain CSVs into ./seeds, consumed by dbt seeds on DuckDB
(local) or BigQuery (one-line profile change). Standard library only - no pip
dependencies, so it runs anywhere even behind a slow mirror.

Run:  python generate_data.py
"""

from __future__ import annotations
import calendar
import csv
import itertools
import os
import random
from datetime import date, timedelta

# ==========================================================================
# CONFIG - every knob lives here. Scale, dates, and leak rates are all tunable.
# The random seed makes the dataset (and therefore the ground truth) fully
# reproducible: same seed -> same planted euros every run.
# ==========================================================================
SEED = 42
AS_OF = date(2026, 5, 31)        # "today" from the audit's point of view
HISTORY_MONTHS = 24
N_ACCOUNTS = 500
N_REPS = 18
OUT_DIR = os.path.join(os.path.dirname(__file__), "seeds")

P_WON = 0.40                     # share of opportunities won
P_LOST = 0.35                    # share lost (remainder stay open)

# Leak rates (share of the relevant population)
RATE_COMMISSION_OVERPAY = 0.03   # of won opportunities
RATE_UNDERBILLING       = 0.04   # of contracts
RATE_ATTRIBUTION_GAP    = 0.08   # of won opportunities
RATE_STALLED            = 0.06   # of open opportunities
RATE_SILENT_CHURN       = 0.05   # of active contracts
RATE_DUPLICATE_INVOICE  = 0.02   # of invoices

OVERPAY_MULT = (1.30, 1.80)      # paid commission as a multiple of the correct one
STALL_DAYS = (150, 300)          # how long a planted stalled deal sits in-stage

HISTORY_START = date(AS_OF.year - 2, AS_OF.month, 1)

random.seed(SEED)

# --- id counters ----------------------------------------------------------
_lead = itertools.count(1)
_opp = itertools.count(1)
_hist = itertools.count(1)
_contract = itertools.count(1)
_invoice = itertools.count(1)
_commission = itertools.count(1)
_leak = itertools.count(1)

nid = lambda c, p, w=5: f"{p}{next(c):0{w}d}"

# --- ground-truth ledger --------------------------------------------------
# impact_class:
#   recoverable_cash   -> money you can actually claw back (overpaid / under-billed)
#   overstated_revenue -> books/forecast overstated (double-billed / phantom ARR)
#   revenue_at_risk    -> not lost yet, but blind or fragile (attribution / stalls)
ground_truth: list[dict] = []

def plant(leak_type, impact_class, entity_type, entity_id, euro, desc):
    ground_truth.append({
        "leak_id": nid(_leak, "GT", 4),
        "leak_type": leak_type,
        "impact_class": impact_class,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "euro_impact": round(euro, 2),
        "description": desc,
    })

# --- helpers --------------------------------------------------------------
def add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))

def months_inclusive(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1

def rand_date(a: date, b: date) -> date:
    span = (b - a).days
    return a + timedelta(days=random.randint(0, max(span, 0)))

def pick(seq, weights=None):
    return random.choices(seq, weights=weights, k=1)[0]

def money(x) -> float:
    return round(float(x), 2)

# word banks (kept small; this is fixture data, not a name service)
ADJ = ["North", "Apex", "Vertex", "Lumen", "Cobalt", "Harbor", "Summit", "Delta",
       "Orbit", "Ember", "Atlas", "Cedar", "Nova", "Quanta", "Pulse", "Slate"]
NOUN = ["Systems", "Labs", "Dynamics", "Logistics", "Analytics", "Networks",
        "Holdings", "Digital", "Works", "Group", "Solutions", "Industries"]
FIRST = ["Maya", "Liam", "Sofia", "Noah", "Elena", "Omar", "Hana", "Lucas",
         "Aria", "Jonas", "Nadia", "Ivan", "Petra", "Theo", "Yuki", "Sven",
         "Mira", "Adam"]
LAST = ["Rossi", "Vermeer", "Nowak", "Haas", "Bauer", "Dubois", "Lind", "Costa",
        "Berg", "Klein", "Moreau", "Sato", "Reyes", "Falk", "Aalto", "Brandt"]
INDUSTRY = ["SaaS", "Fintech", "Healthcare", "Logistics", "Retail",
            "Manufacturing", "Media", "Energy", "Education", "Telecom"]
COUNTRY = ["Netherlands", "Germany", "United Kingdom", "France", "Spain",
           "Denmark", "Sweden", "Ireland", "Belgium", "Italy"]
SEG = ["SMB", "Mid-Market", "Enterprise"]
SEG_W = [0.50, 0.35, 0.15]
ACV_RANGE = {"SMB": (5_000, 20_000), "Mid-Market": (20_000, 80_000),
             "Enterprise": (80_000, 300_000)}
LEAD_SRC = ["Inbound", "Outbound", "Event", "Referral", "Paid Search", "Partner"]
STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation"]

# ==========================================================================
# 1. DIMENSIONS: commission plans, reps, accounts
# ==========================================================================
commission_plans = [
    {"commission_plan_id": "CP1", "plan_name": "SMB Standard",   "commission_rate": 0.08, "floor_price": 5_000},
    {"commission_plan_id": "CP2", "plan_name": "Mid-Market",     "commission_rate": 0.10, "floor_price": 20_000},
    {"commission_plan_id": "CP3", "plan_name": "Enterprise",     "commission_rate": 0.12, "floor_price": 80_000},
]
plan_rate = {p["commission_plan_id"]: p["commission_rate"] for p in commission_plans}

reps = []
for i in range(1, N_REPS + 1):
    reps.append({
        "rep_id": f"R{i:03d}",
        "rep_name": f"{pick(FIRST)} {pick(LAST)}",
        "region": pick(["EMEA", "AMER", "APAC"], [0.6, 0.3, 0.1]),
        "commission_plan_id": pick(["CP1", "CP2", "CP3"], [0.5, 0.35, 0.15]),
        "hire_date": rand_date(date(AS_OF.year - 5, 1, 1), AS_OF - timedelta(days=120)).isoformat(),
    })
rep_ids = [r["rep_id"] for r in reps]

accounts = []
for i in range(1, N_ACCOUNTS + 1):
    seg = pick(SEG, SEG_W)
    accounts.append({
        "account_id": f"A{i:04d}",
        "account_name": f"{pick(ADJ)} {pick(NOUN)}",
        "industry": pick(INDUSTRY),
        "segment": seg,
        "country": pick(COUNTRY),
        "created_date": rand_date(HISTORY_START, AS_OF - timedelta(days=30)).isoformat(),
    })
acct_seg = {a["account_id"]: a["segment"] for a in accounts}
acct_ids = [a["account_id"] for a in accounts]

# ==========================================================================
# 2. OPPORTUNITIES + converting leads + stage history
# ==========================================================================
N_OPP = N_ACCOUNTS * 3
leads = []
opportunities = []
stage_history = []

def build_history(opp_id, created, end_dt, path, is_open):
    """Distribute the opp's life across its stage path; the current/closing
    stage has a null exit. Returns nothing - appends rows to stage_history."""
    if is_open:
        active = path                      # current stage included, no closing event
        bounds = [created]
        cuts = sorted(random.random() for _ in range(len(active) - 1))
        total = max((end_dt - created).days, len(active))
        for c in cuts:
            bounds.append(created + timedelta(days=int(c * total)))
        bounds.append(end_dt)
        for idx, st in enumerate(active):
            stage_history.append({
                "history_id": nid(_hist, "H", 6),
                "opportunity_id": opp_id,
                "stage": st,
                "entered_at": bounds[idx].isoformat(),
                "exited_at": "" if idx == len(active) - 1 else bounds[idx + 1].isoformat(),
            })
    else:
        pre = path[:-1]                    # working stages, then a closing event
        bounds = [created]
        cuts = sorted(random.random() for _ in range(max(len(pre) - 1, 0)))
        total = max((end_dt - created).days, len(pre))
        for c in cuts:
            bounds.append(created + timedelta(days=int(c * total)))
        bounds.append(end_dt)
        for idx, st in enumerate(pre):
            stage_history.append({
                "history_id": nid(_hist, "H", 6),
                "opportunity_id": opp_id,
                "stage": st,
                "entered_at": bounds[idx].isoformat(),
                "exited_at": bounds[idx + 1].isoformat(),
            })
        stage_history.append({                 # closing stage = event at close date
            "history_id": nid(_hist, "H", 6),
            "opportunity_id": opp_id,
            "stage": path[-1],
            "entered_at": end_dt.isoformat(),
            "exited_at": "",
        })

won_opps, open_opps = [], []
for _ in range(N_OPP):
    acct = pick(acct_ids)
    seg = acct_seg[acct]
    lo, hi = ACV_RANGE[seg]
    amount = money(random.randint(lo, hi))
    rep = pick(rep_ids)
    roll = random.random()
    if roll < P_WON:
        outcome = "won"
    elif roll < P_WON + P_LOST:
        outcome = "lost"
    else:
        outcome = "open"

    if outcome == "open":
        created = rand_date(AS_OF - timedelta(days=90), AS_OF - timedelta(days=5))
        cur_idx = random.randint(0, len(STAGES) - 1)
        stage = STAGES[cur_idx]
        path = STAGES[: cur_idx + 1]
        close_date = ""
        is_closed, is_won = 0, 0
        end_dt = AS_OF
    else:
        cycle = random.randint(20, 120)
        created = rand_date(HISTORY_START, AS_OF - timedelta(days=cycle + 1))
        close_dt = created + timedelta(days=cycle)
        close_date = close_dt.isoformat()
        is_closed = 1
        if outcome == "won":
            stage, is_won = "Closed Won", 1
            path = STAGES + [stage]
        else:
            stage, is_won = "Closed Lost", 0
            path = STAGES[: random.randint(1, 4)] + [stage]
        end_dt = close_dt

    # converting lead for this opp
    lead_created = created - timedelta(days=random.randint(3, 45))
    if lead_created < HISTORY_START:
        lead_created = HISTORY_START
    lead_id = nid(_lead, "L")
    leads.append({
        "lead_id": lead_id,
        "account_id": acct,
        "source": pick(LEAD_SRC),
        "created_date": lead_created.isoformat(),
        "status": "Converted",
    })

    opp_id = nid(_opp, "O")
    opportunities.append({
        "opportunity_id": opp_id,
        "account_id": acct,
        "lead_id": lead_id,
        "rep_id": rep,
        "created_date": created.isoformat(),
        "close_date": close_date,
        "stage": stage,
        "amount": amount,
        "is_closed": is_closed,
        "is_won": is_won,
    })
    build_history(opp_id, created, end_dt, path, is_open=(outcome == "open"))

    if outcome == "won":
        won_opps.append(opportunities[-1])
    elif outcome == "open":
        open_opps.append(opportunities[-1])

# a pool of non-converting leads (open / disqualified), unrelated to opps
for _ in range(N_OPP // 2):
    leads.append({
        "lead_id": nid(_lead, "L"),
        "account_id": pick(acct_ids),
        "source": pick(LEAD_SRC),
        "created_date": rand_date(HISTORY_START, AS_OF).isoformat(),
        "status": pick(["Open", "Disqualified"], [0.5, 0.5]),
    })

# ==========================================================================
# 3. CONTRACTS (won opp -> contract, with renewals/churn engineered by cohort
#    so that NEWER cohorts retain worse -> a visible NRR decline)
# ==========================================================================
contracts = []
opp_of_contract = {}

def cohort_recency(start: date) -> float:
    return min(max(months_inclusive(HISTORY_START, start) / HISTORY_MONTHS, 0.0), 1.0)

def make_contract(opp, start, acv, renewal_of=""):
    term = pick([12, 24, 36], [0.7, 0.2, 0.1])
    end = add_months(start, term)
    cid = nid(_contract, "C", 4)
    if end > AS_OF:
        status = "Active"
    else:
        rf = cohort_recency(start)
        churn_p = min(0.6, 0.20 + 0.30 * rf)
        status = "Churned" if random.random() < churn_p else "Renewed"
    row = {
        "contract_id": cid,
        "opportunity_id": opp["opportunity_id"],
        "account_id": opp["account_id"],
        "renewal_of": renewal_of,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "term_months": term,
        "acv": money(acv),
        "status": status,
    }
    contracts.append(row)
    opp_of_contract[cid] = opp
    # if it renewed, expansion factor degrades for newer cohorts (drives NRR down)
    if status == "Renewed":
        rf = cohort_recency(start)
        factor = pick([0.85, 1.0, 1.2, 1.5],
                      [0.20 + 0.30 * rf, 0.45, 0.25 - 0.10 * rf, 0.10 - 0.05 * rf])
        make_contract(opp, end, acv * factor, renewal_of=cid)
    return row

for opp in won_opps:
    make_contract(opp, date.fromisoformat(opp["close_date"]), opp["amount"])

# ==========================================================================
# 4. INVOICES (monthly, clean) and 5. COMMISSIONS (clean)
# ==========================================================================
invoices = []
inv_of_contract = {}

def gen_invoices(contract):
    start = date.fromisoformat(contract["start_date"])
    end = date.fromisoformat(contract["end_date"])
    cap = min(end, AS_OF)
    monthly = money(contract["acv"] / 12.0)
    anchor = date(start.year, start.month, 1)
    rows, k = [], 0
    while add_months(anchor, k) <= date(cap.year, cap.month, 1):
        pm = add_months(anchor, k)
        rows.append({
            "invoice_id": nid(_invoice, "INV", 6),
            "contract_id": contract["contract_id"],
            "account_id": contract["account_id"],
            "invoice_date": pm.isoformat(),
            "period_month": pm.isoformat(),
            "amount": monthly,
        })
        k += 1
    inv_of_contract[contract["contract_id"]] = rows
    invoices.extend(rows)

for c in contracts:
    gen_invoices(c)

commissions = []
comm_of_opp = {}
for opp in won_opps:
    rep_plan = next(r for r in reps if r["rep_id"] == opp["rep_id"])["commission_plan_id"]
    correct = money(opp["amount"] * plan_rate[rep_plan])
    cid = next((c["contract_id"] for c in contracts
                if c["opportunity_id"] == opp["opportunity_id"] and c["renewal_of"] == ""), "")
    row = {
        "commission_id": nid(_commission, "CM", 5),
        "opportunity_id": opp["opportunity_id"],
        "rep_id": opp["rep_id"],
        "contract_id": cid,
        "commission_amount": correct,
        "paid_date": (date.fromisoformat(opp["close_date"]) + timedelta(days=30)).isoformat(),
    }
    commissions.append(row)
    comm_of_opp[opp["opportunity_id"]] = row

# ==========================================================================
# 6. INJECT LEAKS  (the only place the data is corrupted; all recorded as truth)
# ==========================================================================
def sample(pop, rate):
    n = max(1, round(len(pop) * rate))
    return random.sample(pop, min(n, len(pop)))

# 6a. Commission overpayment ------------------------------------------------
for opp in sample(won_opps, RATE_COMMISSION_OVERPAY):
    row = comm_of_opp[opp["opportunity_id"]]
    correct = row["commission_amount"]
    mult = random.uniform(*OVERPAY_MULT)
    row["commission_amount"] = money(correct * mult)
    plant("commission_overpayment", "recoverable_cash", "commission",
          row["commission_id"], row["commission_amount"] - correct,
          f"Paid {mult:.2f}x the plan rate on opp {opp['opportunity_id']}")

# 6b. Attribution gap (won opp's lead link broken) --------------------------
for i, opp in enumerate(sample(won_opps, RATE_ATTRIBUTION_GAP)):
    orig = next(o for o in opportunities if o["opportunity_id"] == opp["opportunity_id"])
    orig["lead_id"] = "" if i % 10 < 7 else f"L9999{i:02d}"   # null OR dangling
    plant("attribution_gap", "revenue_at_risk", "opportunity",
          opp["opportunity_id"], opp["amount"],
          "Won revenue with no resolvable source lead")

# 6c. Stalled deals (open opp parked in-stage) ------------------------------
hist_by_opp = {}
for h in stage_history:
    hist_by_opp.setdefault(h["opportunity_id"], []).append(h)
for opp in sample(open_opps, RATE_STALLED):
    rows = hist_by_opp[opp["opportunity_id"]]
    current = rows[-1]
    entered = AS_OF - timedelta(days=random.randint(*STALL_DAYS))
    current["entered_at"] = entered.isoformat()
    if len(rows) >= 2:
        rows[-2]["exited_at"] = entered.isoformat()
    plant("stalled_deal", "revenue_at_risk", "opportunity",
          opp["opportunity_id"], opp["amount"],
          f"Parked in {current['stage']} for {(AS_OF - entered).days} days")

# partition contracts so under-billing and silent-churn never overlap
active_contracts = [c for c in contracts if c["status"] == "Active"
                    and len(inv_of_contract[c["contract_id"]]) >= 6]
churn_targets = set(c["contract_id"] for c in sample(active_contracts, RATE_SILENT_CHURN))

billable = [c for c in contracts
            if c["contract_id"] not in churn_targets
            and len(inv_of_contract[c["contract_id"]]) >= 4]

# 6d. Under-billing (drop the most recent invoice on a live contract) -------
for c in sample(billable, RATE_UNDERBILLING):
    rows = sorted(inv_of_contract[c["contract_id"]], key=lambda r: r["period_month"])
    dropped = rows[-1]
    invoices.remove(dropped)
    inv_of_contract[c["contract_id"]].remove(dropped)
    plant("under_billing", "recoverable_cash", "contract",
          c["contract_id"], dropped["amount"],
          f"Missing invoice for period {dropped['period_month']}")

# 6e. Silent churn (active contract stops billing 3-5 months ago) -----------
for cid in churn_targets:
    c = next(c for c in contracts if c["contract_id"] == cid)
    rows = sorted(inv_of_contract[cid], key=lambda r: r["period_month"])
    drop_n = random.randint(3, 5)
    for d in rows[-drop_n:]:
        invoices.remove(d)
        inv_of_contract[cid].remove(d)
    plant("silent_churn", "overstated_revenue", "contract", cid, c["acv"],
          f"Marked Active but no billing for ~{drop_n} months (phantom ARR)")

# 6f. Duplicate revenue (clone an existing invoice) -------------------------
for inv in sample(list(invoices), RATE_DUPLICATE_INVOICE):
    dup = dict(inv)
    dup["invoice_id"] = nid(_invoice, "INV", 6)
    invoices.append(dup)
    plant("duplicate_revenue", "overstated_revenue", "invoice",
          dup["invoice_id"], dup["amount"],
          f"Duplicate of {inv['invoice_id']} ({inv['period_month']})")

# 6g. NRR decay - engineered by cohort; record the worst cohorts as truth ----
cohort_orig, cohort_kept = {}, {}
for c in contracts:
    if c["renewal_of"]:
        continue
    key = c["start_date"][:7]                 # YYYY-MM cohort
    cohort_orig[key] = cohort_orig.get(key, 0) + c["acv"]
    if c["status"] == "Churned":
        kept = 0.0
    elif c["status"] == "Renewed":
        ren = next((x for x in contracts if x["renewal_of"] == c["contract_id"]), None)
        kept = ren["acv"] if ren else c["acv"]
    else:
        kept = c["acv"]                        # still in initial term
    cohort_kept[key] = cohort_kept.get(key, 0) + kept

for key in sorted(cohort_orig):
    orig = cohort_orig[key]
    nrr = cohort_kept[key] / orig if orig else 1.0
    if nrr < 0.95 and orig > 0:                # only flag cohorts that actually decayed
        plant("nrr_decay", "revenue_at_risk", "cohort", key, orig - cohort_kept[key],
              f"Cohort net revenue retention {nrr:.0%}")

# ==========================================================================
# 7. WRITE CSVs
# ==========================================================================
def write(name, rows, fields):
    path = os.path.join(OUT_DIR, f"{name}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return len(rows)

tables = {
    "commission_plans": (commission_plans, ["commission_plan_id", "plan_name", "commission_rate", "floor_price"]),
    "reps": (reps, ["rep_id", "rep_name", "region", "commission_plan_id", "hire_date"]),
    "accounts": (accounts, ["account_id", "account_name", "industry", "segment", "country", "created_date"]),
    "leads": (leads, ["lead_id", "account_id", "source", "created_date", "status"]),
    "opportunities": (opportunities, ["opportunity_id", "account_id", "lead_id", "rep_id", "created_date", "close_date", "stage", "amount", "is_closed", "is_won"]),
    "opportunity_stage_history": (stage_history, ["history_id", "opportunity_id", "stage", "entered_at", "exited_at"]),
    "contracts": (contracts, ["contract_id", "opportunity_id", "account_id", "renewal_of", "start_date", "end_date", "term_months", "acv", "status"]),
    "invoices": (invoices, ["invoice_id", "contract_id", "account_id", "invoice_date", "period_month", "amount"]),
    "commissions": (commissions, ["commission_id", "opportunity_id", "rep_id", "contract_id", "commission_amount", "paid_date"]),
    "ground_truth_leaks": (ground_truth, ["leak_id", "leak_type", "impact_class", "entity_type", "entity_id", "euro_impact", "description"]),
}

print("Rows written")
print("-" * 40)
for name, (rows, fields) in tables.items():
    n = write(name, rows, fields)
    print(f"  {name:<28} {n:>6}")

# ==========================================================================
# 8. SUMMARY of planted leaks (this is the score sheet stage 5 reconciles to)
# ==========================================================================
from collections import defaultdict
by_type = defaultdict(lambda: [0, 0.0])
by_class = defaultdict(lambda: [0, 0.0])
for g in ground_truth:
    by_type[g["leak_type"]][0] += 1
    by_type[g["leak_type"]][1] += g["euro_impact"]
    by_class[g["impact_class"]][0] += 1
    by_class[g["impact_class"]][1] += g["euro_impact"]

print("\nPlanted leaks by type")
print("-" * 52)
for t, (c, e) in sorted(by_type.items()):
    print(f"  {t:<24} {c:>4} leaks   EUR {e:>14,.0f}")

print("\nPlanted leaks by impact class")
print("-" * 52)
for t, (c, e) in sorted(by_class.items()):
    print(f"  {t:<24} {c:>4} leaks   EUR {e:>14,.0f}")
print("-" * 52)
print(f"  {'TOTAL':<24} {len(ground_truth):>4} leaks   "
      f"EUR {sum(g['euro_impact'] for g in ground_truth):>14,.0f}")
