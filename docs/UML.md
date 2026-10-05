# UML diagrams

> Draft for team review. Diagrams are drawn from the actual code (`backend/` and `frontend/src/`). GitHub renders the Mermaid blocks directly.

## 1. Use case diagram

Mermaid has no native use-case diagram, so this is drawn as a flowchart: actors on the left, use cases (rounded) in the system boundary, external systems on the right.

```mermaid
flowchart LR
    G(["👤 Gurpreet<br/>exporter"])
    A(["👤 Aïcha<br/>student receiving money"])
    R(["👤 Rahul<br/>finance student"])
    T(["⚙️ Team member<br/>(admin, CLI)"])

    subgraph FX["FX Compass"]
        UC1("Choose base & quote currency")
        UC2("View daily reference rates")
        UC3("Convert an amount")
        UC4("Compare with 3-month average")
        UC5("View history chart 1W–5Y + stats")
        UC6("See daily gain/loss of a holding")
        UC7("Check volatility / risk level")
        UC8("View AI forecast vs naive baseline")
        UC9("Inspect model test metrics")
        UC10("View 10×10 strength heatmap")
        UC11("Create / remove rate alert")
        UC12("See triggered alerts")
        UC13("Backfill history / fetch rates")
        UC14("Pre-train all forecasts")
    end

    ECB[["Frankfurter / ECB"]]
    ER[["open.er-api.com"]]

    A --> UC1 & UC2 & UC3 & UC4 & UC6
    G --> UC1 & UC7 & UC8 & UC11 & UC12 & UC6
    R --> UC5 & UC8 & UC9 & UC10 & UC7
    T --> UC13 & UC14

    UC3 -. includes .-> UC4
    UC8 -. includes .-> UC9
    UC11 -. includes .-> UC12
    UC2 -. "may trigger refresh" .-> UC13
    UC13 --> ECB & ER
```

## 2. Class diagram

Django models (persisted) plus the main service modules (plain Python modules, drawn as classes with their public functions).

```mermaid
classDiagram
    direction LR

    class Currency {
        +CharField code PK
        +CharField name
        +CharField symbol
        +BooleanField in_ecb
    }
    class Rate {
        +DateField date
        +ForeignKey currency
        +DecimalField per_eur
        +CharField source
        +DateTimeField fetched_at
        SOURCE_ECB
        SOURCE_ER_API
        SOURCE_DERIVED_PEG
    }
    class FetchLog {
        +DateTimeField created_at
        +CharField source
        +BooleanField ok
        +IntegerField rows
        +DateField latest_date
        +TextField message
    }
    class ModelMetric {
        +CharField base
        +CharField quote
        +DateField data_until
        +int horizon
        +CharField model_name
        +float model_mae_pct
        +float baseline_mae_pct
        +float model_rmse_pct
        +float baseline_rmse_pct
        +DateField test_start
        +DateField test_end
        +int n_train
        +int n_test
    }
    class Forecast {
        +CharField base
        +CharField quote
        +DateField data_until
        +int horizon
        +DateField target_date
        +float predicted
        +float low
        +float high
        +float baseline
    }
    class Alert {
        +CharField client_id
        +CharField base
        +CharField quote
        +CharField direction
        +float threshold
        +DateTimeField triggered_at
        +float triggered_rate
        +DateField triggered_on
        +is_hit(rate) bool
    }
    Currency "1" --> "*" Rate : rates

    class rates_sources {
        <<module>>
        +fetch_frankfurter(start, end) dict
        +fetch_aed_live() tuple
    }
    class rates_services {
        <<module>>
        +ensure_currencies()
        +store_ecb_days(days) int
        +update_from_ecb(start) FetchLog
        +update_aed_live() FetchLog
        +refresh(full) tuple
        +refresh_if_stale()
        +last_success() FetchLog
    }
    class analytics_series {
        <<module>>
        RANGES
        +load_frames() tuple
        +pair(values, base, quote) Series
        +pair_source(sources, base, quote) Series
        +window(series, range_key) Series
    }
    class analytics_services {
        <<module>>
        +latest_rates(base) dict
        +convert(amount, base, quote) dict
        +history(base, quote, range) dict
        +gain_loss(base, quote, amount, range) dict
        +volatility(base, quote) dict
        +heatmap(range) dict
    }
    class forecasting_model {
        <<module>>
        HORIZON = 7
        TEST_FRACTION = 0.2
        LOOKBACK_YEARS = 5
        +make_features(series) DataFrame
        +make_targets(series) DataFrame
        +time_split(n, gap, test_fraction)
        +run(series) tuple
    }
    class HorizonResult {
        <<dataclass>>
        +int horizon
        +float model_mae_pct
        +float baseline_mae_pct
        +float model_rmse_pct
        +float baseline_rmse_pct
        +float err_lo
        +float err_hi
        +float pred_log_return
    }
    class forecasting_services {
        <<module>>
        +forecast(base, quote) dict
        -_train_and_store(base, quote, series)
    }
    class alerts_services {
        <<module>>
        +evaluate(alerts) dict
        +insight(alerts, current) str
    }
    class AlertSerializer {
        <<DRF ModelSerializer>>
        +validate(data)
    }

    rates_services ..> rates_sources : calls
    rates_services ..> Rate : upserts
    rates_services ..> FetchLog : logs
    rates_services ..> Currency : seeds
    analytics_series ..> Rate : reads all
    analytics_services ..> analytics_series
    forecasting_services ..> analytics_series
    forecasting_services ..> forecasting_model
    forecasting_model ..> HorizonResult : returns
    forecasting_services ..> ModelMetric : stores
    forecasting_services ..> Forecast : stores
    alerts_services ..> analytics_series
    alerts_services ..> Alert : updates
    AlertSerializer ..> Alert
```

