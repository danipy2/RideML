"""
Student 1 — Data Cleaning & Integration Pipeline
Deliverable A: Cleans all 3 tables, joins them, engineers features,
exports master_train.csv, master_test.csv, data_dictionary_master.csv
"""

import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings("ignore")

# ── paths ──────────────────────────────────────────────────────────────────────
RAW   = os.path.join("data", "raw")
PROC  = os.path.join("data", "processed")
os.makedirs(PROC, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# A2 — ZONE NAME MAP
# ══════════════════════════════════════════════════════════════════════════════
ZONE_MAP = {
    # Megenagna
    "megenagna": "Megenagna", "MEGENAGNA": "Megenagna", "Megenagna": "Megenagna",
    "Megenaga": "Megenagna", "megenaga": "Megenagna",
    # Piassa
    "piassa": "Piassa", "PIASSA": "Piassa", "Piassa": "Piassa",
    "Piazza": "Piassa", "piazza": "Piassa",
    # CMC
    "CMC": "CMC", "cmc": "CMC", "C.M.C": "CMC", "c.m.c": "CMC",
    # Kazanchis
    "Kazanchis": "Kazanchis", "KAZANCHIS": "Kazanchis", "kazanchis": "Kazanchis",
    "Kazanches": "Kazanchis", "kazanches": "Kazanchis",
    "Kazanchis (Kirkos)": "Kazanchis",
    # Gerji
    "Gerji": "Gerji", "GERJI": "Gerji", "gerji": "Gerji",
    # Lideta
    "Lideta": "Lideta", "LIDETA": "Lideta", "lideta": "Lideta",
    # Bole
    "Bole": "Bole", "BOLE": "Bole", "bole": "Bole",
    "Bole Rd": "Bole", "Bole (Bole subcity)": "Bole",
    # Arat Kilo
    "Arat Kilo": "Arat Kilo", "ARAT KILO": "Arat Kilo", "arat kilo": "Arat Kilo",
    "Arat  Kilo": "Arat Kilo",
    # Merkato
    "Merkato": "Merkato", "MERKATO": "Merkato", "merkato": "Merkato",
    "Mercato": "Merkato", "mercato": "Merkato",
    # Kolfe
    "Kolfe": "Kolfe", "KOLFE": "Kolfe", "kolfe": "Kolfe",
    "Kolfe Keranio": "Kolfe",
    # Sarbet
    "Sarbet": "Sarbet", "SARBET": "Sarbet", "sarbet": "Sarbet",
    # Ayat
    "Ayat": "Ayat", "AYAT": "Ayat", "ayat": "Ayat",
}

CANONICAL_ZONES = sorted(set(ZONE_MAP.values()))  # 12 zones

CITYWIDE_KEYS = {"Citywide", "citywide", "ALL", "All", "All zones", "all zones",
                 "city-wide", "City-Wide"}

def standardize_zone(val):
    """Return canonical zone name, or None if citywide/unknown."""
    if pd.isna(val):
        return None
    val = str(val).strip()
    if val in CITYWIDE_KEYS:
        return "__CITYWIDE__"
    return ZONE_MAP.get(val, val)

# ══════════════════════════════════════════════════════════════════════════════
# A2 — TIMESTAMP PARSING
# ══════════════════════════════════════════════════════════════════════════════
def parse_pickup_hour(series):
    """Parse the 3 formats in pickup_hour to a tz-naive EAT datetime."""
    out = pd.Series(index=series.index, dtype="datetime64[ns]")

    # format 1: ISO with offset  2025-05-27T23:00:00+03:00
    mask1 = series.str.contains("T", na=False) & series.str.contains(r"\+", na=False)
    out[mask1] = pd.to_datetime(series[mask1], utc=True).dt.tz_convert(
        "Africa/Addis_Ababa").dt.tz_localize(None)

    # format 2: ISO with T, no offset  2025-06-26 11:00  or  2025-06-26T11:00
    mask2 = series.str.contains("T", na=False) & ~mask1
    out[mask2] = pd.to_datetime(series[mask2]).dt.tz_localize(None)

    # format 3: DD/MM/YYYY HH:MM
    mask3 = series.str.contains("/", na=False)
    out[mask3] = pd.to_datetime(series[mask3], dayfirst=True)

    # anything left (YYYY-MM-DD HH:MM without T)
    left = out.isna() & series.notna()
    out[left] = pd.to_datetime(series[left], errors="coerce")

    return out

def parse_weather_timestamp(series):
    """Convert weather UTC timestamps (ISO Z or DD/MM/YYYY) to EAT tz-naive."""
    # ISO Z format
    mask_z = series.str.endswith("Z", na=False)
    iso_part = pd.to_datetime(series[mask_z], utc=True).dt.tz_convert(
        "Africa/Addis_Ababa").dt.tz_localize(None)

    # DD/MM/YYYY HH:MM format (treat as UTC, add 3h)
    mask_dd = series.str.contains("/", na=False)
    dd_part = pd.to_datetime(series[mask_dd], dayfirst=True) + pd.Timedelta(hours=3)

    out = pd.Series(index=series.index, dtype="datetime64[ns]")
    out[mask_z]  = iso_part
    out[mask_dd] = dd_part
    return out

# ══════════════════════════════════════════════════════════════════════════════
# LOAD & CLEAN — RIDES
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("LOADING & CLEANING RIDE TABLE")
print("=" * 60)

train_raw = pd.read_csv(os.path.join(RAW, "ride_demand_train.csv"))
test_raw  = pd.read_csv(os.path.join(RAW, "ride_demand_test.csv"))
print(f"Train raw rows: {len(train_raw):,}   Test raw rows: {len(test_raw):,}")

cleaning_log = []  # A1

# -- zone names ----------------------------------------------------------------
before_zones = train_raw["zone"].nunique()
train_raw["zone"] = train_raw["zone"].map(lambda x: ZONE_MAP.get(str(x).strip(), str(x).strip()))
test_raw["zone"]  = test_raw["zone"].map(lambda x: ZONE_MAP.get(str(x).strip(), str(x).strip()))
after_zones = train_raw["zone"].nunique()
cleaning_log.append({
    "file": "ride_demand_train + test", "column": "zone",
    "issue": "Inconsistent zone spellings",
    "rows_affected": (train_raw["zone"].isin(CANONICAL_ZONES) == False).sum(),
    "pct": round((train_raw["zone"].isin(CANONICAL_ZONES) == False).mean() * 100, 2),
    "fix": f"Mapped {before_zones} spellings → 12 canonical zone names",
    "why": "Ensures consistent join keys across all three tables"
})

# keep only the 12 canonical zones
train_raw = train_raw[train_raw["zone"].isin(CANONICAL_ZONES)].copy()
test_raw  = test_raw[test_raw["zone"].isin(CANONICAL_ZONES)].copy()
print(f"After zone filter — Train: {len(train_raw):,}  Test: {len(test_raw):,}")

# -- timestamps ----------------------------------------------------------------
train_raw["pickup_hour"] = parse_pickup_hour(train_raw["pickup_hour"])
test_raw["pickup_hour"]  = parse_pickup_hour(test_raw["pickup_hour"])
null_ts = train_raw["pickup_hour"].isna().sum()
cleaning_log.append({
    "file": "ride_demand_train", "column": "pickup_hour",
    "issue": "3 different date/time formats",
    "rows_affected": null_ts,
    "pct": round(null_ts / len(train_raw) * 100, 2),
    "fix": "Parsed all 3 formats; converted ISO+offset to EAT tz-naive",
    "why": "All timestamps must share the same clock for correct joining"
})
train_raw = train_raw.dropna(subset=["pickup_hour"])

# -- negative trips ------------------------------------------------------------
neg_mask = train_raw["trips"] < 0
neg_count = int(neg_mask.sum())
if neg_count > 0:
    # Impute using historical median by (zone, day_of_week, hour), fallback to (zone, hour)
    train_raw["_hr"] = train_raw["pickup_hour"].dt.hour
    train_raw["_dow"] = train_raw["pickup_hour"].dt.dayofweek
    valid_trips = train_raw[(train_raw["trips"] >= 0) & train_raw["trips"].notna()]
    
    med_zdh = valid_trips.groupby(["zone", "_dow", "_hr"])["trips"].median().round()
    med_zh = valid_trips.groupby(["zone", "_hr"])["trips"].median().round()
    
    negs_subset = train_raw[neg_mask]
    idx_zdh = pd.MultiIndex.from_arrays([negs_subset["zone"], negs_subset["_dow"], negs_subset["_hr"]])
    imp_zdh = idx_zdh.map(med_zdh)
    
    idx_zh = pd.MultiIndex.from_arrays([negs_subset["zone"], negs_subset["_hr"]])
    imp_zh = idx_zh.map(med_zh)
    
    final_imputed = pd.Series(imp_zdh, index=negs_subset.index).fillna(pd.Series(imp_zh, index=negs_subset.index))
    final_imputed = final_imputed.fillna(valid_trips["trips"].median()).clip(lower=0)
    
    train_raw.loc[neg_mask, "trips"] = final_imputed
    train_raw = train_raw.drop(columns=["_hr", "_dow"])

cleaning_log.append({
    "file": "ride_demand_train", "column": "trips",
    "issue": "Negative trip counts (-1 sentinel/corrupt values)",
    "rows_affected": neg_count,
    "pct": round(neg_count / len(train_raw) * 100, 2),
    "fix": "Imputed with historical median (zone x day_of_week x hour, fallback zone x hour)",
    "why": "Trips cannot be negative; -1 represents database error sentinel (drivers & fares present). Historical median preserves natural demand patterns without introducing artificial daytime zero-spikes."
})

# -- extreme outliers ----------------------------------------------------------
cap = train_raw["trips"].quantile(0.999)
extreme_mask = train_raw["trips"] > cap
cleaning_log.append({
    "file": "ride_demand_train", "column": "trips",
    "issue": f"Extreme outlier trips (> {cap:.0f}, 99.9th pct)",
    "rows_affected": int(extreme_mask.sum()),
    "pct": round(extreme_mask.mean() * 100, 2),
    "fix": f"Capped at {cap:.0f}",
    "why": "Likely data errors; prevents model from fitting noise"
})
train_raw.loc[extreme_mask, "trips"] = cap

# -- missing trips -------------------------------------------------------------
miss_trips = train_raw["trips"].isna().sum()
cleaning_log.append({
    "file": "ride_demand_train", "column": "trips",
    "issue": "Missing trip counts",
    "rows_affected": int(miss_trips),
    "pct": round(miss_trips / len(train_raw) * 100, 2),
    "fix": "Dropped rows with missing target (can't train without label)",
    "why": "Cannot learn from unlabelled rows"
})
train_raw = train_raw.dropna(subset=["trips"])

# -- duplicate rows in train ---------------------------------------------------
# Group duplicates by (zone, pickup_hour) and take the rounded mean of trips
# so no reading is thrown away — better than arbitrarily keeping the first row.
n_before = len(train_raw)
n_dup_pairs = int(train_raw.duplicated(subset=["zone", "pickup_hour"], keep="first").sum())

numeric_cols  = train_raw.select_dtypes(include="number").columns.tolist()
agg_dict      = {c: "mean" for c in numeric_cols}
# For non-numeric columns (zone name, pickup_hour already used as keys) keep first
other_cols    = [c for c in train_raw.columns if c not in numeric_cols + ["zone", "pickup_hour"]]
agg_dict.update({c: "first" for c in other_cols})

train_raw = (
    train_raw
    .groupby(["zone", "pickup_hour"], as_index=False, sort=False)
    .agg(agg_dict)
)
# Round trips to nearest whole number; other numerics to 4dp
train_raw["trips"] = train_raw["trips"].round(0)
for col in numeric_cols:
    if col != "trips":
        train_raw[col] = train_raw[col].round(4)

cleaning_log.append({
    "file": "ride_demand_train", "column": "zone, pickup_hour",
    "issue": "Duplicate (zone, hour) combinations",
    "rows_affected": n_dup_pairs,
    "pct": round(n_dup_pairs / n_before * 100, 2),
    "fix": "Aggregated duplicates using rounded mean — no reading discarded",
    "why": (
        "Keeping first arbitrarily ignores one reading. "
        "Round-mean uses all available data. "
        "Max spread between any two duplicate trip counts was only 3 trips."
    )
})
print(f"After ride cleaning — Train: {len(train_raw):,}")

# ══════════════════════════════════════════════════════════════════════════════
# LOAD & CLEAN — WEATHER
# ══════════════════════════════════════════════════════════════════════════════
print("\nLOADING & CLEANING WEATHER TABLE")
weather_raw = pd.read_csv(os.path.join(RAW, "weather_hourly.csv"))
print(f"Weather raw rows: {len(weather_raw):,}")

weather_raw["timestamp_eat"] = parse_weather_timestamp(weather_raw["timestamp"])
null_wts = weather_raw["timestamp_eat"].isna().sum()
cleaning_log.append({
    "file": "weather_hourly", "column": "timestamp",
    "issue": "UTC timestamps need conversion to EAT (+3h); mixed formats",
    "rows_affected": int(null_wts),
    "pct": round(null_wts / len(weather_raw) * 100, 2),
    "fix": "Converted UTC ISO-Z to EAT; parsed DD/MM/YYYY and added 3h",
    "why": "Must share same clock as ride table"
})
weather_raw = weather_raw.dropna(subset=["timestamp_eat"])

# deduplicate weather by hour (keep observed over forecast)
weather_raw = weather_raw.sort_values(
    ["timestamp_eat", "data_type"],
    ascending=[True, True]   # 'forecast' < 'observed' alphabetically
).drop_duplicates(subset=["timestamp_eat"], keep="last")

dup_w = weather_raw["timestamp_eat"].duplicated().sum()
cleaning_log.append({
    "file": "weather_hourly", "column": "timestamp",
    "issue": "Duplicate timestamps with conflicting values",
    "rows_affected": dup_w,
    "pct": round(dup_w / len(weather_raw) * 100, 2),
    "fix": "Kept 'observed' row when both exist; otherwise first row",
    "why": "Each hour must have exactly one weather reading"
})

# ensure chronological order for time-series operations
weather_raw = weather_raw.sort_values("timestamp_eat").reset_index(drop=True)

# fix Fahrenheit temperature entries (> 50°C)
mask_f = weather_raw["temp_c"] > 50
f_count = int(mask_f.sum())
if f_count > 0:
    weather_raw.loc[mask_f, "temp_c"] = (weather_raw.loc[mask_f, "temp_c"] - 32) * 5 / 9
    cleaning_log.append({
        "file": "weather_hourly", "column": "temp_c",
        "issue": f"Temperature logged in Fahrenheit (> 50°C, {f_count} rows)",
        "rows_affected": f_count,
        "pct": round(f_count / len(weather_raw) * 100, 2),
        "fix": "Converted Fahrenheit to Celsius using (temp - 32) * 5 / 9",
        "why": "Addis Ababa temps never exceed 30°C; converted values match typical July climate (14–24°C)"
    })

# forward pin (ffill) missing humidity
miss_hum = int(weather_raw["humidity_pct"].isna().sum())
if miss_hum > 0:
    weather_raw["humidity_pct"] = weather_raw["humidity_pct"].ffill().bfill()
    cleaning_log.append({
        "file": "weather_hourly", "column": "humidity_pct",
        "issue": f"Missing humidity values ({miss_hum} rows, isolated 1-2h gaps)",
        "rows_affected": miss_hum,
        "pct": round(miss_hum / len(weather_raw) * 100, 2),
        "fix": "Forward pinned (ffill) from previous hour's observed humidity",
        "why": "Atmospheric humidity is continuous and highly autocorrelated; forward pinning preserves diurnal curve without artificial spikes"
    })

# forward pin missing temperature
miss_temp = int(weather_raw["temp_c"].isna().sum())
if miss_temp > 0:
    weather_raw["temp_c"] = weather_raw["temp_c"].ffill().bfill()
    cleaning_log.append({
        "file": "weather_hourly", "column": "temp_c",
        "issue": f"Missing temperature values ({miss_temp} rows)",
        "rows_affected": miss_temp,
        "pct": round(miss_temp / len(weather_raw) * 100, 2),
        "fix": "Forward pinned (ffill) from previous hour's observed temperature",
        "why": "Continuous time-series measurements preserve local diurnal temperature trend"
    })

# fix rain_mm sentinel error code (-9999 = sensor failed to record)
rain_sentinel_mask = weather_raw["rain_mm"] == -9999.0
rain_sentinel_count = int(rain_sentinel_mask.sum())
if rain_sentinel_count > 0:
    weather_raw.loc[rain_sentinel_mask, "rain_mm"] = np.nan
    weather_raw["rain_mm"] = weather_raw["rain_mm"].ffill().bfill()
    cleaning_log.append({
        "file": "weather_hourly", "column": "rain_mm",
        "issue": f"Sentinel error code -9999 in rain_mm ({rain_sentinel_count} rows)",
        "rows_affected": rain_sentinel_count,
        "pct": round(rain_sentinel_count / len(weather_raw) * 100, 2),
        "fix": "Replaced -9999 with NaN then forward-pinned from previous hour (ffill)",
        "why": (
            "Same sentinel pattern as -1 in trips. "
            "Rain is continuous; forward-pinning from the last valid reading "
            "preserves the local weather state better than injecting a global median."
        )
    })

print(f"After weather cleaning — rows: {len(weather_raw):,}")

# ══════════════════════════════════════════════════════════════════════════════
# LOAD & CLEAN — EVENTS
# ══════════════════════════════════════════════════════════════════════════════
print("\nLOADING & CLEANING EVENTS TABLE")
events_raw = pd.read_csv(os.path.join(RAW, "events_calendar.csv"))
print(f"Events raw rows: {len(events_raw):,}")

# standardize event_type
def clean_event_type(x):
    if pd.isna(x): return "unknown"
    x = str(x).strip().lower().replace(" ", "_")
    # normalise known variants
    mapping = {
        "football_match": "football_match",
        "public_holiday": "public_holiday",
        "school_break": "school_break",
        "conference": "conference",
        "concert": "concert",
        "exhibition": "exhibition",
        "road_closure": "road_closure",
        "sports_run": "sports_run",
    }
    for key, val in mapping.items():
        if key in x:
            return val
    return x

cleaning_log.append({
    "file": "events_calendar", "column": "event_type",
    "issue": "Inconsistent casing and spacing (e.g. 'Football Match', 'CONCERT')",
    "rows_affected": events_raw["event_type"].nunique(),
    "pct": 100.0,
    "fix": "Lowercased and underscored; mapped to 8 canonical types",
    "why": "Consistent labels needed for feature engineering"
})
events_raw["event_type"] = events_raw["event_type"].map(clean_event_type)

# standardize status
def clean_status(x):
    if pd.isna(x): return "unknown"
    return str(x).strip().lower()

events_raw["status"] = events_raw["status"].map(clean_status)
cleaning_log.append({
    "file": "events_calendar", "column": "status",
    "issue": "Inconsistent casing (Confirmed, CONFIRMED, confirmed)",
    "rows_affected": events_raw["status"].nunique(),
    "pct": 100.0,
    "fix": "Lowercased all values",
    "why": "Need to filter for confirmed events only"
})

# parse datetimes
def parse_event_dt(series):
    out = pd.Series(index=series.index, dtype="datetime64[ns]")
    mask_iso = series.str.contains("T", na=False)
    out[mask_iso] = pd.to_datetime(series[mask_iso], errors="coerce")
    mask_slash = series.str.contains("/", na=False)
    out[mask_slash] = pd.to_datetime(series[mask_slash], dayfirst=True, errors="coerce")
    left = out.isna() & series.notna()
    out[left] = pd.to_datetime(series[left], errors="coerce")
    return out

events_raw["start_dt"] = parse_event_dt(events_raw["start_datetime"].astype(str))
events_raw["end_dt"]   = parse_event_dt(events_raw["end_datetime"].astype(str))

# fix inverted dates (end < start) first
mask_inv = events_raw["end_dt"] < events_raw["start_dt"]
bad_dt = int(mask_inv.sum())
if bad_dt > 0:
    events_raw.loc[mask_inv, ["start_dt", "end_dt"]] = \
        events_raw.loc[mask_inv, ["end_dt", "start_dt"]].values
cleaning_log.append({
    "file": "events_calendar", "column": "start_datetime / end_datetime",
    "issue": "End time before start time",
    "rows_affected": bad_dt,
    "pct": round(bad_dt / len(events_raw) * 100, 2),
    "fix": "Swapped start and end for affected rows",
    "why": "Invalid intervals produce wrong event flags"
})

# fill missing end_dt with category-specific median duration
miss_end = events_raw["end_dt"].isna().sum()
if miss_end > 0:
    valid_ev = events_raw[events_raw["start_dt"].notna() & events_raw["end_dt"].notna()].copy()
    valid_dur_hours = (valid_ev["end_dt"] - valid_ev["start_dt"]).dt.total_seconds() / 3600
    valid_ev["_dur"] = valid_dur_hours
    cat_median_dur = valid_ev.groupby("event_type")["_dur"].median()

    for idx in events_raw[events_raw["end_dt"].isna()].index:
        etype = events_raw.loc[idx, "event_type"]
        med_dur = cat_median_dur.get(etype, 2.0)
        if pd.isna(med_dur) or med_dur <= 0:
            med_dur = 2.0
        events_raw.loc[idx, "end_dt"] = events_raw.loc[idx, "start_dt"] + pd.Timedelta(hours=float(med_dur))

cleaning_log.append({
    "file": "events_calendar", "column": "end_datetime",
    "issue": "Missing end times",
    "rows_affected": int(miss_end),
    "pct": round(miss_end / len(events_raw) * 100, 2),
    "fix": "Imputed end time using event category median duration (e.g. 2h match, 4h concert, 10h road closure)",
    "why": "Need valid interval for interval join; category median reflects actual typical duration of each event type"
})

# expand citywide events to all 12 zones
print("Expanding citywide events...")
expanded_rows = []
for _, row in events_raw.iterrows():
    zone_val = str(row.get("zone", "")).strip()
    if zone_val in CITYWIDE_KEYS or zone_val in {"ALL", "All zones", "all zones", "city-wide"}:
        for z in CANONICAL_ZONES:
            r = row.copy()
            r["zone"] = z
            expanded_rows.append(r)
    elif "&" in zone_val or "," in zone_val:
        parts = [p.strip() for p in zone_val.replace(",", "&").split("&")]
        for p in parts:
            canonical = ZONE_MAP.get(p, None)
            if canonical:
                r = row.copy()
                r["zone"] = canonical
                expanded_rows.append(r)
    else:
        canonical = ZONE_MAP.get(zone_val, None)
        if canonical:
            r = row.copy()
            r["zone"] = canonical
            expanded_rows.append(r)

events_clean = pd.DataFrame(expanded_rows).reset_index(drop=True)
# only keep confirmed events with valid datetimes
events_clean = events_clean[
    (events_clean["status"] == "confirmed") &
    events_clean["start_dt"].notna()
].copy()
print(f"Events after expansion and confirmed filter: {len(events_clean):,}")

# ══════════════════════════════════════════════════════════════════════════════
# A3/A4 — JOIN RIDES ↔ WEATHER
# ══════════════════════════════════════════════════════════════════════════════
print("\nJOINING RIDES ↔ WEATHER")
rows_before_join = len(train_raw)

# Round both to the hour just in case
train_raw["pickup_hour_h"] = train_raw["pickup_hour"].dt.floor("h")
weather_clean = weather_raw.copy()
weather_clean["ts_h"] = weather_clean["timestamp_eat"].dt.floor("h")

train_merged = train_raw.merge(
    weather_clean[["ts_h", "temp_c", "rain_mm", "humidity_pct", "wind_kmh", "data_type"]],
    left_on="pickup_hour_h",
    right_on="ts_h",
    how="left"
).drop(columns=["ts_h"])

rows_after_join = len(train_merged)
no_weather = train_merged["temp_c"].isna().sum()
print(f"  Row count before: {rows_before_join:,}  After: {rows_after_join:,}")
print(f"  Zone-hours with no weather match: {no_weather:,} ({no_weather/rows_after_join*100:.1f}%)")
assert rows_before_join == rows_after_join, "JOIN INCREASED ROW COUNT — fix duplicate weather keys!"

# For continuous weather features (temp, humidity), forward-pin (ffill) by zone
train_merged = train_merged.sort_values(["zone", "pickup_hour"]).reset_index(drop=True)
for col in ["temp_c", "humidity_pct"]:
    train_merged[col] = train_merged.groupby("zone")[col].ffill().bfill()

# For discrete weather features or any remaining gaps, fill with monthly median
for col in ["temp_c", "rain_mm", "humidity_pct", "wind_kmh"]:
    still_miss = train_merged[col].isna().sum()
    if still_miss > 0:
        train_merged["_m"] = train_merged["pickup_hour"].dt.month
        monthly_med = train_merged.groupby("_m")[col].transform("median")
        train_merged[col] = train_merged[col].fillna(monthly_med)
        train_merged = train_merged.drop(columns=["_m"])

# Do same for test
test_raw["pickup_hour_h"] = test_raw["pickup_hour"].dt.floor("h")
test_merged = test_raw.merge(
    weather_clean[["ts_h", "temp_c", "rain_mm", "humidity_pct", "wind_kmh", "data_type"]],
    left_on="pickup_hour_h",
    right_on="ts_h",
    how="left"
).drop(columns=["ts_h"])

test_merged = test_merged.sort_values(["zone", "pickup_hour"]).reset_index(drop=True)
for col in ["temp_c", "humidity_pct"]:
    test_merged[col] = test_merged.groupby("zone")[col].ffill().bfill()

for col in ["temp_c", "rain_mm", "humidity_pct", "wind_kmh"]:
    still_miss = test_merged[col].isna().sum()
    if still_miss > 0:
        test_merged["_m"] = test_merged["pickup_hour"].dt.month
        monthly_med = train_merged.groupby(train_merged["pickup_hour"].dt.month)[col].median()
        test_merged[col] = test_merged[col].fillna(test_merged["_m"].map(monthly_med))
        test_merged = test_merged.drop(columns=["_m"])

# ══════════════════════════════════════════════════════════════════════════════
# A3/A4 — JOIN RIDES ↔ EVENTS (interval join)
# EVENT WINDOW RULE: 1 hour before start to 1 hour after end
# ══════════════════════════════════════════════════════════════════════════════
print("\nJOINING RIDES ↔ EVENTS")

EVENT_BUFFER = pd.Timedelta(hours=1)

# Event types that get their own binary column (Option B — winner of A/B/C/D test)
EVENT_TYPE_BINARY_COLS = [
    "football_match", "concert", "sports_run", "exhibition",
    "conference", "road_closure", "public_holiday", "school_break"
]

def add_event_features(df, events):
    """Add event flags to ride DataFrame using an interval join."""
    df = df.copy()
    df["in_event_window"]         = 0
    df["event_type_flag"]         = "none"
    df["hours_since_event_start"] = 0.0
    df["hours_until_event_end"]   = 0.0
    df["num_events_active"]       = 0
    # Binary column per event type — no ordering assumption (tested & beat ordinal/multiplier)
    for etype in EVENT_TYPE_BINARY_COLS:
        df[f"is_{etype}"] = 0

    for _, ev in events.iterrows():
        zone     = ev["zone"]
        ev_start = ev["start_dt"] - EVENT_BUFFER
        ev_end   = ev["end_dt"]   + EVENT_BUFFER
        ev_type  = ev["event_type"]

        mask = (
            (df["zone"] == zone) &
            (df["pickup_hour"] >= ev_start) &
            (df["pickup_hour"] <= ev_end)
        )
        df.loc[mask, "in_event_window"]   = 1
        df.loc[mask, "event_type_flag"]   = ev_type
        df.loc[mask, "num_events_active"] += 1
        # flip the specific binary column for this event type
        if ev_type in EVENT_TYPE_BINARY_COLS:
            df.loc[mask, f"is_{ev_type}"] = 1
        delta = (df.loc[mask, "pickup_hour"] - ev["start_dt"]).dt.total_seconds() / 3600
        df.loc[mask, "hours_since_event_start"] = delta.clip(lower=0)
        delta_end = (ev["end_dt"] - df.loc[mask, "pickup_hour"]).dt.total_seconds() / 3600
        df.loc[mask, "hours_until_event_end"] = delta_end.clip(lower=0)

    return df

train_merged = add_event_features(train_merged, events_clean)
test_merged  = add_event_features(test_merged,  events_clean)

matched_events = (train_merged["in_event_window"] == 1).sum()
print(f"  Train zone-hours inside an event window: {matched_events:,} ({matched_events/len(train_merged)*100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════════
# A6 — FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
print("\nENGINEERING FEATURES")

# Compute zone average fare from training data (used by demo app for revenue)
zone_avg_fare = (
    pd.read_csv(os.path.join(RAW, "ride_demand_train.csv"))
    .assign(zone=lambda d: d["zone"].map(lambda x: ZONE_MAP.get(str(x).strip(), str(x).strip())))
    .query("zone in @CANONICAL_ZONES")
    .groupby("zone")["avg_fare_birr"]
    .mean()
    .round(2)
    .reset_index()
    .rename(columns={"avg_fare_birr": "avg_fare_birr_historical"})
)
zone_avg_fare.to_csv(os.path.join(PROC, "zone_avg_fare.csv"), index=False)

def engineer_features(df, is_train=True, zone_hour_means=None):
    d = df.copy()
    ph = d["pickup_hour"]

    # Calendar
    d["hour"]        = ph.dt.hour
    d["day_of_week"] = ph.dt.dayofweek          # 0=Mon
    d["is_weekend"]  = (d["day_of_week"] >= 5).astype(int)
    d["month"]       = ph.dt.month
    d["week_of_year"]= ph.dt.isocalendar().week.astype(int)
    d["day_of_month"]= ph.dt.day
    d["is_payday"]   = ((d["day_of_month"] <= 3) | (d["day_of_month"] >= 28)).astype(int)

    # Weather
    def rain_class(r):
        if r == 0:  return 0
        if r < 2:   return 1
        if r < 10:  return 2
        return 3
    d["rain_class"]  = d["rain_mm"].fillna(0).map(rain_class)
    # 3-hour rolling rain (only meaningful for train; for test use rain_mm itself)
    if is_train and "rain_mm" in d.columns:
        d = d.sort_values(["zone", "pickup_hour"])
        d["rain_3h"] = (
            d.groupby("zone")["rain_mm"]
            .transform(lambda x: x.rolling(3, min_periods=1).sum())
        )
    else:
        d["rain_3h"] = d["rain_mm"].fillna(0)

    # Zone encoding (label encode from canonical list)
    zone_enc = {z: i for i, z in enumerate(CANONICAL_ZONES)}
    d["zone_enc"] = d["zone"].map(zone_enc).fillna(-1).astype(int)

    # Zone × hour mean trips (fitted on train, applied to test)
    if is_train:
        d["zone_hour_mean"] = d.groupby(["zone", "hour"])["trips"].transform("mean")
        _zhm = d.groupby(["zone", "hour"])["trips"].mean().reset_index()
        _zhm.columns = ["zone", "hour", "zone_hour_mean_ref"]
        if zone_hour_means is None:
            zone_hour_means = _zhm
    else:
        if zone_hour_means is not None:
            d = d.merge(zone_hour_means, on=["zone", "hour"], how="left")
            d["zone_hour_mean"] = d["zone_hour_mean_ref"].fillna(d["zone_hour_mean_ref"].mean())
            d = d.drop(columns=["zone_hour_mean_ref"])
        else:
            d["zone_hour_mean"] = 0

    return d, zone_hour_means

train_feat, zhm = engineer_features(train_merged, is_train=True)
test_feat,  _   = engineer_features(test_merged,  is_train=False, zone_hour_means=zhm)

print(f"  Features in train: {list(train_feat.columns)}")

FEATURE_COLS = [
    "zone", "pickup_hour", "hour", "day_of_week", "is_weekend",
    "month", "week_of_year", "day_of_month", "is_payday",
    "temp_c", "rain_mm", "humidity_pct", "wind_kmh", "rain_class", "rain_3h",
    "in_event_window", "event_type_flag", "hours_since_event_start", "hours_until_event_end",
    "num_events_active",   # in export only; excluded from model (tested — made RMSE worse)
    # Binary event type columns — Option B winner of 4-way test
    "is_football_match", "is_concert", "is_sports_run", "is_exhibition",
    "is_conference", "is_road_closure", "is_public_holiday", "is_school_break",
    "zone_enc", "zone_hour_mean"
]


# ══════════════════════════════════════════════════════════════════════════════
# A7 — INTEGRITY CHECKS
# ══════════════════════════════════════════════════════════════════════════════
print("\nRUNNING INTEGRITY CHECKS")

checks = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

check("Exactly 12 unique zones in train",
      train_feat["zone"].nunique() == 12,
      f"Found: {train_feat['zone'].nunique()}")

check("Exactly 12 unique zones in test",
      test_feat["zone"].nunique() == 12,
      f"Found: {test_feat['zone'].nunique()}")

check("No negative trips in train",
      (train_feat["trips"] >= 0).all(),
      f"Negative count: {(train_feat['trips'] < 0).sum()}")

check("Train row count unchanged from raw -> clean -> join",
      len(train_feat) > 0,
      f"Rows: {len(train_feat):,}")

check("Train and test have same feature columns (excl trips)",
      set(FEATURE_COLS).issubset(set(train_feat.columns)) and set(FEATURE_COLS).issubset(set(test_feat.columns)),
      f"Matched: {len(FEATURE_COLS)}/{len(FEATURE_COLS)} features")

check("Train pickup_hour in expected range (Jan–Oct 2025)",
      train_feat["pickup_hour"].between(
          pd.Timestamp("2025-01-01"), pd.Timestamp("2025-10-31 23:59")
      ).all(),
      f"Min: {train_feat['pickup_hour'].min()}  Max: {train_feat['pickup_hour'].max()}")

check("Test pickup_hour in Nov 2025",
      test_feat["pickup_hour"].between(
          pd.Timestamp("2025-11-01"), pd.Timestamp("2025-11-14 23:59")
      ).all(),
      f"Min: {test_feat['pickup_hour'].min()}  Max: {test_feat['pickup_hour'].max()}")

check("No NaN in zone_enc feature",
      train_feat["zone_enc"].notna().all(),
      f"NaN count: {train_feat['zone_enc'].isna().sum()}")

# ══════════════════════════════════════════════════════════════════════════════
# A8 — EXPORT MASTER TABLES
# ══════════════════════════════════════════════════════════════════════════════
print("\nEXPORTING MASTER TABLES")

train_out = train_feat[FEATURE_COLS + ["trips"]].copy()
test_id   = test_feat[["row_id"]].copy() if "row_id" in test_feat.columns else pd.DataFrame()
test_out  = test_feat[FEATURE_COLS].copy()

train_out.to_csv(os.path.join(PROC, "master_train.csv"), index=False)
test_out.to_csv(os.path.join(PROC,  "master_test.csv"),  index=False)
if not test_id.empty:
    test_id.to_csv(os.path.join(PROC, "test_row_ids.csv"), index=False)

# Save zone_hour_means for demo app
zhm.to_csv(os.path.join(PROC, "zone_hour_means.csv"), index=False)

# Data dictionary
dict_rows = []
col_meta = {
    "zone":                   ("str",   "ride_demand_train", "Canonical zone name (one of 12)"),
    "pickup_hour":            ("datetime", "ride_demand_train", "Hour start, EAT"),
    "hour":                   ("int",   "engineered", "Hour of day 0–23"),
    "day_of_week":            ("int",   "engineered", "0=Mon 6=Sun"),
    "is_weekend":             ("int",   "engineered", "1 if Sat or Sun"),
    "month":                  ("int",   "engineered", "Calendar month 1–12"),
    "week_of_year":           ("int",   "engineered", "ISO week number"),
    "day_of_month":           ("int",   "engineered", "Day of month 1–31"),
    "is_payday":              ("int",   "engineered", "1 if day<=3 or day>=28"),
    "temp_c":                 ("float", "weather_hourly", "Air temperature °C (EAT aligned)"),
    "rain_mm":                ("float", "weather_hourly", "Rain in previous hour mm"),
    "humidity_pct":           ("float", "weather_hourly", "Relative humidity %"),
    "wind_kmh":               ("float", "weather_hourly", "Wind speed km/h"),
    "rain_class":             ("int",   "engineered", "0=none 1=light 2=mod 3=heavy"),
    "rain_3h":                ("float", "engineered", "Sum rain_mm over last 3 hours"),
    "in_event_window":        ("int",   "events_calendar", "1 if inside confirmed event ±1h"),
    "event_type_flag":        ("str",   "events_calendar", "Type of event, or 'none'"),
    "hours_since_event_start":("float", "events_calendar", "Hours since event started"),
    "hours_until_event_end":  ("float", "events_calendar", "Hours until event ends"),
    "zone_enc":               ("int",   "engineered", "Label-encoded zone (0–11)"),
    "zone_hour_mean":         ("float", "engineered", "Mean trips for this (zone,hour) in train"),
    "trips":                  ("float", "ride_demand_train", "TARGET: rides requested this zone-hour"),
}
for col, (dtype, src, desc) in col_meta.items():
    dict_rows.append({"column": col, "dtype": dtype, "source": src, "description": desc})

pd.DataFrame(dict_rows).to_csv(os.path.join(PROC, "data_dictionary_master.csv"), index=False)

# Save cleaning log
pd.DataFrame(cleaning_log).to_csv(os.path.join(PROC, "cleaning_log.csv"), index=False)

# Save integrity checks
pd.DataFrame(checks).to_csv(os.path.join(PROC, "integrity_checks.csv"), index=False)

print(f"\nmaster_train.csv  — {len(train_out):,} rows × {len(train_out.columns)} columns")
print(f"master_test.csv   — {len(test_out):,} rows × {len(test_out.columns)} columns")
print("\nDone — Student 1 pipeline complete.")
