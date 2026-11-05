# What does it really cost to send money from the UK to Nigeria?

An automated tracker that records, every day, what UK → Nigeria money transfer providers charge, including the cost hidden in the exchange rate and not just the advertised fee.

## How it works

- A GitHub Actions workflow (`.github/workflows/daily.yml`) runs every morning at 09:17 UTC.
- `track_quotes.py` asks the [Wise Comparison API](https://docs.wise.com/api-reference/comparison) for GBP → NGN quotes at **£120** and **£300**. These are the World Bank's standard UK send amounts, so the results line up with its historical data.
- Each run adds one row per provider per amount to `data/quotes.csv`, and saves the raw API responses in `data/raw/` so they can be checked later.

## The metric

**Total cost %** = what you would receive at the mid-market rate with no fee, minus what you actually receive, as a percentage of the first figure.

That one number captures both the upfront fee and the FX markup. The mid-market benchmark is the quote the API flags as mid-market.

## Data columns (`data/quotes.csv`)

| Column | Meaning |
|---|---|
| `run_utc` | When the tracker ran |
| `date_collected_utc` | When the price was collected (competitor prices may be a few hours old) |
| `amount_gbp` | Amount sent (120 or 300) |
| `provider` | Provider name |
| `fee_gbp` | Upfront fee in GBP |
| `rate_offered` | NGN per GBP the customer gets |
| `mid_market_rate` | Benchmark NGN per GBP |
| `fx_markup_pct` | How far the offered rate is below mid-market, in % |
| `received_ngn` | Naira the recipient gets |
| `total_cost_pct` | Fee + FX markup as % of the amount sent |

## Limitations

- Coverage depends on which providers the Wise API returns for this corridor (currently Wise, Xoom and Western Union).
- Wise both supplies the data and appears in it. Competitor quotes are Wise's own collections, so they may lag the live price by a few hours.
- Prices are quotes for a debit-card-funded transfer to a bank account and exclude promotions.

## Historical context

Long-run trends come from The World Bank, Remittance Prices Worldwide, available at http://remittanceprices.worldbank.org (CC BY 4.0).

---
Built by [Jonathan Kadiri](https://jonathankadiri.dev).
