# Affiliate Tax Reporting (PayPal + Crypto)

## What this adds

Parlay Gorilla now records **every affiliate payout** in a way that’s usable for year-end tax filing:

- **PayPal payouts**: logs payout batch IDs, timestamps, and USD amounts.
- **Crypto payouts (USDC via Circle)**: logs the **asset amount**, **chain**, **tx hash**, and a **USD FMV snapshot** (valuation rate + source + timestamp + raw quote payload).

This creates an audit trail you can hand to an accountant or use to populate 1099-style totals.

## What is stored per payout (DB)

Table: `affiliate_payouts`

- **Gross payout amount (program)**: `amount` (USD)
- **Tax-reportable USD amount**: `tax_amount_usd` (USD FMV at payout time)
- **Method**: `payout_method` (`paypal` | `crypto`)
- **Provider reference**: `provider_payout_id` (PayPal batch ID / Circle transfer ID)
- **Crypto fields (if crypto)**:
  - `asset_symbol` (e.g. `USDC`)
  - `asset_amount`
  - `asset_chain`
  - `transaction_hash`
  - `valuation_usd_per_asset`
  - `valuation_source` (`coinbase_spot` or `stablecoin_peg`)
  - `valuation_at`
  - `valuation_raw` (JSON)

Association table: `affiliate_payout_commissions`
- Links payouts to the commission rows included in that payout.

## Admin exports (API)

All are admin-only.

### 1099-style summary

- **JSON**: `GET /api/admin/tax/affiliates/1099-nec?tax_year=2025`
- **CSV**: `GET /api/admin/tax/affiliates/1099-nec.csv?tax_year=2025`

Query params:
- `minimum_usd` (default `600`)
- `include_tin` (default `false`)  
  - If `true`, includes `tax_id_number` in the export.

### Payout-level ledger (audit trail)

- **JSON**: `GET /api/admin/tax/affiliates/payout-ledger?tax_year=2025`
- **CSV**: `GET /api/admin/tax/affiliates/payout-ledger.csv?tax_year=2025`

## Config / env vars

See `backend/.env.example` for the full list. Key ones:

- **PayPal**:
  - `PAYPAL_CLIENT_ID`
  - `PAYPAL_CLIENT_SECRET`
- **Circle (USDC)**:
  - `CIRCLE_API_KEY`
  - `CIRCLE_ENVIRONMENT` (`sandbox` | `production`)
- **Tax valuation snapshots**:
  - `TAX_VALUATION_EXTERNAL_ENABLED` (default `true`)
  - `TAX_VALUATION_TIMEOUT_SECONDS` (default `3.0`)

## Notes / disclaimer

This system is designed to **track and export** the data you typically need for US tax filing. Exact filing obligations (1099-NEC vs 1042-S, withholding, sourcing rules, etc.) can vary based on affiliate location and your business setup—confirm with a tax professional.


