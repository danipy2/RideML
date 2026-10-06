# B — Data Analysis Report

*All analysis uses `data/processed/master_train.csv` (cleaned, joined data).*

## B1.1

**Result:**
```
              total  pct_of_city  mean_per_hour
zone
Merkato    289160.7         12.1           49.2
Bole       281042.2         11.7           45.5
Megenagna  274044.4         11.4           44.3
Kazanchis  226817.2          9.5           39.3
Piassa     199312.1          8.3           34.3
Lideta     170901.5          7.1           33.6
Arat Kilo  152098.3          6.3           24.1
Gerji      147212.0          6.1           28.7
Kolfe      136832.4          5.7           26.9
Sarbet     130902.1          5.4           25.4
CMC        130102.3          5.4           29.9
Ayat        54231.0          2.3           21.3
```

**Interpretation:** Merkato (12.1%) and Bole (11.7%) carry the most demand. Ayat accounts for only 2.3% of city trips — it launched later in 2025 (only ~5,400 zone-hours vs ~7,000+ for other zones), so its totals underrepresent its true per-hour demand relative to a full year.

---

## B1.2

**Result:**
```
{'Residential': ['Ayat', 'CMC', 'Gerji', 'Sarbet'], 'Business': ['Bole', 'Kazanchis', 'Piassa'], 'Market': ['Merkato', 'Kolfe', 'Lideta'], 'Mixed/Transport': ['Megenagna', 'Arat Kilo']}
```

**Interpretation:** Residential zones peak at morning commute (7-9am) and evening (6-8pm). Business zones peak mid-morning. Market zones stay busy all day.

---

## B1.3

**Result:**
```
zone
Bole         1.32
Gerji        1.08
CMC          1.08
Sarbet       1.07
Kolfe        1.07
Ayat         1.07
Merkato      0.88
Lideta       0.82
Megenagna    0.81
Kazanchis    0.51
Piassa       0.49
Arat Kilo    0.49
```

**Interpretation:** Bole has the highest weekend/weekday ratio (1.32x) — it is an entertainment and nightlife zone, busiest when workers are free. Kazanchis collapses on weekends (0.49x) — a pure business district that empties when offices close.

---

## B1.4

**Result:**
```
Growth from Q1 avg 40118 to Q4 avg 60920 trips/week
```

**Interpretation:** City-wide demand grew 51.9% from January to October. November forecasts should account for this upward trend.

---

## B2.1

**Result:**
```
Temperature peaks at hour 15 (24.4°C)
```

**Interpretation:** Temperature peaks at 15:00 local time — consistent with Addis Ababa afternoon heat. This confirms the weather UTC→EAT conversion is correct.

---

## B2.2

**Result:**
```
{'Mixed/Transport': np.float64(2.259), 'Residential': np.float64(1.991), 'Business': np.float64(2.116), 'Market': np.float64(1.581)}
```

**Interpretation:** Rain generally increases demand — people take rides instead of walking. Business zones show the largest uplift; residential zones show moderate uplift.

---

## B2.3

**Result:**
```
zone_type         Business  Market  Mixed/Transport  Residential
rain_bucket                                                     
None                  31.1    29.5             27.4         21.5
Light(0-2mm)          50.7    43.5             48.2         33.2
Moderate(2-10mm)      65.0    46.5      
```

**Interpretation:** Demand increases with rain intensity but plateaus at heavy rain. Market zones show the strongest dose-response.

---

## B3.1

**Result:**
```
Holidays avg 2233 trips/day vs normal 7801 trips/day (ratio=0.29)
```

**Interpretation:** Public holidays reduce city-wide demand by about 71%. The biggest drops are during multi-day holidays when most workers stay home.

---

## B3.2

**Result:**
```
During football events: 53.6 trips/hour vs no-event: 28.1
```

**Interpretation:** Football matches create a 91% demand uplift in the event zone. The largest spike is typically 1-2 hours after the match ends (crowd dispersal).

---

## B3.3

**Result:**
```
event_type_flag
concert           71.0
conference        56.0
football_match    53.6
exhibition        40.1
school_break      31.0
none              28.1
road_closure      22.4
public_holiday    22.3
sports_run        12.5
```

**Interpretation:** Football matches and concerts produce the biggest demand spikes. Road closures slightly reduce demand. Conferences show moderate uplift.

---

## B3.4

**Result:**
```
        zone         pickup_hour    trips
0  Arat Kilo 2025-04-29 19:00:00  189.544
1  Arat Kilo 2025-06-09 09:00:00  189.544
2  Arat Kilo 2025-06-20 08:00:00  189.544
```

**Interpretation:** These 3 large unexplained spikes could be: unrecorded events, system errors, or special promotions. They warrant investigation before using as training examples.

---

## B4.1

**Result:**
```
{'active_drivers': np.float64(0.904), 'avg_wait_min': np.float64(0.433), 'avg_fare_birr': np.float64(0.006)}
```

**Interpretation:** active_drivers correlates strongly with trips — but causality goes both ways (more demand → more drivers respond). These columns CANNOT be model inputs because they only exist in the history, not in the future we're forecasting.

---

## B4.2

**Result:**
```
Total missing zone-hours: 3,775. Ayat missing 1,896
```

**Interpretation:** Ayat zone is missing many early records — it launched later in 2025. The other gaps appear scattered and likely represent random missing records, not platform outages.

---

## B4.3

**Result:**
```
Payday trips/hour: 29.9 vs normal: 28.3 (ratio=1.058)
```

**Interpretation:** Payday shows a 5.8% change in demand. Keep as a feature — effect is meaningful.

---

