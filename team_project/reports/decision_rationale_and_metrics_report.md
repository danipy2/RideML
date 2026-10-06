# Comprehensive Decision Rationale & Model Accuracy Report
**Project:** Qiyas AI Hackathon #2 — Addis Ababa Ride Demand Forecasting  
**Team:** Team Qiyas  
**Validation Window:** October 18 – October 31, 2025 (3,958 zone-hour holdout intervals)  
**Primary Metrics:** **$R^2 = 0.9145$ (91.45%)** | **$\text{RMSE} = 7.99\text{ trips/h}$** | **$\text{MAE} = 5.22\text{ trips/h}$** (15.6% relative error)

---

## 1. Executive Metric Summary: Baseline vs. Iterative Progression

Every decision made throughout the pipeline was evaluated on an un-seen, strictly chronological validation holdout (**October 18–31, 2025**). The table below demonstrates how each progressive refinement reduced prediction error and increased explained variance:

| Model / Pipeline Milestone | RMSE (trips/h) | MAE (trips/h) | Relative Error (% of Mean Demand) | $R^2$ Variance Explained |
| :--- | :---: | :---: | :---: | :---: |
| **Global Mean Baseline** | 27.80 | 20.76 | 62.0% | 0.00% |
| **Seasonal Naive Baseline** *(Same hour last week)* | 11.99 | 7.37 | 22.0% | 79.20% |
| **Linear Model (Ridge Regression)** | 14.79 | 10.35 | 30.9% | 68.45% |
| **Random Forest (100 Trees)** | 9.91 | 6.24 | 18.6% | 87.12% |
| **Histogram Gradient Boosting** | 9.47 | 6.07 | 18.1% | 88.24% |
| **Initial LightGBM** *(Zero-clip negatives, flat +2h events, monthly weather means)* | 8.63 | 5.42 | 16.2% | 90.12% |
| **Intermediate LightGBM** *(Historical median imputation for negatives + category event durations)* | 8.00 | 5.26 | 15.7% | 91.43% |
| **Final LightGBM** *(+ Forward pinning humidity, Fahrenheit to Celsius fix)* | **7.99** | **5.22** | **15.6%** | **91.45%** |

---

## 2. Decision-by-Decision Rationale & Empirical Results

### Decision 1: Imputing Negative Trips via Historical Median (vs. Zero-Clipping)
* **The Raw Problem:** 681 rows contained negative trip counts, all with values of exactly `-1.0`.
* **The Analysis:** When cross-referenced against operational indicators, these rows had 60–70 active drivers and collected 250–320 Birr in average fares during daytime rush hours. `-1.0` was an automated **system error sentinel**, not actual zero demand.
* **Why We Chose Historical Median:**
  * Setting `-1.0` to `0` introduced artificial collapses in daytime demand, confusing tree splits.
  * We computed the **median demand for each `zone × day_of_week × hour_of_day`** (with fallback to `zone × hour`).
  * *Example:* Piassa on Monday at 19:00 was previously clipped to `0`; it now receives its real typical demand of **72 trips**.
* **The Result:** Validation RMSE dropped from **8.63 to 8.00** (-7.3% error reduction), and $R^2$ increased from **90.12% to 91.43%**.

---

### Decision 2: Category-Specific Event Duration Imputation (vs. Flat +2 Hours)
* **The Raw Problem:** 4 events in `events_calendar.csv` had missing `end_datetime`.
* **Why Global Average Duration Failed:**
  * The raw events calendar mixes short 90-minute football matches with 2-month school breaks and multi-day exhibitions.
  * A naive average duration across the file yielded **1,227 hours (~51 days)**. Assigning 51 days to a football match would distort demand modeling for months.
* **Why We Chose Category Median:**
  * Categorized durations by event type:
    * **Football Match:** Median = **2.0 hours** (90 min game + halftime/extra time).
    * **Concert:** Median = **4.0 hours** (evening music performance).
    * **Road Closure:** Median = **10.0 hours** (daily construction shift).
* **The Result:** Avoided assigning 50-day surge windows to stadium matches, keeping localized surge flags tightly bounded.

---

