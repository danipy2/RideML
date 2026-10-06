import pandas as pd
import numpy as np
import json
from sklearn.metrics import r2_score

val = pd.read_csv('data/processed/val_predictions.csv')
y_true = val['trips']
y_pred = val['pred']

tuned_rmse = float(np.sqrt(np.mean((y_true - y_pred)**2)))
tuned_mae  = float(np.mean(np.abs(y_true - y_pred)))
tuned_r2   = float(r2_score(y_true, y_pred))

print("=== FINAL HACKATHON MODEL METRICS ===\n")
print("Validation Set: Oct 18 - Oct 31, 2025 (3,958 zone-hours)\n")
print(f"  RMSE (tuned LightGBM) : {tuned_rmse:.4f}")
print(f"  MAE  (tuned LightGBM) : {tuned_mae:.4f}")
print(f"  R2   (tuned LightGBM) : {tuned_r2:.4f}  ({tuned_r2*100:.2f}%)")
print()

with open('data/processed/model_results.json') as f:
    mr = json.load(f)

var_y = float(np.var(y_true))
print("=== FULL COMPARISON TABLE ===\n")
headers = ["Model", "RMSE", "MAE", "R2"]
print(f"{'Model':<28} {'RMSE':>6} {'MAE':>6} {'R2':>8}")
print("-"*54)
for name, m in mr.items():
    rmse = m['rmse']
    mae  = m['mae']
    r2   = 1.0 - (rmse**2 / var_y)
    print(f"{name:<28} {rmse:>6.2f} {mae:>6.2f} {r2*100:>7.2f}%")

label = "LightGBM (Optuna Tuned)"
print(f"{label:<28} {tuned_rmse:>6.2f} {tuned_mae:>6.2f} {tuned_r2*100:>7.2f}%")

print("\n=== IMPROVEMENT OVER BASELINES ===")
naive_rmse = 11.995853234235147
print(f"  vs Seasonal Naive : {naive_rmse:.2f} -> {tuned_rmse:.2f} RMSE  ({(naive_rmse-tuned_rmse)/naive_rmse*100:.1f}% improvement)")
global_rmse = 27.79525424483132
print(f"  vs Global Mean    : {global_rmse:.2f} -> {tuned_rmse:.2f} RMSE  ({(global_rmse-tuned_rmse)/global_rmse*100:.1f}% improvement)")