## 3. Sequence diagram: "user converts currency"

Aïcha types 1000 USD → INR in the Converter.

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant C as Converter.jsx
    participant H as useApi hook
    participant CL as api/client.js
    participant V as analytics.views.convert
    participant P as analytics.params
    participant S as analytics.services.convert
    participant SE as analytics.series
    participant DB as SQLite (rates_rate)

    U->>C: types amount "1000" (base USD, quote INR from header)
    C->>H: useApi('/convert', {base, quote, amount})
    H->>CL: api.get('/convert', params)
    CL->>V: GET /api/convert?base=USD&quote=INR&amount=1000
    V->>P: pair(request), amount(request)
    alt invalid parameters
        P-->>V: ValidationError
        V-->>CL: 400 with field error, e.g. amount must be positive
        CL-->>H: throw Error(message)
        H-->>C: error
        C-->>U: "Couldn't load this widget: …"
    else valid
        P-->>V: ("USD", "INR"), 1000.0
        V->>S: convert(1000, "USD", "INR")
        S->>SE: load_frames()
        SE->>DB: SELECT date, currency_id, per_eur, source FROM rates_rate
        DB-->>SE: ~22k rows
        SE-->>S: values, sources (pivoted per trading day)
        S->>SE: pair(values, USD, INR) = INR/EUR ÷ USD/EUR
        S->>S: rate = last value, avg_3m = mean of last 63 days,<br/>vs_avg %, result = amount × rate, insight sentence
        S-->>V: dict
        V-->>CL: 200 JSON {rate, result, avg_3m, vs_avg_3m_pct, source, insight}
        CL-->>H: data
        H-->>C: data
        C-->>U: insight line, then result, rate (+ badge if AED), 3-month avg, vs average
    end
