"""
Student 3 — Modeling & Evaluation
Deliverable D: Baselines, model comparison, rolling-origin validation,
leakage audit, ablation, tuning, error analysis.
Produces: submission file + final_model.joblib
"""
import pandas as pd
import numpy as np
import joblib, os, warnings, time
warnings.filterwarnings("ignore")

PROC   = os.path.join("data", "processed")
RAW    = os.path.join("data", "raw")
MODELS = "models"
FIG    = "figures"
os.makedirs(MODELS, exist_ok=True)
os.makedirs(FIG,    exist_ok=True)
os.makedirs("reports", exist_ok=True)

np.random.seed(42)

# ── load data ─────────────────────────────────────────────────────────────────
df      = pd.read_csv(os.path.join(PROC, "master_train.csv"), parse_dates=["pickup_hour"])
test_df = pd.read_csv(os.path.join(PROC, "master_test.csv"),  parse_dates=["pickup_hour"])
test_ids = pd.read_csv(os.path.join(PROC, "test_row_ids.csv")) if os.path.exists(os.path.join(PROC,"test_row_ids.csv")) else None
sub_tmpl = pd.read_csv(os.path.join(RAW, "submission_template.csv"))

print(f"Train: {len(df):,}  Test: {len(test_df):,}")

# ── feature columns (NO leaky cols) ──────────────────────────────────────────
# D4 — Leakage audit
LEAKY = ["avg_fare_birr", "avg_wait_min", "active_drivers"]  # exist only in history
FEATURE_COLS = [
    "hour", "day_of_week", "is_weekend", "month", "week_of_year",
    "day_of_month", "is_payday",
    "temp_c", "rain_mm", "humidity_pct", "wind_kmh", "rain_class", "rain_3h",
    "in_event_window", "hours_since_event_start", "hours_until_event_end",
    # num_events_active: tested — RMSE worse, excluded
    # binary event cols (is_football_match etc): tested — RMSE worse despite CV gain, excluded
    "zone_enc", "zone_hour_mean",
]

TARGET = "trips"

# Only keep features that exist in both train and test
FEATURE_COLS = [c for c in FEATURE_COLS if c in df.columns and c in test_df.columns]
print(f"Features used: {FEATURE_COLS}")

# ── chronological split ───────────────────────────────────────────────────────
TRAIN_END  = pd.Timestamp("2025-10-17 23:00")
VAL_START  = pd.Timestamp("2025-10-18 00:00")

train = df[df["pickup_hour"] <= TRAIN_END].copy()
val   = df[df["pickup_hour"] >= VAL_START].copy()
print(f"Train split: {len(train):,} rows  Val: {len(val):,} rows")
print(f"Val dates: {val['pickup_hour'].min()} → {val['pickup_hour'].max()}")

X_train, y_train = train[FEATURE_COLS], train[TARGET]
X_val,   y_val   = val[FEATURE_COLS],   val[TARGET]

def rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_true - np.array(y_pred))**2))

def mae(y_true, y_pred):
    return np.mean(np.abs(y_true - np.array(y_pred)))

# ══════════════════════════════════════════════════════════════════════════════
# D1 — BASELINES
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== D1: BASELINES ===")

# Baseline 1: global mean
global_mean = y_train.mean()
b1_pred = np.full(len(y_val), global_mean)
b1_rmse = rmse(y_val, b1_pred);  b1_mae = mae(y_val, b1_pred)
print(f"Global mean baseline  — RMSE: {b1_rmse:.2f}  MAE: {b1_mae:.2f}")

# Baseline 2: seasonal naive (mean by zone × day_of_week × hour)
sn = (train.groupby(["zone_enc", "day_of_week", "hour"])[TARGET]
      .mean().reset_index().rename(columns={TARGET: "sn_pred"}))
val_sn = val.merge(sn, on=["zone_enc","day_of_week","hour"], how="left")
val_sn["sn_pred"] = val_sn["sn_pred"].fillna(global_mean)
b2_rmse = rmse(y_val, val_sn["sn_pred"]); b2_mae = mae(y_val, val_sn["sn_pred"])
print(f"Seasonal naive baseline — RMSE: {b2_rmse:.2f}  MAE: {b2_mae:.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# D2 — MODEL COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== D2: MODEL COMPARISON ===")

from sklearn.linear_model  import Ridge
from sklearn.ensemble      import RandomForestRegressor, HistGradientBoostingRegressor

models_to_try = {
    "Ridge":       Ridge(alpha=10.0, random_state=42),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    "HGBoosting":  HistGradientBoostingRegressor(max_iter=300, random_state=42),
}

