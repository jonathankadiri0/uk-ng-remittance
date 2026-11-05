"""
Daily UK -> Nigeria remittance quote tracker.

Asks the Wise Comparison API what each provider charges to send GBP -> NGN,
for the World Bank's standard UK amounts (GBP 120 and GBP 300), and appends
one row per provider per amount to data/quotes.csv.

Runs automatically every day via GitHub Actions (.github/workflows/daily.yml).
Needs a read-only Wise API token in the WISE_TOKEN environment variable.
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

AMOUNTS_GBP = [120, 300]
URL = "https://api.wise.com/v4/comparisons/"
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
CSV_PATH = DATA_DIR / "quotes.csv"

COLUMNS = [
    "run_utc",            # when this script ran
    "date_collected_utc", # when Wise collected that provider's price
    "amount_gbp",
    "provider",
    "provider_alias",
    "provider_type",
    "fee_gbp",
    "rate_offered",       # NGN per GBP the customer gets
    "mid_market_rate",    # benchmark NGN per GBP (Wise's mid-market quote)
    "fx_markup_pct",      # how much worse than mid-market the rate is, as reported by Wise
    "received_ngn",
    "total_cost_pct",     # (what you'd get at mid-market with no fee - what you get) / that, x100
]


def fetch(amount, token):
    """Ask Wise for quotes. Try a request for more providers first, fall back to the basic one."""
    headers = {"Authorization": f"Bearer {token}"}
    base = {"sourceCurrency": "GBP", "targetCurrency": "NGN", "sendAmount": amount}
    attempts = [
        {**base, "sourceCountry": "GB", "targetCountry": "NG", "numberOfProviders": 20},
        {**base, "numberOfProviders": 20},
        base,
    ]
    for params in attempts:
        r = requests.get(URL, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.json()
        print(f"  {r.status_code} with {params}: {r.text[:200]}")
    sys.exit(f"Wise API failed for GBP {amount}. See messages above.")


def to_rows(data, amount, run_utc):
    """Turn one API response into CSV rows."""
    providers = data.get("providers", [])

    # The benchmark: the quote Wise flags as mid-market (its own).
    mid = None
    for p in providers:
        for q in p.get("quotes", []):
            if q.get("isConsideredMidMarketRate"):
                mid = q.get("rate")

    rows = []
    for p in providers:
        for q in p.get("quotes", []):
            received = q.get("receivedAmount")
            total_cost = None
            if mid and received is not None:
                ideal = amount * mid
                total_cost = round((ideal - received) / ideal * 100, 3)
            rows.append({
                "run_utc": run_utc,
                "date_collected_utc": q.get("dateCollected"),
                "amount_gbp": amount,
                "provider": p.get("name"),
                "provider_alias": p.get("alias"),
                "provider_type": p.get("type"),
                "fee_gbp": q.get("fee"),
                "rate_offered": q.get("rate"),
                "mid_market_rate": mid,
                "fx_markup_pct": q.get("markup"),
                "received_ngn": received,
                "total_cost_pct": total_cost,
            })
    return rows


def main():
    token = os.environ.get("WISE_TOKEN")
    if not token:
        sys.exit("No WISE_TOKEN set.")

    run_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    today = run_utc[:10]
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_rows = []
    for amount in AMOUNTS_GBP:
        print(f"Fetching GBP {amount} -> NGN")
        data = fetch(amount, token)
        # Keep the untouched response as evidence, in case we need to re-check anything later.
        (RAW_DIR / f"{today}_gbp{amount}.json").write_text(json.dumps(data, indent=2))
        rows = to_rows(data, amount, run_utc)
        for r in rows:
            print(f"  {r['provider']:<22} fee={r['fee_gbp']}  rate={r['rate_offered']}  "
                  f"received={r['received_ngn']}  total_cost={r['total_cost_pct']}%")
        all_rows.extend(rows)

    new_file = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            w.writeheader()
        w.writerows(all_rows)
    print(f"\nAdded {len(all_rows)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
