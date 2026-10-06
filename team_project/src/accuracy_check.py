"""Quick accuracy check — re-runs validation on the saved model"""
import pandas as pd
import numpy as np
import joblib, os

df    = pd.read_csv("data/processed/master_train.csv", parse_dates=["pickup_hour"])
model = joblib.load("models/final_model.joblib")
feats = joblib.load("models/feature_list.joblib")

# Chronological split (same as training)
train = df[df["pickup_hour"] <= "2025-10-17 23:00"]
val   = df[df["pickup_hour"] >= "2025-10-18 00:00"]

X_val, y_val = val[feats], val["trips"]
preds = np.clip(model.predict(X_val), 0, None)

rmse = np.sqrt(np.mean((y_val - preds)**2))
mae  = np.mean(np.abs(y_val - preds))
mean_demand = y_val.mean()
pct_err = mae / mean_demand * 100

# Seasonal naive (the simple baseline we must beat)
sn = (train.groupby(["zone_enc","day_of_week","hour"])["trips"]
      .mean().reset_index().rename(columns={"trips":"sn_pred"}))
val_sn = val.merge(sn, on=["zone_enc","day_of_week","hour"], how="left")
val_sn["sn_pred"] = val_sn["sn_pred"].fillna(train["trips"].mean())
sn_rmse = np.sqrt(np.mean((y_val - val_sn["sn_pred"])**2))
sn_mae  = np.mean(np.abs(y_val - val_sn["sn_pred"]))

improvement = (sn_rmse - rmse) / sn_rmse * 100

# Per-zone accuracy
val2 = val.copy()
val2["pred"] = preds
val2["abs_error"] = np.abs(val2["trips"] - val2["pred"])
zone_acc = val2.groupby("zone").agg(
    mean_trips=("trips","mean"),
    mae=("abs_error","mean"),
).round(1)
zone_acc["pct_error"] = (zone_acc["mae"] / zone_acc["mean_trips"] * 100).round(1)
zone_acc = zone_acc.sort_values("mae", ascending=False)

# Hour-of-day accuracy
hour_acc = val2.groupby("hour")["abs_error"].mean().round(1)

print("=" * 55)
print("ACCURACY REPORT")
print("=" * 55)
print(f"\nValidation period: Oct 18 – Oct 31, 2025")
print(f"Validation rows:   {len(val):,} zone-hours")
print(f"Mean demand:       {mean_demand:.1f} trips per zone-hour")
print()
print("OUR MODEL (LightGBM):")
print(f"  RMSE = {rmse:.2f} trips/hour")
print(f"  MAE  = {mae:.2f} trips/hour  ({pct_err:.1f}% of avg demand)")
print()
print("SIMPLE BASELINE (seasonal naive):")
print(f"  RMSE = {sn_rmse:.2f} trips/hour")
print(f"  MAE  = {sn_mae:.2f} trips/hour")
print()
print(f"IMPROVEMENT OVER BASELINE: {improvement:.1f}%")
print()
print("ACCURACY PER ZONE:")
print(zone_acc.to_string())
print()
print("HARDEST HOURS (highest avg error):")
print(hour_acc.sort_values(ascending=False).head(6).to_string())
print()
print("EASIEST HOURS:")
print(hour_acc.sort_values().head(6).to_string())