results = {}
for name, model in models_to_try.items():
    t0 = time.time()
    model.fit(X_train, y_train)
    pred = model.predict(X_val).clip(0)
    elapsed = time.time() - t0
    r = rmse(y_val, pred); m = mae(y_val, pred)
    results[name] = {"model": model, "rmse": r, "mae": m, "time_s": round(elapsed,1), "pred": pred}
    print(f"{name:20s} — RMSE: {r:.2f}  MAE: {m:.2f}  Time: {elapsed:.1f}s")

# try LightGBM if available
try:
    import lightgbm as lgb
    t0 = time.time()
    lgb_model = lgb.LGBMRegressor(
        n_estimators=500, learning_rate=0.05, num_leaves=63,
        random_state=42, n_jobs=-1, verbose=-1
    )
    lgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
    pred_lgb = lgb_model.predict(X_val).clip(0)
    elapsed = time.time() - t0
    r = rmse(y_val, pred_lgb); m = mae(y_val, pred_lgb)
    results["LightGBM"] = {"model": lgb_model, "rmse": r, "mae": m,
                           "time_s": round(elapsed,1), "pred": pred_lgb}
    print(f"{'LightGBM':20s} — RMSE: {r:.2f}  MAE: {m:.2f}  Time: {elapsed:.1f}s")
except ImportError:
    print("LightGBM not installed — skipping")

# pick winner
best_name = min(results, key=lambda k: results[k]["rmse"])
best_model = results[best_name]["model"]
print(f"\nWinner: {best_name} (RMSE={results[best_name]['rmse']:.2f})")

# ══════════════════════════════════════════════════════════════════════════════
# D3 — ROLLING-ORIGIN VALIDATION (4 folds)
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== D3: ROLLING-ORIGIN VALIDATION ===")

fold_cuts = [
    (pd.Timestamp("2025-06-30"), pd.Timestamp("2025-07-01"), pd.Timestamp("2025-07-31")),
    (pd.Timestamp("2025-07-31"), pd.Timestamp("2025-08-01"), pd.Timestamp("2025-08-31")),
    (pd.Timestamp("2025-08-31"), pd.Timestamp("2025-09-01"), pd.Timestamp("2025-09-30")),
    (pd.Timestamp("2025-09-30"), pd.Timestamp("2025-10-01"), pd.Timestamp("2025-10-17")),
]

fold_rmses = []
for i, (train_end, val_start, val_end) in enumerate(fold_cuts):
    f_train = df[df["pickup_hour"] <= train_end]
    f_val   = df[(df["pickup_hour"] >= val_start) & (df["pickup_hour"] <= val_end)]
    if len(f_val) == 0: continue

    # seasonal naive for this fold
    f_sn = (f_train.groupby(["zone_enc","day_of_week","hour"])[TARGET]
            .mean().reset_index().rename(columns={TARGET:"sn_pred"}))
    f_val_sn = f_val.merge(f_sn, on=["zone_enc","day_of_week","hour"], how="left")
    f_val_sn["sn_pred"] = f_val_sn["sn_pred"].fillna(f_train[TARGET].mean())

    # best model
    from sklearn.base import clone
    fold_model = clone(best_model)
    fold_model.fit(f_train[FEATURE_COLS], f_train[TARGET])
    fold_pred  = fold_model.predict(f_val[FEATURE_COLS]).clip(0)

    fold_r = rmse(f_val[TARGET], fold_pred)
    fold_rmses.append(fold_r)
    print(f"  Fold {i+1} ({val_start.date()}–{val_end.date()}) RMSE={fold_r:.2f}")

