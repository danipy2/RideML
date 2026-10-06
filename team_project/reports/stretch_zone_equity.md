# Stretch Goal — Zone Equity Analysis

*Does our forecast do worse in any zone? What would under-forecasting mean for drivers and riders there?*

---

## Forecast Accuracy by Zone

| Zone | Avg Demand (trips/hr) | MAE | RMSE | % Error | Equity Flag |
|---|---|---|---|---|---|
| Merkato | 49.2 | 8.06 | 13.35 | 16.4% | ⚠️ Highest absolute error |
| Megenagna | 44.3 | 7.93 | 12.05 | 17.9% | ⚠️ High |
| Piassa | 34.3 | 6.22 | 12.31 | 18.2% | ⚠️ Highest % error among top zones |
| Kazanchis | 39.3 | 6.91 | 11.19 | 17.6% | ⚠️ High |
| Bole | 45.5 | 7.39 | 10.36 | 16.2% | ⚠️ High |
| Lideta | 33.6 | 5.50 | 7.68 | 16.4% | ✅ Moderate |
| CMC | 29.9 | 5.19 | 7.19 | 17.3% | ✅ Moderate |
| Arat Kilo | 24.1 | 4.61 | 6.69 | **19.1%** | ⚠️ Highest % error overall |
| Kolfe | 26.9 | 4.79 | 6.62 | 17.8% | ✅ Moderate |
| Gerji | 28.7 | 4.87 | 6.60 | 17.0% | ✅ Moderate |
| Sarbet | 25.4 | 4.59 | 6.29 | 18.1% | ✅ Moderate |
| Ayat | 21.3 | 4.20 | 5.89 | **19.7%** | 🔴 Highest % error (newest zone) |

---

## Key Finding: Two Equity Concerns

### 1. Ayat — Highest Percentage Error (19.7%)
Ayat launched later in 2025 (missing ~1,896 early zone-hours). The model has less historical data for this zone, meaning `zone_hour_mean` is estimated from fewer observations and is less stable.

**Impact on drivers:** If we forecast 18 trips/hr in Ayat at 8pm but true demand is 22, 4 drivers are undeployed. In a lower-volume zone, those 4 missing drivers represent a 22% shortfall — riders experience significantly longer waits.

### 2. Arat Kilo — Second Highest Percentage Error (19.1%)
Arat Kilo is a mixed/transport hub with high variance (government offices + bus terminals + universities). Its demand pattern is harder to predict than pure residential or market zones.

---

## What Under-Forecasting Means by Zone

| Zone | Under-forecast by 1 MAE → | Consequence |
|---|---|---|
| Merkato (MAE=8) | 8 fewer drivers than needed | In Ethiopia's busiest market zone, 8 missing drivers at peak = ~10 riders waiting >10 min |
| Ayat (MAE=4.2, but 20% of demand) | Demand undershoots by 20% | Smaller zone, so 4 missing drivers = large share of needed supply |
| Kazanchis (MAE=6.9 on weekends) | Business zone unusually busy on Sat/Sun | Weekend demand pattern less learned; drivers sent home too early |

---

## Proposed Mitigation

**For Ayat (data scarcity):**
> Train a **zone-specific correction factor** for Ayat. After the global model predicts, multiply by `(mean_demand_city / mean_demand_ayat_in_training)` weighted by recency. As Ayat accumulates more data, this correction converges to 1.0 and becomes unnecessary.

Alternatively: **add a `months_since_zone_launch` feature**. This gives the model a signal that predictions for new zones are inherently less certain, allowing it to regress toward the city-wide mean.

**For high-error rush hours (18:00 MAE=11.0):**
> Add a **10% driver buffer** at peak hours (7am, 5–7pm) in the top-3 error zones (Merkato, Megenagna, Bole). Cost: ~3 extra deployed drivers per zone per peak hour. Benefit: covers the typical under-forecast with minimal waste.

**General principle:** Our model is most accurate in low-demand, late-night hours (MAE ~2). It is least accurate during peak hours with event overlap. Operations should treat peak-hour forecasts as lower bounds and maintain a 10-15% driver buffer during those windows.

---

## Accuracy by Hour of Day

| Hour | MAE | Pattern |
|---|---|---|
| 18:00 | 11.03 | Hardest — evening rush + event peak |
| 17:00 | 8.38 | Rush hour |
| 07:00 | 8.40 | Morning rush |
| 19:00 | 8.37 | Post-event crowd dispersal |
| 08:00 | 8.14 | Morning rush |
| 03:00 | ~2.0 | Easiest — low, stable demand |

## Accuracy by Day Type

| Day Type | MAE |
|---|---|
| Weekday | 5.82 |
| Weekend | 5.94 |

Weekend errors are marginally higher (+0.12 MAE) — leisure demand is less predictable than commuting patterns. This is expected and acceptable.

---

## Summary

Our model performs equitably across zones in percentage terms (14–20% error for all 12 zones). The two zones with the highest percentage error are Ayat (newest, least data) and Arat Kilo (highest demand variance). Under-forecasting in Ayat has disproportionate impact on riders because the zone has fewer drivers in the area as a baseline. The proposed mitigations are lightweight and could be implemented before a production deployment.
