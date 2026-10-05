# User manual

> Draft for team review. Replace each `[SCREENSHOT: …]` with a real screenshot before submission.

FX Compass has **one page**, the dashboard. It is made of widgets (cards). Each card answers a question in one plain sentence first, then shows the chart or numbers behind it. This manual covers installing the app, then each widget from top to bottom.

---

## Part A: Installation

### A.1 What you need

| Tool | Version | Check with |
|---|---|---|
| Python | 3.12 or newer (tested on 3.14) | `python3 --version` |
| Node.js | 20 or newer (tested on 22) | `node --version` |
| Git | any | `git --version` |
| Internet | only for the first data download; afterwards the app works from its saved data | |

No API keys or accounts are needed.

### A.2 Get the code and configure

```bash
git clone https://github.com/alexandre-kouakou/fx-compass.git
cd fx-compass
cp .env.example .env
```

Open `.env` and set `DJANGO_SECRET_KEY` to any long random string. Leave everything else as it is.

### A.3 Backend (first time)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py backfill_history    # downloads daily rates since 2018 (~10 s)
.venv/bin/python manage.py train_forecasts     # optional: pre-trains all 90 forecasts (~10 s)
```

`backfill_history` should end with two lines like `ecb: OK rows=2241 …` and `er_api: OK rows=1 …`. If it says `FAILED`, check your internet connection and run it again.

> **Windows:** use `.venv\Scripts\python` instead of `.venv/bin/python`.

### A.4 Frontend (first time), in a second terminal

```bash
cd frontend
npm install
```

### A.5 Start the app (every time)

Terminal 1:
```bash
cd backend
.venv/bin/python manage.py runserver          # API on http://localhost:8000/api/
```

Terminal 2:
```bash
cd frontend
npm run dev                                   # dashboard on http://localhost:5173
```

Open **http://localhost:5173** in a browser. To preview the phone layout, use your browser's device mode (e.g. Chrome DevTools → toggle device toolbar).

To open it on a real phone on the same Wi-Fi (untested, all on your computer): find your computer's IP (e.g. `192.168.1.20`), then in `.env` add it to `DJANGO_ALLOWED_HOSTS`, set `VITE_API_URL=http://192.168.1.20:8000/api`, add `http://192.168.1.20:5173` to `CORS_ALLOWED_ORIGINS`; start the backend with `runserver 0.0.0.0:8000` and the frontend with `npm run dev -- --host`, then open `http://192.168.1.20:5173` on the phone.

### A.6 Keeping data up to date

Nothing to do: whenever the dashboard is opened and the data is more than 6 hours old, the backend fetches the newest ECB day by itself. To force an update: `.venv/bin/python manage.py fetch_rates`.

### A.7 If something goes wrong

| You see | Meaning | Fix |
|---|---|---|
| "Can't reach the FX Compass API. Is the Django server running on port 8000?" | The frontend can't talk to the backend | Start `runserver` (A.5) |
| A card says "Couldn't load this widget: …" | That one request failed; the message says why | Usually a wrong currency choice; reload the page |
| Banner "▲ Showing saved data from <date>. The ECB source could not be reached…" | No internet, or the ECB source is down | Nothing; the app keeps working with saved data and retries automatically |
| Every card fails right after installing | The database is empty | Run `backfill_history` (A.3) |

[SCREENSHOT: the "Can't reach the API" message]

---

## Part B: Using the dashboard

[SCREENSHOT: full dashboard on a laptop, light mode]

[SCREENSHOT: full dashboard on a phone, scrolled to the top]

**Layout.** On a phone, all cards are in one column. On a laptop, the main analysis is on the left (Converter, History, Forecast, Gain/Loss), the quick-look cards on the right (Rates, Volatility, Alerts), and the heatmap across the bottom. Light or dark mode follows your device setting.

**Your choices are remembered.** The currency pair you pick is saved in your browser and restored next time.

### B.1 Header: choose your currencies

[SCREENSHOT: header with From / To selectors and the "last updated" line]

- **From** = the currency you have (the *base*). **To** = the currency you want (the *quote*). All cards except the heatmap use this pair.
- **⇄** swaps them.
- You can't pick the same currency on both sides (it is greyed out).
- Under the title: **"Daily reference rates · last updated <date>"**. These are the European Central Bank's once-a-day rates, not live market prices. The ECB doesn't publish on weekends or holidays, so on a Monday morning "last updated" shows Friday.
- If the data is more than 4 days old or the last download failed, a banner explains that you're seeing saved data.

### B.2 Converter: "Is today a good day to convert?"

[SCREENSHOT: Converter card with 1000 USD → INR]

1. Type an amount in the **Amount in <From>** box.
2. The result appears next to it.
3. The sentence on top compares today's rate with its **3-month average**, e.g. *"Today's USD→INR rate is 0.72% above its 3-month average, so you get more INR than usual."* Within ±0.25% it says "about the same".
4. Below: **Rate** (with its date), **3-month avg**, and **vs average** in %.

*For Aïcha:* if the rate is above average, sending money home today gets more than usual. It's a comparison with the recent past, not a prediction.

> Real conversions at a bank or money-transfer service include a margin; the result here is the reference rate only.

