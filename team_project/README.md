# 🚖 Addis Ride Demand Forecasting — Team Qiyas

> **Qiyas AI Hackathon #2 · Addis Ababa University · IADE AI Training Program**

A full end-to-end machine learning pipeline that forecasts ride-hailing demand for **12 zones across Addis Ababa**, hour-by-hour, for a 14-day future window (November 1–14, 2025). Built under hackathon time pressure from raw messy data to a deployed interactive demo.

---

## 🏆 Results at a Glance

| Metric | Value |
|---|---|
| **R² (validation)** | **91.65%** |
| **Validation RMSE** | **7.89 trips / zone-hour** |
| **Validation MAE** | **5.17 trips / zone-hour** |
| **vs. Seasonal Naive baseline** | **34% lower RMSE** (12.00 → 7.89) |
| **vs. Global Mean baseline** | **71.6% lower RMSE** (27.80 → 7.89) |
| **Total forecasts produced** | **4,032** (12 zones × 336 hours) |
| **Training data** | **83,777 zone-hours** (Jan–Oct 2025) |

---

## 📐 Problem Statement

Predict the number of ride-hailing trips in each of 12 Addis Ababa zones for every hour of November 1–14, 2025, using only information that would genuinely be available before that date — no leakage from future outcomes.

**Three data sources fused together:**
- 🗃️ `ride_demand_train.csv` — 10 months of zone-hour trip history
- 🌦️ `weather_hourly.csv` — hourly weather observations + forecasts
- 📅 `events_calendar.csv` — city events (football matches, concerts, public holidays, road closures…)

---

## ⚙️ Pipeline Overview

```
Raw Data (3 sources)
      │
      ▼
[A] Data Cleaning & Integration   ← 15+ data quality issues fixed
      │  Zone spellings unified, timestamps aligned (UTC→EAT),
      │  Fahrenheit→Celsius, negative sentinels imputed,
      │  event durations inferred, 17 features engineered
      ▼
[B] Exploratory Analysis          ← Demand patterns, weather effects,
      │  event impact quantified     event impact measured
      ▼
[C] Visualizations                ← 12 publication-ready figures
      ▼
[D] Modeling & Evaluation         ← 5 models compared, Optuna HPO,
      │  LightGBM selected          rolling-origin CV, leakage audit
      ▼
[E] Streamlit Demo App            ← Interactive 24-hour forecast tool
      ▼
[F] Slide Deck  +  [G] Submission CSV
```

---

## 🔬 Key Technical Decisions

| Decision | What We Did | Why It Mattered |
|---|---|---|
| **Weather timezone fix** | Converted UTC→EAT (+3h) before joining | Wrong clock = 3-hour shift in join = wrong model. Temperature now peaks at 15:00 local — correct. |
| **Negative trip imputation** | Historical median (zone × day_of_week × hour), not zero-clip | `-1` was a system error sentinel, not zero demand. Zero-clipping created artificial daytime demand collapses. RMSE improvement: 8.63 → 8.00. |
| **Fahrenheit detection** | 350 rows with `temp > 50°C` converted via (F−32)×5/9 | Addis Ababa never exceeds 30°C. Preserved real diurnal variation rather than imputing a flat mean. |
| **Event buffer ±1h** | Flagged ±1 hour around event windows | Captures ingress (fans travelling to a match) and egress (crowd dispersal spike after it ends). 24% of zone-hours flagged. |
| **Leakage exclusion** | Excluded `avg_fare_birr`, `avg_wait_min`, `active_drivers` | These are consequences of demand, not causes. Not available at forecast time. |
| **Chronological validation** | Train Jan 1–Oct 17, Validate Oct 18–31 | Random splits are forbidden for time-series — they leak future patterns into training. |
| **Full-data final model** | Retrained on all labelled data (train + val) | More data = better Nov forecasts. Val split used only for model selection & tuning. |
| **Optuna HPO** | 50 Optuna trials on chronological hold-out | Tuned LightGBM (RMSE 9.35 → 7.89), a 16% improvement over default hyperparameters. |

---

## 📊 Model Comparison

All models trained on the same chronological split (≤ Oct 17) with identical features:

| Model | RMSE | MAE | Train Time |
|---|---|---|---|
| Global Mean (baseline) | 27.80 | 20.76 | — |
| Seasonal Naive (baseline) | 12.00 | 7.37 | — |
| Ridge Regression | 14.80 | 10.36 | 0.2s |
| Random Forest | 9.98 | 6.27 | 11.0s |
| Histogram Gradient Boosting | 9.51 | 6.08 | 3.7s |
| LightGBM (default) | 9.35 | 5.95 | 3.6s |
| **LightGBM (Optuna tuned)** | **7.89** | **5.17** | **3.6s** |

**Winner: LightGBM** — best accuracy, fastest training, robust to non-linear feature interactions (rain effect varies by zone type and hour of day).

---

## 🧠 Feature Engineering (17 Features, Zero Leakage)

| Feature | Source | Description |
|---|---|---|
| `hour`, `day_of_week`, `is_weekend` | Timestamp | Time-of-day and weekly cycle |
| `month`, `week_of_year`, `day_of_month` | Timestamp | Seasonal and monthly patterns |
| `is_payday` | Timestamp | Days 1–3 and 28–31 (pay-period uplift: +5.8%) |
| `temp_c`, `rain_mm`, `rain_class`, `rain_3h` | Weather | Rain drives demand up; non-linear binning; 3-hour sustained rain |
| `in_event_window`, `hours_since_event_start`, `hours_until_event_end` | Events calendar | Event surge flag + temporal position within window |
| `zone_enc` | Zone name | Label-encoded zone identity |
| `zone_hour_mean` | Training history | Mean demand per (zone, hour) — **top feature, 38% importance**. No leakage: fitted on training data only. |

