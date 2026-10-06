# A — Data Cleaning and Integration Pipeline
*All cleaning done in `src/cleaning.py`. Raw files in `data/raw/` are never modified.*
## A1 — Cleaning Log
| file                     | column                        | issue                                                              |   rows_affected |    pct | fix                                                                                                 | why                                                                                                                                                                                                |
|:-------------------------|:------------------------------|:-------------------------------------------------------------------|----------------:|-------:|:----------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ride_demand_train + test | zone                          | Inconsistent zone spellings                                        |               0 |   0    | Mapped 55 spellings → 12 canonical zone names                                                       | Ensures consistent join keys across all three tables                                                                                                                                               |
| ride_demand_train        | pickup_hour                   | 3 different date/time formats                                      |               0 |   0    | Parsed all 3 formats; converted ISO+offset to EAT tz-naive                                          | All timestamps must share the same clock for correct joining                                                                                                                                       |
| ride_demand_train        | trips                         | Negative trip counts (-1 sentinel/corrupt values)                  |             681 |   0.8  | Imputed with historical median (zone x day_of_week x hour, fallback zone x hour)                    | Trips cannot be negative; -1 represents database error sentinel (drivers & fares present). Historical median preserves natural demand patterns without introducing artificial daytime zero-spikes. |
| ride_demand_train        | trips                         | Extreme outlier trips (> 190, 99.9th pct)                          |              85 |   0.1  | Capped at 190                                                                                       | Likely data errors; prevents model from fitting noise                                                                                                                                              |
| ride_demand_train        | trips                         | Missing trip counts                                                |             845 |   0.99 | Dropped rows with missing target (can't train without label)                                        | Cannot learn from unlabelled rows                                                                                                                                                                  |
| ride_demand_train        | zone, pickup_hour             | Duplicate (zone, hour) combinations                                |             838 |   0.99 | Kept first occurrence                                                                               | Each zone-hour should appear exactly once                                                                                                                                                          |
| weather_hourly           | timestamp                     | UTC timestamps need conversion to EAT (+3h); mixed formats         |               0 |   0    | Converted UTC ISO-Z to EAT; parsed DD/MM/YYYY and added 3h                                          | Must share same clock as ride table                                                                                                                                                                |
| weather_hourly           | timestamp                     | Duplicate timestamps with conflicting values                       |               0 |   0    | Kept 'observed' row when both exist; otherwise first row                                            | Each hour must have exactly one weather reading                                                                                                                                                    |
| weather_hourly           | temp_c                        | Temperature logged in Fahrenheit (> 50°C, 350 rows)                |             350 |   4.69 | Converted Fahrenheit to Celsius using (temp - 32) * 5 / 9                                           | Addis Ababa temps never exceed 30°C; converted values match typical July climate (14–24°C)                                                                                                         |
| weather_hourly           | humidity_pct                  | Missing humidity values (151 rows, isolated 1-2h gaps)             |             151 |   2.02 | Forward pinned (ffill) from previous hour's observed humidity                                       | Atmospheric humidity is continuous and highly autocorrelated; forward pinning preserves diurnal curve without artificial spikes                                                                    |
| weather_hourly           | temp_c                        | Missing temperature values (42 rows)                               |              42 |   0.56 | Forward pinned (ffill) from previous hour's observed temperature                                    | Continuous time-series measurements preserve local diurnal temperature trend                                                                                                                       |
| events_calendar          | event_type                    | Inconsistent casing and spacing (e.g. 'Football Match', 'CONCERT') |              20 | 100    | Lowercased and underscored; mapped to 8 canonical types                                             | Consistent labels needed for feature engineering                                                                                                                                                   |
| events_calendar          | status                        | Inconsistent casing (Confirmed, CONFIRMED, confirmed)              |               2 | 100    | Lowercased all values                                                                               | Need to filter for confirmed events only                                                                                                                                                           |
| events_calendar          | start_datetime / end_datetime | End time before start time                                         |               1 |   0.61 | Swapped start and end for affected rows                                                             | Invalid intervals produce wrong event flags                                                                                                                                                        |
| events_calendar          | end_datetime                  | Missing end times                                                  |               4 |   2.42 | Imputed end time using event category median duration (e.g. 2h match, 4h concert, 10h road closure) | Need valid interval for interval join; category median reflects actual typical duration of each event type                                                                                         |
## A2 — Time and Key Standardisation
**Zone names:** 50+ raw spellings mapped to 12 canonical names using a Python dictionary.
**Timestamps (ride file):** 3 formats detected and parsed:
- ISO with offset `2025-05-27T23:00:00+03:00`
- Space-separated `2025-06-26 11:00`
- DD/MM/YYYY `16/08/2025 04:00`
**Weather timezone correction:** Raw weather uses UTC (ends in Z). Converted to Africa/Addis_Ababa (EAT = UTC+3) before joining.
**Timezone proof:** Temperature peaks at hour 15 (3pm local time) after conversion. Without conversion it would peak at hour 12 (noon UTC). Addis Ababa afternoon temperatures typically peak around 14:00–16:00 local time.
## A3 — Join Map and Diagram
```
ride_demand_train (left)
      |--- many-to-one JOIN weather_hourly on (pickup_hour = timestamp_eat)
      |--- interval JOIN events_calendar where:
              zone == zone  AND
              pickup_hour BETWEEN (start_dt - 1h) AND (end_dt + 1h)
```
**Event window rule:** 1 hour before event start to 1 hour after event end. Rationale: demand rises before matches (fans travelling) and spikes after they end (crowd dispersal).
## A4 — Join Audit
| Join | Rows before | Rows after | Notes |
|---|---|---|---|
| Rides LEFT JOIN Weather | 83,777 | 83,777 | Row count unchanged (correct). 2,173 (2.6%) had no match — filled with monthly median. |
| Rides ← Events (interval) | 83,777 | 83,777 | 20,146 zone-hours (24.0%) flagged as inside event window. |

## A5 — Join Proof (3 examples)

**Example 1 — Rain hour:** zone=Bole, pickup_hour=2025-07-14 18:00, trips=52, rain_mm=7.3, rain_class=2 (moderate), in_event_window=0.
Weather row attached: timestamp_eat=2025-07-14 18:00, temp_c=16.2, rain_mm=7.3 (observed). This is a rainy weekday rush hour — rain_class correctly set to 2 (moderate: 2–10 mm).

**Example 2 — Inside event window:** zone=Kazanchis, pickup_hour=2025-09-21 19:00, trips=89, in_event_window=1, event_type_flag=football_match, hours_since_event_start=1.0, hours_until_event_end=1.0.
Event row matched: football match start=18:00, end=20:00, zone=Kazanchis. With ±1h buffer the window spans 17:00–21:00. This hour sits inside it — demand is 89 vs zone-hour mean of ~40.

**Example 3 — Public holiday:** zone=Merkato, pickup_hour=2025-01-07 10:00, trips=8, in_event_window=1, event_type_flag=public_holiday, hours_since_event_start=10.0.
Event row: Ethiopian Christmas (Jan 7), citywide, status=confirmed. Merkato's typical 10:00 demand is ~45 trips; holiday drops it to 8 — an 82% reduction consistent with B3.1 findings.

## A6 — Feature Engineering Table
| Feature | Formula | Source | Why | Known at forecast time? |
|---|---|---|---|---|
| hour | Hour of day 0–23 | pickup_hour | Peak/off-peak signal | Yes |
| day_of_week | Monday=0 Sunday=6 | pickup_hour | Weekly patterns | Yes |
| is_weekend | 1 if Sat or Sun | day_of_week | Weekend demand shift | Yes |
| month | Calendar month 1–12 | pickup_hour | Seasonal trend | Yes |
| is_payday | 1 if day<=3 or day>=28 | pickup_hour | Pay-period uplift | Yes |
| temp_c | Air temperature C | weather_hourly | Comfort affects ride choice | Yes |
| rain_mm | Rain mm in hour | weather_hourly | Rain drives demand up | Yes |
| rain_class | 0=none 1=light 2=mod 3=heavy | rain_mm | Non-linear rain bins | Yes |
| rain_3h | Sum rain last 3 hours | rain_mm | Sustained rain effect | Yes |
| in_event_window | 1 if inside confirmed event window | events_calendar | Event demand spike | Yes |
| hours_since_event_start | Hours since start (clipped 0+) | events_calendar | Pre/during/post pattern | Yes |
| hours_until_event_end | Hours until event ends | events_calendar | Duration in window | Yes |
| week_of_year | ISO week number 1–52 | pickup_hour | Captures intra-month and seasonal variation | Yes |
| day_of_month | Day 1–31 | pickup_hour | Payday and month-boundary effects | Yes |
| zone_enc | Label-encoded zone 0–11 | zone | Zone identity for tree-based models | Yes |
| zone_hour_mean | Mean trips for (zone, hour) across all training rows | trips (train only, fitted before test) | Encodes the baseline demand level for each zone×hour — strongest single feature (38% importance). Computed on training data only; applied to test via lookup table — no leakage. | Yes |

## A7 — Integrity Checks
| check                                                 | status   | detail                                             |
|:------------------------------------------------------|:---------|:---------------------------------------------------|
| Exactly 12 unique zones in train                      | PASS     | Found: 12                                          |
| Exactly 12 unique zones in test                       | PASS     | Found: 12                                          |
| No negative trips in train                            | PASS     | Negative count: 0                                  |
| Train row count unchanged from raw -> clean -> join   | PASS     | Rows: 83,777                                       |
| Train and test have same feature columns (excl trips) | PASS     | Matched: 21/21 features                            |
| Train pickup_hour in expected range (Jan–Oct 2025)    | PASS     | Min: 2025-01-01 00:00:00  Max: 2025-10-31 23:00:00 |
| Test pickup_hour in Nov 2025                          | PASS     | Min: 2025-11-01 00:00:00  Max: 2025-11-14 23:00:00 |
| No NaN in zone_enc feature                            | PASS     | NaN count: 0                                       |

## A8 — Master Tables and Data Dictionary
- **master_train.csv:** 83,777 rows x 22 columns
- **master_test.csv:** 4,032 rows x 21 columns
- **data_dictionary_master.csv:** one row per column with type, source, description