### B.3 Daily reference rates: all currencies at a glance

[SCREENSHOT: Daily reference rates list with a DERIVED/LIVE badge on AED]

- Shows what **1 <From>** buys in each of the other 9 currencies, and the change since the previous ECB trading day (▲ up / ▼ down).
- The top sentence names the biggest gain and the biggest drop.
- **Tap a currency** to make it the *To* currency for every other card.
- **AED badge:** the ECB doesn't publish the UAE dirham. **LIVE** = today's AED from open.er-api.com; **DERIVED** = calculated from the dirham's fixed peg (1 USD = 3.6725 AED). Hover or long-press the badge for the explanation.

### B.4 History chart: 1W / 1M / 6M / 1Y / 5Y

[SCREENSHOT: History chart, 1Y selected, with stats below]

1. Pick a period with the tabs (default 1M).
2. The sentence summarises the move, e.g. *"Over the past week, 1 USD rose 0.53% against INR (95.82 → 96.32), ranging 95.82–96.33."*
3. Hover or tap the line to see the rate on a given day.
4. Stats below: **Change** over the period, **Average** (and number of trading days), **Low** and **High** with their dates.

Weekends and ECB holidays have no rate and are skipped, not filled in.

### B.5 AI forecast: next 7 trading days

[SCREENSHOT: Forecast chart showing actual (blue), model (orange), naive (grey dashed) and the shaded range]

[SCREENSHOT: "Show how this was tested" expanded with the per-horizon table]

- The chart shows the last 60 trading days (**blue**), the model's forecast (**orange**), the **naive "no change"** line (grey dashed), and a **shaded 80% range**: in testing, 80% of the model's misses fell inside this band.
- The badge at the top right gives the honest verdict:
  - **● Beats naive baseline**: on the most recent year of data it never saw, the model's average error was more than 1% smaller than assuming "no change".
  - **▲ No better than naive**: it wasn't. The sentence then says to treat today's rate as the best guess and gives the 7-day range.
  - **● Pegged currency**: USD/AED doesn't move, so there is nothing to forecast.
- **Model avg. error / Naive avg. error**: average miss in % of the rate on the test period.
- **Show how this was tested** reveals the training/test sizes and dates and the error for each day ahead.

*For Gurpreet:* use the shaded range as a "how far could it move in a week" guide when deciding whether to wait before converting an invoice.

> Educational model, not financial advice. On data up to 2 Oct 2026 the model beat the baseline on 18 of 90 pairs. See [MODEL_REPORT.md](MODEL_REPORT.md).

### B.6 Daily gain / loss: "What did holding this currency earn me?"

[SCREENSHOT: Gain/loss bar chart, 1M, holding 10,000 USD valued in INR]

1. Enter the amount you hold in **If I hold … <From>, valued in <To>** (default 10,000).
2. Pick a period: 1W / 1M / 6M / 1Y.
3. Each bar is one trading day's change in value (**blue** = gained, **red** = lost).
4. The sentence gives the total plus the best and worst day; below are **Total** (amount and %), **Up days** and **Down days**.

### B.7 Volatility (risk)

[SCREENSHOT: Volatility card with risk pill and rolling volatility line]

- **Risk pill:** **● Low** (under 5% a year), **▲ Moderate** (5–10%), **◆ High** (over 10%).
- The sentence translates it into a typical daily move, e.g. *"…on a typical day it moves about ±0.23%…"*, and says whether it's calmer than, in line with, or more volatile than its own past year.
- Numbers: **Last 30 days** and **Past year** volatility (annualised), **Typical day** move.
- The small chart shows how 30-day volatility changed over the past year.

### B.8 Rate alerts

[SCREENSHOT: Alerts card with one waiting (○) and one triggered (▲) alert]

1. The form reads **"Tell me when 1 <From> is [above/below] [level] <To>"**. The level is pre-filled with today's rate.
2. Change the direction and level, then **Add alert**.
3. Each alert shows **○ Waiting**, or **▲ Triggered: <rate> on <date>** once the daily rate has crossed your level.
4. **Remove** deletes it.

How it works, plainly:
- Alerts are checked against each new **daily** rate when you open the dashboard. There are no push notifications, emails or SMS.
- If the condition is already true when you create the alert, it triggers straight away.
- Alerts belong to **this browser** (no account). Clearing your browser data, or using another browser or device, shows a different, empty list.

### B.9 Currency strength heatmap

[SCREENSHOT: 10×10 heatmap, 1M, with the strength ranking below]

- Pick a period: 1W / 1M / 3M / 1Y.
- **Read a cell as:** "1 unit of the **row** currency changed by this % when priced in the **column** currency." **Blue** = the row currency strengthened, **red** = weakened; stronger colour = bigger move. Hover a cell for the exact value.
- The sentence names the strongest and weakest currency (average change against the other nine).
- The numbered chips below rank all 10 currencies from strongest to weakest.
- On a phone, scroll the table sideways.

*For Rahul:* this is the quickest way to see whether a move in INR is about the rupee itself (its whole row is red) or about the other currency (only one column stands out).

### B.10 Footer

Data sources and attribution (ECB via Frankfurter; Rates By Exchange Rate API for AED), the "not real-time" note, the "not financial advice" note, and the team.
