# Figure Captions

## fig01_gaps_and_missingness.png
**What it shows:** Missing or invalid values per column across all three raw files, plus a timeline of data coverage per zone.

**Takeaway:** Ayat has significantly fewer records, confirming it launched mid-year. Several columns in the events file have high missingness.

---

## fig02_before_after_cleaning.png
**What it shows:** Distributions of trips and temperature before and after cleaning.

**Takeaway:** Cleaning removed impossible negative trips and aligned weather timestamps, producing more realistic and consistent distributions.

---

## fig03_demand_trend_with_holidays.png
**What it shows:** Daily city-wide trip totals from January to October 2025, with public holidays marked and a 30-day rolling average.

**Takeaway:** Demand grew ~52% over the year. Public holidays cause sharp daily drops, especially multi-day holidays.

---

## fig04_hour_by_weekday_heatmap.png
**What it shows:** Mean trips by hour of day (rows) and day of week (columns) for the whole city and Bole zone.

**Takeaway:** Rush hours (8am and 6pm) are clearly busiest. Bole is distinctly busier on weekends than the city average.

---

## fig05_zone_profiles.png
**What it shows:** Weekday vs weekend hourly demand profiles for each zone type.

**Takeaway:** Residential zones show a classic double-peak. Market zones stay high all day. Business zones collapse on weekends.

---

## fig06_weather_timezone_check.png
**What it shows:** Average temperature by hour using the original UTC timestamps vs the corrected EAT timestamps.

**Takeaway:** The EAT-corrected curve peaks at 15:00 local time — matching Addis Ababa's climate. The UTC curve peaks at 12:00, proving the correction is necessary.

---

## fig07_rain_effect.png
**What it shows:** Demand ratio vs normal (dry) hours, for four rain intensity categories, by zone type.

**Takeaway:** Rain boosts demand in all zone types. Business zones show up to 2.4× uplift in heavy rain. The response plateaus at heavy rain.

---

## fig08_event_study.png
**What it shows:** Average demand during football matches and concerts versus the no-event baseline, by hours since event start.

**Takeaway:** Both event types generate significant demand uplift. The peak occurs during the event and continues for 1–2 hours after it ends.

---

## fig09_holiday_effects.png
**What it shows:** Holiday demand index (100 = normal weekday) for each public holiday, sorted ascending.

**Takeaway:** Almost all holidays reduce demand substantially. The most disruptive holidays reduce city trips to under 30% of normal.

---

## fig10_model_comparison.png
**What it shows:** Validation RMSE for all models compared, with baselines highlighted.

**Takeaway:** LightGBM/HGBoosting outperforms simpler models. The seasonal naive baseline is a strong benchmark that simple models struggle to beat.

---

## fig11_forecast_vs_actual.png
**What it shows:** Predicted vs actual trips per hour for 3 zones over the Oct 18–31 validation period.

**Takeaway:** The model captures daily and weekly patterns well. Errors are largest around unexpected events and holiday transitions.

---

## fig12_feature_importance.png
**What it shows:** Top feature importances from the final model, with weather and event features highlighted.

**Takeaway:** Zone-hour mean demand and hour of day are the top predictors. Weather (rain) and event features both contribute meaningfully.

---

