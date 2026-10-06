# Team Qiyas — Addis Ride Demand Forecasting

**Qiyas AI Hackathon #2** · Addis Ababa University · IADE AI Training Program

## Team Members

| Student | Role |
|---|---|
| Student 1 | Data Cleaning & Integration (Deliverable A) |
| Student 2 | Data Analysis Report (Deliverable B) |
| Student 3 | Modeling & Evaluation (Deliverable D) |
| Student 4 | Visualization Pack (Deliverable C) |
| Student 5 | Demo App, Slides & Project Structure (Deliverables E, F, G) |

## What This Project Does

We predict ride-hailing trips for 12 zones in Addis Ababa for every hour of **November 1–14, 2025** (4,032 forecasts). We combine 10 months of trip history with hourly weather and city events. Our final model is LightGBM trained on 83,777 zone-hours.

## Key Results

| Metric | Value |
|---|---|
| R² (full-data model) | **91.65%** |
| Validation RMSE | **7.89 trips/zone-hour** |
| Validation MAE | **5.17 trips/zone-hour** |
| vs. Seasonal Naive baseline | **34% better** (RMSE 12.00 → 7.89) |

## Deliverables

| # | Deliverable | Files |
|---|---|---|
| A | Data Cleaning & Integration | `notebooks/01_cleaning_and_integration.ipynb` · `src/cleaning.py` · `reports/A_cleaning_and_integration.md` · `data/processed/` |
| B | Analysis Report | `notebooks/02_analysis_report.ipynb` · `src/analysis.py` · `reports/B_analysis_report.md` |
| C | Visualization Pack | `notebooks/03_visualizations.ipynb` · `src/visualizations.py` · `figures/` (12 figures) |
| D | Modeling & Evaluation | `notebooks/04_modeling_and_evaluation.ipynb` · `src/modeling.py` · `reports/D_model_evaluation.md` · `models/` |
| E | Demo App | `app/app.py` — run with `streamlit run app/app.py` |
| F | Slides | `presentation/team_qiyas_slides.html` |
| G | Project Structure | This README · `requirements.txt` |
| — | Submission | `submission/team_qiyas_submission.csv` (4,032 rows) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (in order)
python src/cleaning.py        # Deliverable A — produces data/processed/
python src/analysis.py        # Deliverable B
python src/visualizations.py  # Deliverable C — produces figures/
python src/modeling.py        # Deliverable D — trains model, makes submission

# OR run via notebooks
jupyter nbconvert --to notebook --execute notebooks/01_cleaning_and_integration.ipynb
jupyter nbconvert --to notebook --execute notebooks/02_analysis_report.ipynb
jupyter nbconvert --to notebook --execute notebooks/03_visualizations.ipynb
jupyter nbconvert --to notebook --execute notebooks/04_modeling_and_evaluation.ipynb

# Demo app
streamlit run app/app.py
```

## Folder Layout

```
team_project/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/          ← original files (never modified)
│   └── processed/    ← master_train.csv, master_test.csv, val_predictions.csv …
├── notebooks/        ← 01–04 Jupyter notebooks (one per deliverable)
├── src/              ← Python scripts (same logic as notebooks)
├── figures/          ← 12 publication-ready PNG figures
├── reports/          ← A, B, D markdown reports
├── models/           ← final_model.joblib, feature_list.joblib
├── app/              ← Streamlit demo (app.py + assets/)
├── presentation/     ← team_qiyas_slides.html
└── submission/       ← team_qiyas_submission.csv
```

## Key Technical Decisions

| Decision | Reason |
|---|---|
| Weather timezone: UTC → EAT (+3h) | Raw weather timestamps end in "Z". Wrong clock = 3-hour shift in join = wrong model. |
| No leaky features | `avg_fare_birr`, `avg_wait_min`, `active_drivers` excluded — they don't exist at forecast time. |
| Chronological validation only | Train Jan 1–Oct 17, Val Oct 18–31. Random splits forbidden for time series. |
| Full-data final model | Final model trained on all labelled data (train + val) for best Nov 1–14 predictions. |

## Reproducibility

- All random seeds set to `42`
- All file paths are relative to `team_project/`
- `data/raw/` files are never modified