### Decision 3: Event Ingress/Egress Buffer (±1 Hour)
* **The Raw Problem:** Ride demand does not only exist during an event; attendees must travel to and from the venue.
* **Why We Chose ±1 Hour Buffer:**
  * Events were joined using the condition:
    $$\text{start} - 1\text{h} \le \text{pickup\_hour} \le \text{end} + 1\text{h}$$
  * *Ingress Buffer (start - 1h):* Captures fans traveling to the stadium before kickoff.
  * *Egress Buffer (end + 1h):* Captures the crowd dispersal surge when thousands of attendees order rides simultaneously.
* **The Result:** Matched **20,154 zone-hours (24.1% of training data)** inside active event windows. Statistical analysis verified a **+91% demand surge** during stadium matches.

---

### Decision 4: Weather Timezone Shift (+3 Hours UTC $\rightarrow$ EAT)
* **The Raw Problem:** Weather timestamps ended in `Z` (UTC / Greenwich Mean Time), while ride logs were in local Addis Ababa time (East Africa Time, UTC+3).
* **Why We Chose +3 Hour Conversion:**
  * Without shifting, a 17:00 thunderstorm would join to 14:00 demand, inverting weather causality.
* **The Empirical Proof:**
  * After shifting +3 hours, the diurnal temperature curve peaks at **15:00 (3:00 PM local time)** at **24.4°C**.
  * Before conversion, temperature peaked at 12:00 UTC, which contradicts real-world afternoon solar heating in Addis Ababa.
* **The Result:** Guaranteed 100% temporal alignment between weather events and passenger demand spikes.

---

### Decision 5: Converting Temperatures Above 50°C from Fahrenheit to Celsius
* **The Raw Problem:** 353 rows between July 10 and July 24 contained temperatures from **55.4°C to 76.6°C**. Addis Ababa has a subtropical highland climate that never exceeds 30°C.
* **The Discovery:** The sensor logged in **Fahrenheit (°F)**:
  $$(57.4^\circ\text{F} - 32) \times \frac{5}{9} = 14.1^\circ\text{C}, \quad (76.6^\circ\text{F} - 32) \times \frac{5}{9} = 24.8^\circ\text{C}$$
* **Why We Chose Unit Conversion (vs. Capping or Mean Imputation):**
  * Imputing with a flat monthly mean removes the diurnal day/night temperature variation for those 14 days.
  * Converting `(F - 32) * 5 / 9` restored the real, physical hourly temperature fluctuations recorded by the station.
* **The Result:** Eliminated extreme temperature anomalies without destroying hourly time-series variance.

---

### Decision 6: Forward Pinning (`ffill`) for Missing Humidity
* **The Raw Problem:** 153 missing values existed in `humidity_pct`.
* **The Finding:** 147 of the 153 missing rows were **isolated 1-hour gaps**, and 3 were **2-hour gaps**. Zero gaps were longer than 2 hours.
* **Why We Chose Forward Pinning (vs. Monthly Mean):**
  * Atmospheric humidity is a continuous, autocorrelated physical variable ($r > 0.95$).
  * If humidity is 42% at 2:00 PM and 45% at 4:00 PM, filling 3:00 PM with the monthly rainy-season mean (72%) injects a false 30% humidity spike into a dry sunny afternoon.
  * Forward pinning (`ffill().bfill()`) estimates ~42%, preserving atmospheric continuity.
* **The Result:** Reduced RMSE to **7.99 trips/h** and MAE to **5.22 trips/h** (our top-performing pipeline).

---

### Decision 7: Strict Data Leakage Exclusion Audit
* **The Raw Problem:** Training data contained `active_drivers` ($r = 0.904$ correlation with trips), `avg_wait_min`, and `avg_fare_birr`.
* **Why We Excluded Them:**
  * Active drivers and wait times are **outcomes of realized demand**, not inputs available 14 days in advance.
  * In the test file (`ride_demand_test.csv`), these columns do not exist.
* **The Result:** Zero test-time leakage. The model generalizes to future forecasting using only known calendar, weather forecast, and event schedules.

---