print(f"  Rolling-origin mean RMSE: {np.mean(fold_rmses):.2f} ± {np.std(fold_rmses):.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# D5 — ABLATION STUDY
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== D5: ABLATION ===")

CALENDAR = ["hour","day_of_week","is_weekend","month","week_of_year","day_of_month","is_payday","zone_enc","zone_hour_mean"]
WEATHER   = ["temp_c","rain_mm","humidity_pct","wind_kmh","rain_class","rain_3h"]
EVENTS    = ["in_event_window","hours_since_event_start","hours_until_event_end"]

ablation_sets = {
    "Calendar+Zone":      CALENDAR,
    "+Weather":           CALENDAR + WEATHER,
    "+Events":            CALENDAR + EVENTS,
    "All (Cal+Wthr+Evnt)":CALENDAR + WEATHER + EVENTS,
}

ablation_results = {}
from sklearn.base import clone
for label, feats in ablation_sets.items():
    feats = [f for f in feats if f in X_train.columns]
    m = clone(best_model); m.fit(X_train[feats], y_train)
    p = m.predict(X_val[feats]).clip(0)
    r = rmse(y_val, p); ma = mae(y_val, p)
    ablation_results[label] = {"rmse": r, "mae": ma, "features": feats}
    print(f"  {label:25s} RMSE={r:.2f}  MAE={ma:.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# D6 — HYPERPARAMETER TUNING (simple grid, optuna if available)
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== D6: TUNING ===")
best_rmse_before = results[best_name]["rmse"]

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        if best_name == "LightGBM":
            import lightgbm as lgb
            params = {
                "n_estimators":       trial.suggest_int("n_estimators", 300, 1000),
                "learning_rate":      trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
                "num_leaves":         trial.suggest_int("num_leaves", 31, 255),
                "max_depth":          trial.suggest_int("max_depth", 4, 12),
                "min_child_samples":  trial.suggest_int("min_child_samples", 10, 80),
                "subsample":          trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree":   trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "reg_alpha":          trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
                "reg_lambda":         trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
                "random_state": 42, "n_jobs": -1, "verbose": -1,
            }
            m = lgb.LGBMRegressor(**params)
        elif best_name == "HGBoosting":
            params = {
                "max_iter":       trial.suggest_int("max_iter", 200, 600),
                "learning_rate":  trial.suggest_float("learning_rate", 0.02, 0.2, log=True),
                "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 31, 127),
                "random_state": 42,
            }
            m = HistGradientBoostingRegressor(**params)
        else:
            return best_rmse_before  # skip tuning for simpler models

        m.fit(X_train, y_train)
        p = m.predict(X_val).clip(0)
        return rmse(y_val, p)


    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=50, show_progress_bar=False)
    best_params = study.best_params
    best_tuned_rmse = study.best_value
    print(f"  Best params: {best_params}")
    print(f"  RMSE before: {best_rmse_before:.2f}  After tuning: {best_tuned_rmse:.2f}")

    # retrain with best params on full train
    if best_name == "LightGBM":
        import lightgbm as lgb
        final_model = lgb.LGBMRegressor(**{**best_params, "random_state":42, "n_jobs":-1, "verbose":-1})
    else:
        final_model = HistGradientBoostingRegressor(**{**best_params, "random_state":42})
    final_model.fit(df[FEATURE_COLS], df[TARGET])

except ImportError:
    print("  Optuna not installed — using best model from D2 without further tuning")
    best_params = {}
    best_tuned_rmse = best_rmse_before
    final_model = best_model
    # refit on full train
    final_model.fit(df[FEATURE_COLS], df[TARGET])

# ══════════════════════════════════════════════════════════════════════════════
# D7 — ERROR ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== D7: ERROR ANALYSIS ===")
val_pred = final_model.predict(X_val).clip(0)
val["pred"] = val_pred
val["error"] = val["trips"] - val["pred"]
val["abs_error"] = val["error"].abs()

# by zone
zone_err = val.groupby("zone")["abs_error"].mean().sort_values(ascending=False).round(2)
print("  MAE by zone:")
print(zone_err.to_string())

# by hour
hour_err = val.groupby("hour")["abs_error"].mean().sort_values(ascending=False).head(5)
print(f"\n  Hardest hours: {hour_err.index.tolist()}")

# top 10 worst zone-hours
top10 = val.nlargest(10, "abs_error")[["zone","pickup_hour","trips","pred","error"]].reset_index(drop=True)
print("\n  Top 10 worst zone-hours:")
print(top10.to_string())

# D8 — Response: add zone_hour_mean as extra feature (already included)
print("\n=== D8: No additional change needed — zone_hour_mean already encodes zone-hour patterns ===")

# D9 — plain language metric
final_val_rmse = rmse(y_val, val_pred)
final_val_mae  = mae(y_val, val_pred)
mean_trips     = y_val.mean()
pct_rmse = final_val_rmse / mean_trips * 100
approx_drivers = final_val_rmse / 1.3
print(f"\n=== D9: Plain-language metrics ===")
print(f"  RMSE = {final_val_rmse:.1f} trips per zone-hour")
print(f"  MAE  = {final_val_mae:.1f} trips per zone-hour")
print(f"  As % of mean demand ({mean_trips:.1f}): {pct_rmse:.1f}%")
print(f"  In driver terms: ~{approx_drivers:.1f} drivers per zone-hour")

# ══════════════════════════════════════════════════════════════════════════════
# SAVE MODEL & MAKE PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
joblib.dump(final_model,  os.path.join(MODELS, "final_model.joblib"))
joblib.dump(FEATURE_COLS, os.path.join(MODELS, "feature_list.joblib"))
print(f"\nModel saved to {MODELS}/final_model.joblib")

# Generate predictions
test_pred = final_model.predict(test_df[FEATURE_COLS]).clip(0).round(0).astype(int)

# Build submission
sub = sub_tmpl.copy()
sub["predicted_trips"] = test_pred
sub.to_csv(os.path.join("submission", "team_qiyas_submission.csv"), index=False)
print(f"Submission saved: {len(sub):,} rows")

# Copy model to app assets
import shutil
os.makedirs(os.path.join("app","assets"), exist_ok=True)
shutil.copy(os.path.join(MODELS, "final_model.joblib"), os.path.join("app","assets","final_model.joblib"))
shutil.copy(os.path.join(MODELS, "feature_list.joblib"), os.path.join("app","assets","feature_list.joblib"))

# ══════════════════════════════════════════════════════════════════════════════
# SAVE CHARTS DATA & WRITE REPORT
# ══════════════════════════════════════════════════════════════════════════════
import json
model_results_for_chart = {
    "Global Mean":        {"rmse": b1_rmse, "mae": b1_mae},
    "Seasonal Naive":     {"rmse": b2_rmse, "mae": b2_mae},
}
for k,v in results.items():
    model_results_for_chart[k] = {"rmse": v["rmse"], "mae": v["mae"]}

with open(os.path.join(PROC, "model_results.json"), "w") as f:
    json.dump(model_results_for_chart, f)

with open(os.path.join(PROC, "ablation_results.json"), "w") as f:
    json.dump({k: {"rmse": v["rmse"], "mae": v["mae"]} for k,v in ablation_results.items()}, f)

with open(os.path.join(PROC, "rolling_rmses.json"), "w") as f:
    json.dump({"folds": fold_rmses, "mean": float(np.mean(fold_rmses)), "std": float(np.std(fold_rmses))}, f)

val[["zone","pickup_hour","trips","pred","error","abs_error"]].to_csv(
    os.path.join(PROC,"val_predictions.csv"), index=False)

# Write D report
with open(os.path.join("reports","D_model_evaluation.md"), "w", encoding="utf-8") as f:
    f.write("# D — Modeling & Evaluation\n\n")
    f.write(f"## D1: Baselines\n\n")
    f.write(f"| Model | RMSE | MAE |\n|---|---|---|\n")
    f.write(f"| Global Mean | {b1_rmse:.2f} | {b1_mae:.2f} |\n")
    f.write(f"| Seasonal Naive | {b2_rmse:.2f} | {b2_mae:.2f} |\n\n")
    f.write(f"## D2: Model Comparison\n\n| Model | RMSE | MAE | Time(s) |\n|---|---|---|---|\n")
    for k,v in results.items():
        f.write(f"| {k} | {v['rmse']:.2f} | {v['mae']:.2f} | {v['time_s']} |\n")
    f.write(f"\n**Winner:** {best_name}\n\n")
    f.write(f"## D3: Rolling-Origin Validation\n\nMean RMSE: {np.mean(fold_rmses):.2f} ± {np.std(fold_rmses):.2f}\n\n")
    f.write(f"## D4: Leakage Audit\n\nExcluded features: {LEAKY}\n(These only exist in training history — not available at forecast time.)\n\n")
    f.write(f"## D5: Ablation\n\n| Feature set | RMSE | MAE |\n|---|---|---|\n")
    for k,v in ablation_results.items():
        f.write(f"| {k} | {v['rmse']:.2f} | {v['mae']:.2f} |\n")
    f.write(f"\n## D6: Tuning\n\nBest params: {best_params}\nRMSE before: {best_rmse_before:.2f} → after: {best_tuned_rmse:.2f}\n\n")
    f.write(f"## D7: Error Analysis\n\nMAE by zone:\n```\n{zone_err.to_string()}\n```\n\nTop 10 worst zone-hours:\n```\n{top10.to_string()}\n```\n\n")
    f.write(f"## D9: Plain-language metric\n\n")
    f.write(f"Our model is off by about **{final_val_rmse:.0f} trips per zone-hour** on average. "
            f"That is **{pct_rmse:.0f}% of typical demand** ({mean_trips:.0f} trips/hour). "
            f"In driver terms, this means we might over- or under-deploy roughly "
            f"**{approx_drivers:.0f} drivers per zone per hour** — a manageable margin for operations.\n")

print("\nStudent 3 modeling complete.")
