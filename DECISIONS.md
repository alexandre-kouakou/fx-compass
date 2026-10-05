# Decisions log

Technical choices, newest at the bottom. Format: date — decision — why — alternatives considered.

## 2026-10-05 — Frankfurter v1 at api.frankfurter.dev
- **Why:** `api.frankfurter.app` now 301-redirects to `api.frankfurter.dev/v1/`. Calling the new URL directly avoids a redirect hop and surprises.
- **Alternatives:** keep old URL and follow redirects (works, but fragile).

## 2026-10-05 — AED: live from open.er-api.com, history derived from the USD peg
- **Why:** verified that ECB/Frankfurter has no AED. open.er-api.com is free, needs no key, and returns AED daily. AED has been pegged at 3.6725 per USD since 1997, so `AED per X = 3.6725 × (USD per X)` is accurate for history. Derived rows are tagged `source="derived_peg"` and shown as "derived".
- **Alternatives:** drop AED (breaks scope); paid API with full AED history (needs a key, overkill).

## 2026-10-05 — Store everything with base EUR, compute crosses on the fly
- **Why:** ECB publishes everything against EUR. Storing one row per (date, currency) vs EUR keeps the table ~10× smaller than storing every pair, and any cross (e.g. INR per USD) is a simple division. Selectable base in the UI comes from this.
- **Alternatives:** store all 90 pairs per day (redundant, can drift out of sync).

## 2026-10-05 — Frontend never calls external APIs
- **Why:** the app must work offline/when an API is down; all data comes from our DB via Django REST Framework.