### Decision 8: Model Architecture Selection (LightGBM)
* **Comparison:**
  * *Ridge Regression:* Failed to capture non-linear rain/event spikes (RMSE 14.79).
  * *Random Forest:* Good accuracy (RMSE 9.91), but slow (11.5 seconds) and rigid splits.
  * *LightGBM:* **Fastest training (2.5s)**, handles complex feature interactions, and achieved the lowest error across all 4 rolling-origin backtest folds.

---

## 3. Detailed Accuracy Metrics & Performance Breakdowns

### 3.1: Zone-by-Zone Accuracy on Validation Holdout

| Zone | Mean Demand (trips/h) | MAE (trips/h) | Error Margin (%) | Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Merkato** | 49.2 | 6.7 | **13.6%** | High-volume market; lowest percentage error |
| **Bole** | 45.5 | 6.3 | **13.8%** | Airport/commercial hub; strong predictable pattern |
| **Megenagna** | 44.3 | 6.6 | **14.9%** | Major transit hub; steady commuter demand |
| **Lideta** | 33.6 | 5.0 | **14.9%** | Central residential/commercial |
| **Kazanchis** | 39.3 | 6.0 | **15.3%** | Business center; high weekday commute peak |
| **Gerji** | 28.7 | 4.6 | **16.0%** | Residential community; stable diurnal profile |
| **CMC** | 29.9 | 4.8 | **16.1%** | Residential corridor; clear morning outbound surge |
| **Sarbet** | 25.4 | 4.1 | **16.1%** | Residential/diplomatic zone |
| **Piassa** | 34.3 | 5.7 | **16.6%** | Historic shopping district |
| **Kolfe** | 26.9 | 4.6 | **17.1%** | Mixed residential/market |
| **Arat Kilo** | 24.1 | 4.4 | **18.3%** | University/government offices |
| **Ayat** | 21.3 | 3.9 | **18.3%** | Launched mid-year; shorter history to learn from |

---

### 3.2: Hour-of-Day Error Breakdown (Easiest vs. Hardest Hours)

| Hour of Day | Average Error (MAE) | Operational Context |
| :---: | :---: | :--- |
| **03:00** | **2.0 trips/h** | Dead of night; demand is near zero (easiest to predict) |
| **00:00** | **2.4 trips/h** | Late night off-peak |
| **01:00** | **2.4 trips/h** | Late night off-peak |
| **02:00** | **2.6 trips/h** | Late night off-peak |
| **12:00** | **6.8 trips/h** | Midday lunch movement |
| **08:00** | **6.8 trips/h** | Morning school/work commute peak |
| **17:00** | **7.4 trips/h** | Evening rush hour onset |
| **07:00** | **7.6 trips/h** | Morning rush hour peak |
| **18:00** | **8.6 trips/h** | **Hardest hour:** Peak evening commute combined with unpredictable dinner, event, and transit delays |

---

### 3.3: Rolling-Origin Time-Series Cross-Validation (D3)

To ensure the model does not suffer from temporal overfitting, we evaluated rolling-origin backtests across 4 historical monthly folds:

* **Fold 1 (July 2025):** $\text{RMSE} = 15.47$ (Heaviest month of the Kiremt rainy season)
* **Fold 2 (August 2025):** $\text{RMSE} = 9.92$
* **Fold 3 (September 2025):** $\text{RMSE} = 11.67$ (Meskel holiday disruptions)
* **Fold 4 (October 1–17, 2025):** $\text{RMSE} = 10.79$
* **Rolling-Origin Mean:** **$11.96 \pm 2.12\text{ trips/h}$**

---

### 3.4: Practical Fleet Translation (In Driver Terms)

* **Rule of Thumb:** In urban dispatch operations, 1 active driver fulfills approximately **1.3 trips per hour**.
* **Model Error Translation:**
  $$\text{Driver Margin} = \frac{\text{MAE}}{1.3} = \frac{5.22}{1.3} \approx \mathbf{4.0\text{ drivers per zone-hour}}$$
* **Operational Impact:** For a busy zone averaging 45 rides/hour and deploying ~35 drivers, our prediction is off by only **4 drivers**, providing high operational fidelity for daily driver shift scheduling and revenue optimization.
