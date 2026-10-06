import sys, os, joblib
import pandas as pd

# 1. Test all imports
for pkg in ["streamlit","joblib","pandas","numpy","matplotlib"]:
    try:
        __import__(pkg)
        print("OK  " + pkg)
    except Exception as e:
        print("ERR " + pkg + " : " + str(e))

# 2. Check asset files exist
assets = "app/assets"
required = [
    "final_model.joblib","feature_list.joblib",
    "weather_nov.csv","events_nov.csv",
    "zone_avg_fare.csv","zone_hour_means.csv","zone_types.csv",
]
for f in required:
    path = os.path.join(assets, f)
    ok = os.path.exists(path) and os.path.getsize(path) > 0
    print(("OK  " if ok else "MISSING ") + path)

# 3. Test model prediction
try:
    model = joblib.load("app/assets/final_model.joblib")
    feat_cols = joblib.load("app/assets/feature_list.joblib")
    dummy = pd.DataFrame([{c: 0 for c in feat_cols}])
    pred = model.predict(dummy)
    print("OK  model prediction: " + str(round(pred[0], 1)))
except Exception as e:
    print("ERR model: " + str(e))

# 4. Test CSV loads
for fname in ["weather_nov.csv","events_nov.csv","zone_avg_fare.csv","zone_hour_means.csv"]:
    try:
        df = pd.read_csv(os.path.join(assets, fname))
        print("OK  " + fname + " rows=" + str(len(df)))
    except Exception as e:
        print("ERR " + fname + ": " + str(e))

# 5. Simulate exactly what app.py does for one forecast
try:
    import numpy as np
    from datetime import date

    model = joblib.load("app/assets/final_model.joblib")
    feat_cols = joblib.load("app/assets/feature_list.joblib")
    weather_nov = pd.read_csv("app/assets/weather_nov.csv", parse_dates=["timestamp_eat"])
    events_nov  = pd.read_csv("app/assets/events_nov.csv",  parse_dates=["start_dt","end_dt"])
    fare_df     = pd.read_csv("app/assets/zone_avg_fare.csv")
    zhm         = pd.read_csv("app/assets/zone_hour_means.csv")
    fare_map    = dict(zip(fare_df["zone"], fare_df["avg_fare_birr_historical"]))

    CANONICAL_ZONES = sorted(["Arat Kilo","Ayat","Bole","CMC","Gerji","Kazanchis",
                               "Kolfe","Lideta","Megenagna","Merkato","Piassa","Sarbet"])
    ZONE_ENC = {z: i for i, z in enumerate(CANONICAL_ZONES)}
    EVENT_BUFFER = pd.Timedelta(hours=1)

    zone = "Bole"
    chosen_date = date(2025, 11, 3)
    rows = []
    dt_base = pd.Timestamp(chosen_date)
    for h in range(24):
        dt = dt_base + pd.Timedelta(hours=h)
        w_row = weather_nov[weather_nov["timestamp_eat"] == dt]
        temp_c   = float(w_row["temp_c"].iloc[0])   if len(w_row) else 22.0
        rain_mm  = float(w_row["rain_mm"].iloc[0])  if len(w_row) else 0.0
        humidity = float(w_row["humidity_pct"].iloc[0]) if len(w_row) else 60.0
        wind_kmh = float(w_row["wind_kmh"].iloc[0]) if len(w_row) else 10.0
        rain_class = 0 if rain_mm == 0 else 1 if rain_mm < 2 else 2 if rain_mm < 10 else 3

        ev_mask = (
            (events_nov["zone"] == zone) &
            (events_nov["start_dt"] - EVENT_BUFFER <= dt) &
            (events_nov["end_dt"]   + EVENT_BUFFER >= dt)
        )
        ev_rows = events_nov[ev_mask]
        in_event = 1 if len(ev_rows) > 0 else 0

        val_col = "trips" if "trips" in zhm.columns else [c for c in zhm.columns if c not in ["zone", "hour"]][0]
        zhm_val = zhm[(zhm["zone"] == zone) & (zhm["hour"] == h)]
        zhm_val = float(zhm_val[val_col].iloc[0]) if len(zhm_val) else 20.0

        rows.append({
            "hour": h, "day_of_week": dt.dayofweek,
            "is_weekend": int(dt.dayofweek >= 5),
            "month": dt.month,
            "week_of_year": dt.isocalendar().week,
            "day_of_month": dt.day,
            "is_payday": int(dt.day <= 3 or dt.day >= 28),
            "temp_c": temp_c, "rain_mm": rain_mm,
            "humidity_pct": humidity, "wind_kmh": wind_kmh,
            "rain_class": rain_class, "rain_3h": rain_mm,
            "in_event_window": in_event,
            "hours_since_event_start": 0.0,
            "hours_until_event_end":   0.0,
            "zone_enc": ZONE_ENC.get(zone, 0),
            "zone_hour_mean": zhm_val,
        })

    feat_df = pd.DataFrame(rows)
    X = feat_df[feat_cols]
    preds = np.clip(model.predict(X), 0, None).round(0).astype(int)
    print("OK  Full prediction simulation: peak=" + str(preds.max()) + " at hour " + str(int(preds.argmax())))
    print("OK  Revenue est: " + str(int(preds.sum() * fare_map.get(zone, 40))) + " Birr total")

except Exception as e:
    import traceback
    print("ERR simulation: " + str(e))
    traceback.print_exc()
