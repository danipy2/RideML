import os, pandas as pd

checks = [
    ("submission/team_qiyas_submission.csv",       "Submission file"),
    ("data/processed/master_train.csv",            "master_train"),
    ("data/processed/master_test.csv",             "master_test"),
    ("data/processed/data_dictionary_master.csv",  "Data dictionary"),
    ("models/final_model.joblib",                  "Saved model"),
    ("models/feature_list.joblib",                 "Feature list"),
    ("reports/A_cleaning_and_integration.md",      "Report A"),
    ("reports/B_analysis_report.md",               "Report B"),
    ("reports/D_model_evaluation.md",              "Report D"),
    ("app/app.py",                                 "Demo app"),
    ("README.md",                                  "README"),
    ("requirements.txt",                           "requirements.txt"),
    ("figures/figure_captions.md",                 "Figure captions"),
]

fig_names = {
    1:"gaps_and_missingness", 2:"before_after_cleaning", 3:"demand_trend_with_holidays",
    4:"hour_by_weekday_heatmap", 5:"zone_profiles", 6:"weather_timezone_check",
    7:"rain_effect", 8:"event_study", 9:"holiday_effects", 10:"model_comparison",
    11:"forecast_vs_actual", 12:"feature_importance",
}
for i in range(1, 13):
    checks.append((f"figures/fig{i:02d}_{fig_names[i]}.png", f"fig{i:02d}"))

all_pass = True
for path, label in checks:
    exists = os.path.exists(path)
    size   = os.path.getsize(path) if exists else 0
    ok     = exists and size > 0
    if not ok:
        all_pass = False
    print(f"[{'PASS' if ok else 'FAIL'}] {label:40s} {path}")

sub = pd.read_csv("submission/team_qiyas_submission.csv")
row_check  = len(sub) == 4032
neg_check  = (sub["predicted_trips"] >= 0).all()
null_check = sub["predicted_trips"].notna().all()

for cond, msg in [(row_check, f"Submission rows = {len(sub)} (need 4032)"),
                  (neg_check,  "No negative predictions"),
                  (null_check, "No blank predictions")]:
    if not cond:
        all_pass = False
    print(f"[{'PASS' if cond else 'FAIL'}] {msg}")

print()
print("ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED — see FAIL lines above")
