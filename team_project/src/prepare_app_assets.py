"""
Prepare app/assets/ — copy lookup tables the demo app needs.
Run once after modeling.py completes.
"""
import pandas as pd
import numpy as np
import shutil, os

PROC   = os.path.join("data","processed")
RAW    = os.path.join("data","raw")
ASSETS = os.path.join("app","assets")
os.makedirs(ASSETS, exist_ok=True)

# 1) Copy model files
for f in ["final_model.joblib","feature_list.joblib"]:
    src = os.path.join("models", f)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(ASSETS, f))
        print(f"Copied {f}")

# 2) Copy zone_avg_fare, zone_hour_means, zone_types
for f in ["zone_avg_fare.csv", "zone_types.csv"]:
    src = os.path.join(PROC, f)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(ASSETS, f))
        print(f"Copied {f}")

zhm_df = pd.read_csv(os.path.join(PROC, "zone_hour_means.csv"))
if "zone_hour_mean_ref" in zhm_df.columns:
    zhm_df = zhm_df.rename(columns={"zone_hour_mean_ref": "trips"})
zhm_df.to_csv(os.path.join(ASSETS, "zone_hour_means.csv"), index=False)
print("Copied zone_hour_means.csv")

# 3) Build weather_nov.csv — the November forecast rows (already EAT-aligned)
weather = pd.read_csv(os.path.join(RAW,"weather_hourly.csv"))
# parse timestamps
import warnings; warnings.filterwarnings("ignore")

def parse_ts(series):
    out = pd.Series(index=series.index, dtype="datetime64[ns]")
    mask_z = series.str.endswith("Z", na=False)
    if mask_z.any():
        out[mask_z] = (pd.to_datetime(series[mask_z], utc=True)
                       .dt.tz_convert("Africa/Addis_Ababa").dt.tz_localize(None))
    mask_dd = series.str.contains("/", na=False)
    if mask_dd.any():
        out[mask_dd] = pd.to_datetime(series[mask_dd], dayfirst=True) + pd.Timedelta(hours=3)
    return out

weather["timestamp_eat"] = parse_ts(weather["timestamp"].astype(str))
nov_weather = weather[
    weather["timestamp_eat"].between("2025-11-01","2025-11-14 23:59")
].copy()
nov_weather[["timestamp_eat","temp_c","rain_mm","humidity_pct","wind_kmh","data_type"]].to_csv(
    os.path.join(ASSETS,"weather_nov.csv"), index=False)
print(f"weather_nov.csv — {len(nov_weather):,} rows")

# 4) Build events_nov.csv — cleaned events relevant to November
events = pd.read_csv(os.path.join(RAW,"events_calendar.csv"))

ZONE_MAP = {
    "megenagna":"Megenagna","MEGENAGNA":"Megenagna","Megenagna":"Megenagna","Megenaga":"Megenagna",
    "piassa":"Piassa","PIASSA":"Piassa","Piassa":"Piassa","Piazza":"Piassa","piazza":"Piassa",
    "CMC":"CMC","cmc":"CMC","C.M.C":"CMC","c.m.c":"CMC",
    "Kazanchis":"Kazanchis","KAZANCHIS":"Kazanchis","kazanchis":"Kazanchis","Kazanches":"Kazanchis",
    "Kazanchis (Kirkos)":"Kazanchis",
    "Gerji":"Gerji","GERJI":"Gerji","gerji":"Gerji",
    "Lideta":"Lideta","LIDETA":"Lideta","lideta":"Lideta",
    "Bole":"Bole","BOLE":"Bole","bole":"Bole","Bole Rd":"Bole","Bole (Bole subcity)":"Bole",
    "Arat Kilo":"Arat Kilo","ARAT KILO":"Arat Kilo","arat kilo":"Arat Kilo","Arat  Kilo":"Arat Kilo",
    "Merkato":"Merkato","MERKATO":"Merkato","merkato":"Merkato","Mercato":"Merkato","mercato":"Merkato",
    "Kolfe":"Kolfe","KOLFE":"Kolfe","kolfe":"Kolfe","Kolfe Keranio":"Kolfe",
    "Sarbet":"Sarbet","SARBET":"Sarbet","sarbet":"Sarbet",
    "Ayat":"Ayat","AYAT":"Ayat","ayat":"Ayat",
}
CANONICAL_ZONES = sorted(set(ZONE_MAP.values()))
CITYWIDE = {"Citywide","citywide","ALL","All","All zones","all zones","city-wide","City-Wide"}

def parse_event_dt(series):
    out = pd.Series(index=series.index, dtype="datetime64[ns]")
    mask_iso = series.str.contains("T", na=False)
    if mask_iso.any():
        out[mask_iso] = pd.to_datetime(series[mask_iso], errors="coerce")
    mask_slash = series.str.contains("/", na=False)
    if mask_slash.any():
        out[mask_slash] = pd.to_datetime(series[mask_slash], dayfirst=True, errors="coerce")
    left = out.isna() & series.notna()
    if left.any():
        out[left] = pd.to_datetime(series[left], errors="coerce")
    return out

events["start_dt"] = parse_event_dt(events["start_datetime"].astype(str))
events["end_dt"]   = parse_event_dt(events["end_datetime"].astype(str))
events.loc[events["end_dt"].isna(), "end_dt"] = \
    events.loc[events["end_dt"].isna(), "start_dt"] + pd.Timedelta(hours=2)
events["status"]   = events["status"].astype(str).str.strip().str.lower()
events["event_type"] = events["event_type"].astype(str).str.strip().str.lower().str.replace(" ","_")

# expand to zone level
expanded = []
for _, row in events.iterrows():
    zone_val = str(row.get("zone","")).strip()
    if zone_val in CITYWIDE:
        for z in CANONICAL_ZONES:
            r = row.copy(); r["zone"] = z; expanded.append(r)
    elif "&" in zone_val or "," in zone_val:
        parts = [p.strip() for p in zone_val.replace(",","&").split("&")]
        for p in parts:
            canon = ZONE_MAP.get(p)
            if canon: r = row.copy(); r["zone"] = canon; expanded.append(r)
    else:
        canon = ZONE_MAP.get(zone_val)
        if canon: r = row.copy(); r["zone"] = canon; expanded.append(r)

ev_df = pd.DataFrame(expanded)
ev_df = ev_df[ev_df["status"]=="confirmed"]
# filter to events that overlap November 1–14
nov_start = pd.Timestamp("2025-11-01")
nov_end   = pd.Timestamp("2025-11-14 23:59")
ev_nov = ev_df[
    (ev_df["end_dt"] >= nov_start) & (ev_df["start_dt"] <= nov_end)
][["zone","event_type","start_dt","end_dt","status"]].copy()

ev_nov.to_csv(os.path.join(ASSETS,"events_nov.csv"), index=False)
print(f"events_nov.csv — {len(ev_nov):,} rows")
print("\nApp assets ready.")
