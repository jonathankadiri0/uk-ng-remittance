"""
One-off test: which providers does the Wise Comparison API return for GBP -> NGN?

How to run (Windows PowerShell):
    pip install requests
    $env:WISE_TOKEN="paste-your-token-here"
    python test_wise.py

How to run (Mac / Linux):
    pip install requests
    export WISE_TOKEN="paste-your-token-here"
    python test_wise.py

Never put the token in this file or commit it to GitHub.
"""
import json
import os
import sys

import requests

TOKEN = os.environ.get("WISE_TOKEN")
if not TOKEN:
    sys.exit("No WISE_TOKEN found. Set it first (see the top of this file).")

URLS = [
    "https://api.wise.com/v4/comparisons/",       # long-standing version
    "https://api.wise.com/2026Q4/comparisons",    # newest documented version
]
PARAMS = {"sourceCurrency": "GBP", "targetCurrency": "NGN", "sendAmount": 120}
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

for url in URLS:
    print(f"\n=== Trying {url} ===")
    r = requests.get(url, params=PARAMS, headers=HEADERS, timeout=30)
    print("Status:", r.status_code)
    if r.status_code != 200:
        print(r.text[:500])
        continue

    data = r.json()
    with open("wise_sample_response.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Full response saved to wise_sample_response.json")

    providers = data.get("providers", [])
    print(f"\n{len(providers)} providers returned:")
    for p in providers:
        for q in p.get("quotes", [])[:1]:
            print(f"  - {p.get('name'):<25} fee={q.get('fee')}  rate={q.get('rate')}  "
                  f"received={q.get('receivedAmount')}")
        if not p.get("quotes"):
            print(f"  - {p.get('name'):<25} (no quote)")
    break