```

## 4. Sequence diagram: "alert check"

Alerts are checked when they are created and whenever the dashboard lists them (on page load). There is no background worker.

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant A as Alerts.jsx
    participant CL as api/client.js
    participant V as alerts.views.alert_list
    participant SV as alerts.services
    participant SE as analytics.series
    participant DB as SQLite

    Note over A: on mount, clientId() reads or creates<br/>fx-client-id in localStorage
    U->>A: opens dashboard
    A->>CL: GET /api/alerts?client_id=…
    CL->>V: request
    V->>V: _client_id() (400 if not 8–64 chars)
    V->>DB: SELECT * FROM alerts_alert WHERE client_id=…
    DB-->>V: alerts
    V->>SV: evaluate(alerts)
    SV->>SE: load_frames()
    SE->>DB: read all rates
    loop each alert
        SV->>SE: pair(values, base, quote) (cached per pair)
        SV->>SV: rate, day = latest value
        alt not yet triggered and is_hit(rate)
            SV->>DB: UPDATE alert SET triggered_at, triggered_rate, triggered_on
        end
    end
    SV-->>V: current_rates per pair, e.g. USD/INR = 96.32
    V->>SV: insight(alerts, current)
    V-->>CL: 200 {alerts, current_rates, insight}
    CL-->>A: data
    A-->>U: insight + list (▲ triggered / ○ waiting)

    U->>A: "Tell me when 1 USD is above 97 INR" → Add alert
    A->>CL: POST /api/alerts {client_id, base, quote, direction, threshold}
    CL->>V: request
    V->>V: AlertSerializer.is_valid() (400 on bad input)
    V->>DB: INSERT alert
    V->>SV: evaluate([alert]) (may trigger immediately)
    V-->>CL: 201 alert
    A->>A: reload() → GET /api/alerts again
```

## 5. Activity diagram: "daily fetch + alert check"

What happens from a dashboard request to updated data and alert states. The refresh is triggered by `GET /api/rates/latest` (or by running `fetch_rates` by hand); the alert check happens when the Alerts widget loads.

```mermaid
flowchart TD
    start([Dashboard opened]) --> req["LiveRates widget calls<br/>GET /api/rates/latest"]
    req --> stale{"Last ECB fetch attempt older than<br/>6 h (after success) or 15 min (after failure)?<br/>Or never fetched?"}
    stale -- no --> serve
    stale -- yes --> seed["ensure_currencies()"]
    seed --> start_date["start = last stored date<br/>(or HISTORY_START if empty)"]
    start_date --> ecb["GET Frankfurter /start..today<br/>symbols = 8 ECB currencies"]
    ecb --> ecbok{"Success?"}
    ecbok -- no --> logfail["FetchLog(source=ecb, ok=False, message)"]
    ecbok -- yes --> store["For each day: upsert EUR=1,<br/>8 ECB rates (source=ecb),<br/>AED = USD × 3.6725 (source=derived_peg)"]
    store --> logok["FetchLog(source=ecb, ok=True, rows, latest_date)"]
    logfail --> aed
    logok --> aed["GET open.er-api.com/v6/latest/USD"]
    aed --> aedok{"Success and<br/>ECB data exists?"}
    aedok -- yes --> aedstore["Overwrite AED on latest date =<br/>AED/USD (er-api) × USD/EUR (ECB)<br/>source=er_api; FetchLog ok"]
    aedok -- no --> aedfail["FetchLog(source=er_api, ok=False)"]
    aedstore --> serve
    aedfail --> serve
    serve["Answer from cached DB rows<br/>(latest rates + insight)"] --> header["Header reads /api/status:<br/>show 'last updated', and banner if<br/>last fetch failed or data > 4 days old"]
    header --> alerts["Alerts widget: GET /api/alerts?client_id"]
    alerts --> loop{"For each alert<br/>not yet triggered"}
    loop --> hit{"above: rate > threshold<br/>below: rate < threshold"}
    hit -- yes --> trig["Set triggered_at, triggered_rate, triggered_on"]
    hit -- no --> wait["Stays 'waiting'"]
    trig --> show
    wait --> show
    show(["Show alert list + insight"])
```
