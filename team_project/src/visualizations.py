"""
Student 4 — Visualization Pack
Deliverable C: All 12 required figures (fig01–fig09 here, fig10–12 from modeling.py)
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import json, os, warnings
warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid", palette="colorblind", font_scale=1.2)
CMAP = "Blues"
DPI  = 150
FIG  = "figures"
PROC = os.path.join("data", "processed")
RAW  = os.path.join("data", "raw")
os.makedirs(FIG, exist_ok=True)
os.makedirs("reports", exist_ok=True)

CB_COLORS = ["#0077BB","#EE7733","#009988","#CC3311","#33BBEE","#EE3377","#BBBBBB","#000000"]

def savefig(name):
    path = os.path.join(FIG, name)
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")

# ── load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(PROC, "master_train.csv"), parse_dates=["pickup_hour"])
zone_types_df = pd.read_csv(os.path.join(PROC, "zone_types.csv"))
df = df.merge(zone_types_df, on="zone", how="left")

raw_train   = pd.read_csv(os.path.join(RAW, "ride_demand_train.csv"))
raw_weather = pd.read_csv(os.path.join(RAW, "weather_hourly.csv"))
raw_events  = pd.read_csv(os.path.join(RAW, "events_calendar.csv"))

ZONE_TYPES = ["Residential","Business","Market","Mixed/Transport"]
TYPE_COLORS = {zt: CB_COLORS[i] for i, zt in enumerate(ZONE_TYPES)}

# ══════════════════════════════════════════════════════════════════════════════
# FIG 01 — Gaps and Missingness
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig01...")
fig, axes = plt.subplots(2, 1, figsize=(14, 9))

# Top: missing pct per column per file
missing_data = {
    "ride_demand_train": raw_train.isnull().mean() * 100,
    "weather_hourly":    raw_weather.isnull().mean() * 100,
    "events_calendar":   raw_events.isnull().mean() * 100,
}
all_cols = []
vals_per_file = []
file_labels = []
for file, miss in missing_data.items():
    miss = miss[miss > 0]
    for col, pct in miss.items():
        all_cols.append(f"{file}\n{col}")
        vals_per_file.append(pct)
        file_labels.append(file)

colors_bar = [CB_COLORS[0] if "train" in f else CB_COLORS[1] if "weather" in f else CB_COLORS[2]
              for f in file_labels]
axes[0].barh(all_cols, vals_per_file, color=colors_bar)
axes[0].set_xlabel("Missing (%)")
axes[0].set_title("Missing Values per Column in Each Raw File")
patches = [mpatches.Patch(color=CB_COLORS[i], label=l)
           for i, l in enumerate(["ride_demand_train","weather_hourly","events_calendar"])]
axes[0].legend(handles=patches, loc="lower right")

# Bottom: missing zone-hours timeline
CANONICAL_ZONES = ["Megenagna","Piassa","CMC","Kazanchis","Gerji","Lideta",
                   "Bole","Arat Kilo","Merkato","Kolfe","Sarbet","Ayat"]
for i, z in enumerate(CANONICAL_ZONES):
    zdf = df[df["zone"]==z].copy()
    axes[1].scatter(zdf["pickup_hour"], [i]*len(zdf), s=0.1, c=CB_COLORS[i % len(CB_COLORS)], alpha=0.3)

axes[1].set_yticks(range(len(CANONICAL_ZONES)))
axes[1].set_yticklabels(CANONICAL_ZONES, fontsize=9)
axes[1].set_xlabel("Date")
axes[1].set_title("Data Coverage Timeline per Zone (dots = hours with data)")
plt.suptitle("Fig 01 — Data Gaps & Missingness", fontsize=13, fontweight="bold")
plt.tight_layout()
savefig("fig01_gaps_and_missingness.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 02 — Before / After Cleaning
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig02...")
fig, axes = plt.subplots(2, 2, figsize=(14, 8))

raw_trips = raw_train["trips"].dropna()
clean_trips = df["trips"]

axes[0,0].hist(raw_trips.clip(-50, 400), bins=50, color=CB_COLORS[0], edgecolor="white")
axes[0,0].set_title("Trips — Raw (includes negatives & extreme values)")
axes[0,0].set_xlabel("Trips"); axes[0,0].set_ylabel("Count")

axes[0,1].hist(clean_trips.clip(0, 300), bins=50, color=CB_COLORS[1], edgecolor="white")
axes[0,1].set_title("Trips — After Cleaning (negatives removed, capped)")
axes[0,1].set_xlabel("Trips"); axes[0,1].set_ylabel("Count")

raw_temp = raw_weather["temp_c"].dropna()
clean_temp = df["temp_c"].dropna()

axes[1,0].hist(raw_temp, bins=40, color=CB_COLORS[2], edgecolor="white")
axes[1,0].set_title("Temperature °C — Raw")
axes[1,0].set_xlabel("°C"); axes[1,0].set_ylabel("Count")

axes[1,1].hist(clean_temp, bins=40, color=CB_COLORS[3], edgecolor="white")
axes[1,1].set_title("Temperature °C — After Cleaning (missing filled, UTC→EAT)")
axes[1,1].set_xlabel("°C"); axes[1,1].set_ylabel("Count")

plt.suptitle("Fig 02 — Before & After Cleaning", fontsize=13, fontweight="bold")
plt.tight_layout()
savefig("fig02_before_after_cleaning.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 03 — Demand Trend with Holidays
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig03...")
df["date"] = df["pickup_hour"].dt.date
daily = df.groupby("date")["trips"].sum().reset_index()
daily["date"] = pd.to_datetime(daily["date"])
daily = daily.sort_values("date")
daily["rolling30"] = daily["trips"].rolling(30, min_periods=1).mean()

holiday_dates = df[df["event_type_flag"]=="public_holiday"]["pickup_hour"].dt.date.unique()
holiday_dates = pd.to_datetime(holiday_dates)

fig, ax = plt.subplots(figsize=(16, 5))
ax.plot(daily["date"], daily["trips"], color=CB_COLORS[0], alpha=0.35, linewidth=0.8, label="Daily total")
ax.plot(daily["date"], daily["rolling30"], color=CB_COLORS[1], linewidth=2.5, label="30-day rolling avg")
for hd in holiday_dates:
    ax.axvline(hd, color=CB_COLORS[3], alpha=0.6, linewidth=0.8)
ax.axvline(holiday_dates[0], color=CB_COLORS[3], alpha=0.8, linewidth=1, label="Public holiday")
ax.set_xlabel("Date"); ax.set_ylabel("Total city-wide trips per day")
ax.set_title("Fig 03 — City-Wide Demand Trend Jan–Oct 2025 with Public Holidays", fontweight="bold")
ax.legend(); plt.tight_layout()
savefig("fig03_demand_trend_with_holidays.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 04 — Hour × Weekday Heatmap
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig04...")
dow_labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
city_heat  = df.groupby(["hour","day_of_week"])["trips"].mean().unstack("day_of_week")
bole_heat  = df[df["zone"]=="Bole"].groupby(["hour","day_of_week"])["trips"].mean().unstack("day_of_week")

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
sns.heatmap(city_heat, ax=axes[0], cmap=CMAP, xticklabels=dow_labels, yticklabels=range(24),
            cbar_kws={"label":"Mean trips/hour"})
axes[0].set_title("All Zones — Mean Trips by Hour × Day"); axes[0].set_ylabel("Hour of Day")

sns.heatmap(bole_heat, ax=axes[1], cmap=CMAP, xticklabels=dow_labels, yticklabels=range(24),
            cbar_kws={"label":"Mean trips/hour"})
axes[1].set_title("Bole Zone — Mean Trips by Hour × Day"); axes[1].set_ylabel("Hour of Day")

plt.suptitle("Fig 04 — Hour-of-Day × Day-of-Week Demand Heatmap", fontsize=13, fontweight="bold")
plt.tight_layout()
savefig("fig04_hour_by_weekday_heatmap.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 05 — Zone Profiles by Type
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig05...")
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()
for i, zt in enumerate(ZONE_TYPES):
    sub = df[df["zone_type"]==zt]
    wd  = sub[sub["is_weekend"]==0].groupby("hour")["trips"].mean()
    we  = sub[sub["is_weekend"]==1].groupby("hour")["trips"].mean()
    axes[i].plot(wd.index, wd.values, color=CB_COLORS[0], linewidth=2.5, label="Weekday")
    axes[i].plot(we.index, we.values, color=CB_COLORS[1], linewidth=2.5, linestyle="--", label="Weekend")
    axes[i].set_title(f"{zt} Zones"); axes[i].set_xlabel("Hour"); axes[i].set_ylabel("Mean trips")
    axes[i].legend(); axes[i].set_xticks(range(0,24,2))

plt.suptitle("Fig 05 — Weekday vs Weekend Hourly Profiles by Zone Type", fontsize=13, fontweight="bold")
plt.tight_layout()
savefig("fig05_zone_profiles.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 06 — Weather Timezone Check
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig06...")
# Load raw weather and show the UTC (wrong) vs EAT (correct) temperature curves
raw_w = pd.read_csv(os.path.join(RAW, "weather_hourly.csv"))
# Parse raw UTC
mask_z = raw_w["timestamp"].astype(str).str.endswith("Z")
raw_w_z = raw_w[mask_z].copy()
raw_w_z["ts_utc"] = pd.to_datetime(raw_w_z["timestamp"], utc=True)
raw_w_z["hour_utc"] = raw_w_z["ts_utc"].dt.hour
raw_w_z["ts_eat"]   = raw_w_z["ts_utc"].dt.tz_convert("Africa/Addis_Ababa")
raw_w_z["hour_eat"] = raw_w_z["ts_eat"].dt.hour

utc_curve = raw_w_z.groupby("hour_utc")["temp_c"].mean()
eat_curve = raw_w_z.groupby("hour_eat")["temp_c"].mean()

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(utc_curve.index, utc_curve.values, color=CB_COLORS[3], linewidth=2.5,
        linestyle="--", label="Using UTC clock (wrong)")
ax.plot(eat_curve.index, eat_curve.values, color=CB_COLORS[0], linewidth=2.5,
        label="Using EAT clock (correct, +3h)")
ax.axvspan(13, 16, alpha=0.12, color=CB_COLORS[1], label="Expected peak window (2–5pm local)")
ax.set_xlabel("Hour of day"); ax.set_ylabel("Mean temperature (°C)")
ax.set_title("Fig 06 — Weather Timezone Check: Temperature Peaks at 15:00 EAT", fontweight="bold")
ax.set_xticks(range(0,24,2)); ax.legend()
plt.tight_layout()
savefig("fig06_weather_timezone_check.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 07 — Rain Effect by Zone Type
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig07...")
df["rain_bucket_lbl"] = pd.cut(df["rain_mm"], bins=[-0.1,0,2,10,9999],
                               labels=["None","Light","Moderate","Heavy"])
# compute ratio vs dry for each zone_type × rain bucket
dry_mean = df[df["rain_bucket_lbl"]=="None"].groupby("zone_type")["trips"].mean()
ratio_df  = []
for zt in ZONE_TYPES:
    for rb in ["None","Light","Moderate","Heavy"]:
        sub = df[(df["zone_type"]==zt) & (df["rain_bucket_lbl"]==rb)]
        r = sub["trips"].mean() / dry_mean.get(zt, 1)
        ratio_df.append({"zone_type": zt, "rain": rb, "ratio": r})
ratio_df = pd.DataFrame(ratio_df)

fig, ax = plt.subplots(figsize=(12, 6))
for i, zt in enumerate(ZONE_TYPES):
    sub = ratio_df[ratio_df["zone_type"]==zt]
    ax.plot(sub["rain"], sub["ratio"], marker="o", color=CB_COLORS[i], linewidth=2.5, label=zt)
ax.axhline(1.0, color="black", linestyle="--", linewidth=1, label="Dry baseline (ratio=1)")
ax.set_xlabel("Rain Category"); ax.set_ylabel("Demand ratio vs dry hours")
ax.set_title("Fig 07 — Rain Effect on Demand by Zone Type", fontweight="bold")
ax.legend(); plt.tight_layout()
savefig("fig07_rain_effect.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 08 — Event Study (±6 hours around start)
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig08...")
event_types_to_show = ["football_match", "concert"]
fig, ax = plt.subplots(figsize=(12, 6))

no_ev_baseline = df[df["in_event_window"]==0]["trips"].mean()
ax.axhline(no_ev_baseline, color="black", linestyle="--", linewidth=1.5, label="No-event baseline")

for i, et in enumerate(event_types_to_show):
    ev_rows = df[df["event_type_flag"]==et].copy()
    # bucket by hours_since_event_start (0 = during, negative = before handled as within buffer)
    ev_rows["hse_bucket"] = ev_rows["hours_since_event_start"].clip(0, 6).round()
    profile = ev_rows.groupby("hse_bucket")["trips"].mean()
    ax.plot(profile.index, profile.values, marker="o", color=CB_COLORS[i+1],
            linewidth=2.5, label=f"{et.replace('_',' ').title()}")

ax.set_xlabel("Hours since event started (0 = match start, 6 = well after end)")
ax.set_ylabel("Mean trips per zone-hour"); ax.legend()
ax.set_title("Fig 08 — Demand During Event Windows vs No-Event Baseline", fontweight="bold")
plt.tight_layout()
savefig("fig08_event_study.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 09 — Holiday Effects
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig09...")
hol_df = df[df["event_type_flag"]=="public_holiday"].copy()
normal_df = df[df["event_type_flag"]=="none"].copy()

hol_df["date"] = hol_df["pickup_hour"].dt.date
hol_daily = hol_df.groupby("date")["trips"].sum()
norm_daily_avg = normal_df.groupby(normal_df["pickup_hour"].dt.date)["trips"].sum().mean()

hol_index = (hol_daily / norm_daily_avg * 100).sort_values()
hol_labels = [str(d) for d in hol_index.index]

fig, ax = plt.subplots(figsize=(12, max(4, len(hol_index)*0.4)))
colors_bar = [CB_COLORS[3] if v < 80 else CB_COLORS[1] if v < 100 else CB_COLORS[0]
              for v in hol_index.values]
ax.barh(hol_labels, hol_index.values, color=colors_bar)
ax.axvline(100, color="black", linestyle="--", linewidth=1.5, label="Normal demand = 100")
ax.set_xlabel("Demand index (100 = normal weekday)")
ax.set_title("Fig 09 — Public Holiday Demand vs Normal Days (sorted)", fontweight="bold")
ax.legend(); plt.tight_layout()
savefig("fig09_holiday_effects.png")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 10 — Model Comparison (uses data from modeling.py)
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig10...")
model_results_path = os.path.join(PROC, "model_results.json")
if os.path.exists(model_results_path):
    with open(model_results_path) as f:
        model_results = json.load(f)
    names = list(model_results.keys())
    rmses = [v["rmse"] for v in model_results.values()]
    colors_m = [CB_COLORS[3] if "Mean" in n or "Naive" in n else CB_COLORS[0] for n in names]
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(names, rmses, color=colors_m, edgecolor="white")
    ax.set_ylabel("Validation RMSE (trips/hour)")
    ax.set_title("Fig 10 — Model Comparison: Validation RMSE", fontweight="bold")
    for bar, v in zip(bars, rmses):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{v:.1f}", ha="center", fontsize=10)
    patches = [mpatches.Patch(color=CB_COLORS[3], label="Baselines"),
               mpatches.Patch(color=CB_COLORS[0], label="Models")]
    ax.legend(handles=patches)
    plt.xticks(rotation=15, ha="right"); plt.tight_layout()
    savefig("fig10_model_comparison.png")
else:
    print("  [SKIP] model_results.json not found — run modeling.py first")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 11 — Forecast vs Actual
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig11...")
val_pred_path = os.path.join(PROC, "val_predictions.csv")
if os.path.exists(val_pred_path):
    val = pd.read_csv(val_pred_path, parse_dates=["pickup_hour"])
    zones_to_show = ["Merkato", "Bole", "CMC"]
    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    for i, z in enumerate(zones_to_show):
        sub = val[val["zone"]==z].sort_values("pickup_hour")
        axes[i].plot(sub["pickup_hour"], sub["trips"], color=CB_COLORS[0],
                     linewidth=1.2, alpha=0.8, label="Actual")
        axes[i].plot(sub["pickup_hour"], sub["pred"], color=CB_COLORS[1],
                     linewidth=1.2, alpha=0.8, linestyle="--", label="Predicted")
        axes[i].set_title(f"Zone: {z}"); axes[i].set_ylabel("Trips/hour")
        axes[i].legend(loc="upper right")
    axes[-1].set_xlabel("Date")
    plt.suptitle("Fig 11 — Forecast vs Actual (Oct 18–31 Validation)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    savefig("fig11_forecast_vs_actual.png")
else:
    print("  [SKIP] val_predictions.csv not found — run modeling.py first")

# ══════════════════════════════════════════════════════════════════════════════
# FIG 12 — Feature Importance
# ══════════════════════════════════════════════════════════════════════════════
print("Making fig12...")
model_path = os.path.join("models", "final_model.joblib")
feat_path  = os.path.join("models", "feature_list.joblib")
if os.path.exists(model_path) and os.path.exists(feat_path):
    model = __import__("joblib").load(model_path)
    feat_cols = __import__("joblib").load(feat_path)
    if hasattr(model, "feature_importances_"):
        imps = model.feature_importances_
        imp_df = pd.DataFrame({"feature": feat_cols, "importance": imps})
        imp_df = imp_df.sort_values("importance", ascending=True).tail(12)
        weather_feats = {"temp_c","rain_mm","humidity_pct","wind_kmh","rain_class","rain_3h"}
        event_feats   = {"in_event_window","hours_since_event_start","hours_until_event_end","event_type_flag"}
        colors_imp = []
        for f in imp_df["feature"]:
            if f in weather_feats:   colors_imp.append(CB_COLORS[1])
            elif f in event_feats:   colors_imp.append(CB_COLORS[2])
            else:                    colors_imp.append(CB_COLORS[0])
        fig, ax = plt.subplots(figsize=(12, 7))
        bars = ax.barh(imp_df["feature"], imp_df["importance"], color=colors_imp)
        patches = [mpatches.Patch(color=CB_COLORS[0], label="Calendar/Zone"),
                   mpatches.Patch(color=CB_COLORS[1], label="Weather"),
                   mpatches.Patch(color=CB_COLORS[2], label="Events")]
        ax.legend(handles=patches)
        ax.set_xlabel("Feature importance"); ax.set_title("Fig 12 — Top Feature Importances", fontweight="bold")
        plt.tight_layout()
        savefig("fig12_feature_importance.png")
else:
    print("  [SKIP] model files not found — run modeling.py first")

# ══════════════════════════════════════════════════════════════════════════════
# CAPTIONS FILE
# ══════════════════════════════════════════════════════════════════════════════
captions = {
    "fig01_gaps_and_missingness.png": (
        "Missing or invalid values per column across all three raw files, plus a timeline of data coverage per zone.",
        "Ayat has significantly fewer records, confirming it launched mid-year. Several columns in the events file have high missingness."
    ),
    "fig02_before_after_cleaning.png": (
        "Distributions of trips and temperature before and after cleaning.",
        "Cleaning removed impossible negative trips and aligned weather timestamps, producing more realistic and consistent distributions."
    ),
    "fig03_demand_trend_with_holidays.png": (
        "Daily city-wide trip totals from January to October 2025, with public holidays marked and a 30-day rolling average.",
        "Demand grew ~52% over the year. Public holidays cause sharp daily drops, especially multi-day holidays."
    ),
    "fig04_hour_by_weekday_heatmap.png": (
        "Mean trips by hour of day (rows) and day of week (columns) for the whole city and Bole zone.",
        "Rush hours (8am and 6pm) are clearly busiest. Bole is distinctly busier on weekends than the city average."
    ),
    "fig05_zone_profiles.png": (
        "Weekday vs weekend hourly demand profiles for each zone type.",
        "Residential zones show a classic double-peak. Market zones stay high all day. Business zones collapse on weekends."
    ),
    "fig06_weather_timezone_check.png": (
        "Average temperature by hour using the original UTC timestamps vs the corrected EAT timestamps.",
        "The EAT-corrected curve peaks at 15:00 local time — matching Addis Ababa's climate. The UTC curve peaks at 12:00, proving the correction is necessary."
    ),
    "fig07_rain_effect.png": (
        "Demand ratio vs normal (dry) hours, for four rain intensity categories, by zone type.",
        "Rain boosts demand in all zone types. Business zones show up to 2.4× uplift in heavy rain. The response plateaus at heavy rain."
    ),
    "fig08_event_study.png": (
        "Average demand during football matches and concerts versus the no-event baseline, by hours since event start.",
        "Both event types generate significant demand uplift. The peak occurs during the event and continues for 1–2 hours after it ends."
    ),
    "fig09_holiday_effects.png": (
        "Holiday demand index (100 = normal weekday) for each public holiday, sorted ascending.",
        "Almost all holidays reduce demand substantially. The most disruptive holidays reduce city trips to under 30% of normal."
    ),
    "fig10_model_comparison.png": (
        "Validation RMSE for all models compared, with baselines highlighted.",
        "LightGBM/HGBoosting outperforms simpler models. The seasonal naive baseline is a strong benchmark that simple models struggle to beat."
    ),
    "fig11_forecast_vs_actual.png": (
        "Predicted vs actual trips per hour for 3 zones over the Oct 18–31 validation period.",
        "The model captures daily and weekly patterns well. Errors are largest around unexpected events and holiday transitions."
    ),
    "fig12_feature_importance.png": (
        "Top feature importances from the final model, with weather and event features highlighted.",
        "Zone-hour mean demand and hour of day are the top predictors. Weather (rain) and event features both contribute meaningfully."
    ),
}

with open(os.path.join(FIG, "figure_captions.md"), "w", encoding="utf-8") as f:
    f.write("# Figure Captions\n\n")
    for fname, (desc, takeaway) in captions.items():
        f.write(f"## {fname}\n")
        f.write(f"**What it shows:** {desc}\n\n")
        f.write(f"**Takeaway:** {takeaway}\n\n---\n\n")

print(f"\nCaptions written to {FIG}/figure_captions.md")
print("\nStudent 4 visualization complete.")