---

## 📈 Key Analytical Findings

- **City-wide demand grew 51.9%** from Q1 to Q4 2025 — November forecasts must account for this trend.
- **Football matches create a +91% demand surge** in the event zone (53.6 vs 28.1 avg trips/hr).
- **Concerts are the biggest spike driver** at 71 trips/hour during events.
- **Public holidays reduce demand by 71%** city-wide (2,233 vs 7,801 trips/day).
- **Rain increases demand** — Business zones show the largest uplift (2× demand in moderate rain).
- **Bole is the most weekend-biased zone** (1.32× weekday rate) — entertainment/nightlife hub.
- **Kazanchis collapses on weekends** (0.49× rate) — pure business district.
- **Evening rush (5–7pm) is the hardest hour to predict** due to commute + event dispersal overlap (MAE up to 8.6).

---

## 🗺️ Error Analysis

### By Zone (Validation Oct 18–31)
All 12 zones fall within **13–18% relative error** — consistent across both high-density hubs and outer residential areas.

| Zone | Mean Demand | MAE | % Error |
|---|---|---|---|
| Merkato | 49.2 | 6.57 | 13.4% |
| Bole | 45.5 | 6.32 | 13.9% |
| … | … | … | … |
| Ayat | 21.3 | 3.82 | 17.9% |

### In Driver Terms
MAE of 5.17 trips/hour ÷ 1.3 trips/driver-hour = **~4 drivers margin per zone-hour**. If we forecast 20 drivers needed in Bole at 6pm, the true need is typically 16–24 — an actionable planning range.

---

## 🗂️ Deliverables

| # | Deliverable | Key Files |
|---|---|---|
| **A** | Data Cleaning & Integration | `src/cleaning.py` · `reports/A_cleaning_and_integration.md` · `data/processed/` |
| **B** | Analysis Report | `src/analysis.py` · `reports/B_analysis_report.md` |
| **C** | Visualization Pack | `src/visualizations.py` · `figures/` (12 PNGs) |
| **D** | Modeling & Evaluation | `src/modeling.py` · `reports/D_model_evaluation.md` · `models/` |
| **E** | Demo App | `app/app.py` — `streamlit run app/app.py` |
| **F** | Slide Deck | `presentation/team_qiyas_slides.html` |
| **G** | Project Structure | This README · `requirements.txt` |
| — | Submission | `submission/team_qiyas_submission.csv` (4,032 rows) |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full pipeline (in order)
python src/cleaning.py        # A — produces data/processed/
python src/analysis.py        # B — analysis outputs
python src/visualizations.py  # C — produces figures/
python src/modeling.py        # D — trains model + makes submission

# 3. Launch the interactive demo
streamlit run app/app.py
```

Or run via Jupyter notebooks (one per deliverable):
```bash
jupyter nbconvert --to notebook --execute notebooks/01_cleaning_and_integration.ipynb
jupyter nbconvert --to notebook --execute notebooks/02_analysis_report.ipynb
jupyter nbconvert --to notebook --execute notebooks/03_visualizations.ipynb
jupyter nbconvert --to notebook --execute notebooks/04_modeling_and_evaluation.ipynb
```

---

## 📁 Folder Layout

```
team_project/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/               ← original files (never modified)
│   └── processed/         ← master_train.csv, master_test.csv, val_predictions.csv …
├── notebooks/             ← 01–04 Jupyter notebooks (one per deliverable)
├── src/                   ← Python scripts (same logic as notebooks)
│   ├── cleaning.py        ← data cleaning + feature engineering
│   ├── analysis.py        ← EDA and demand pattern analysis
│   ├── visualizations.py  ← 12 publication-quality figures
│   └── modeling.py        ← model training, HPO, evaluation, submission
├── figures/               ← 12 publication-ready PNG figures
├── reports/               ← A, B, D markdown reports + methodology PDF
├── models/                ← final_model.joblib, feature_list.joblib
├── app/                   ← Streamlit demo (app.py + assets/)
├── presentation/          ← team_qiyas_slides.html
└── submission/            ← team_qiyas_submission.csv
```

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| **Language** | Python 3.11 |
| **Data Processing** | pandas, numpy |
| **Machine Learning** | LightGBM, scikit-learn (Ridge, RandomForest, HistGradientBoosting) |
| **Hyperparameter Optimization** | Optuna (50 trials, TPE sampler) |
| **Visualization** | matplotlib, seaborn |
| **Demo App** | Streamlit |
| **Model Serialization** | joblib |
| **Notebooks** | Jupyter |

---

## 🔁 Reproducibility

- All random seeds set to `42`
- All file paths are relative to `team_project/`
- `data/raw/` files are never modified in-place
- `master_train.csv` and `master_test.csv` are deterministically generated from raw files
- Final model stored at `models/final_model.joblib`

---

## 👥 Team Members

| Student | Role |
|---|---|
| Student 1 | Data Cleaning & Integration (Deliverable A) |
| Student 2 | Data Analysis Report (Deliverable B) |
| Student 3 | Modeling & Evaluation (Deliverable D) |
| Student 4 | Visualization Pack (Deliverable C) |
| Student 5 | Demo App, Slides & Project Structure (Deliverables E, F, G) |

---

*Built at the Qiyas AI Hackathon #2 — Addis Ababa, 2025*
