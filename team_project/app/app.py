"""
Student 5 — Demo App (Streamlit)
Deliverable E: Working forecast demo for Addis Ride Demand

Run with:  streamlit run app/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import joblib, os, warnings
from datetime import date, timedelta
warnings.filterwarnings("ignore")

# ── config ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Addis Ride Forecast",
    page_icon="🚖",
    layout="wide",
)

CANONICAL_ZONES = [
    "Arat Kilo","Ayat","Bole","CMC","Gerji","Kazanchis",
    "Kolfe","Lideta","Megenagna","Merkato","Piassa","Sarbet",
]
NOV_START = date(2025, 11, 1)
NOV_END   = date(2025, 11, 14)

# ── load assets ───────────────────────────────────────────────────────────────
ASSETS = os.path.join(os.path.dirname(__file__), "assets")

@st.cache_resource
def load_model():
    model_path = os.path.join(ASSETS, "final_model.joblib")
    feat_path  = os.path.join(ASSETS, "feature_list.joblib")
    if os.path.exists(model_path) and os.path.exists(feat_path):
        return joblib.load(model_path), joblib.load(feat_path)
    return None, None

@st.cache_data
def load_lookups():
    # Weather for Nov
    wdf = pd.read_csv(os.path.join(ASSETS, "weather_nov.csv"), parse_dates=["timestamp_eat"])
    # Events for Nov
    edf = pd.read_csv(os.path.join(ASSETS, "events_nov.csv"), parse_dates=["start_dt","end_dt"])
    # Zone avg fare (for revenue estimate)
    fare = pd.read_csv(os.path.join(ASSETS, "zone_avg_fare.csv"))
    fare_map = dict(zip(fare["zone"], fare["avg_fare_birr_historical"]))
    # Zone hour means
    zhm = pd.read_csv(os.path.join(ASSETS, "zone_hour_means.csv"))
    # rename any variant column name to 'trips'
    for col in ["zone_hour_mean_ref", "zone_hour_mean", "mean_trips"]:
        if col in zhm.columns:
            zhm = zhm.rename(columns={col: "trips"})
    # Zone types
    zt  = pd.read_csv(os.path.join(ASSETS, "zone_types.csv"))
    return wdf, edf, fare_map, zhm, zt

model, feature_cols = load_model()
weather_nov, events_nov, fare_map, zone_hour_means, zone_types = load_lookups()

ZONE_ENC = {z: i for i, z in enumerate(CANONICAL_ZONES)}

# ── helper: build features for 24 hours of a given zone+date ──────────────────
EVENT_BUFFER = pd.Timedelta(hours=1)

def build_features(zone: str, chosen_date: date) -> pd.DataFrame:
    rows = []
    dt_base = pd.Timestamp(chosen_date)
    for h in range(24):
        dt = dt_base + pd.Timedelta(hours=h)

        # weather lookup
        w_row = weather_nov[weather_nov["timestamp_eat"] == dt]
        temp_c     = float(w_row["temp_c"].iloc[0])     if len(w_row) else 22.0
        rain_mm    = float(w_row["rain_mm"].iloc[0])    if len(w_row) else 0.0
        humidity   = float(w_row["humidity_pct"].iloc[0]) if len(w_row) else 60.0
        wind_kmh   = float(w_row["wind_kmh"].iloc[0])   if len(w_row) else 10.0

        # rain features
        rain_class = (0 if rain_mm == 0 else 1 if rain_mm < 2 else 2 if rain_mm < 10 else 3)
        rain_3h    = rain_mm  # simplified: single-hour value

        # event lookup (interval join with buffer)
        ev_mask = (
            (events_nov["zone"] == zone) &
            (events_nov["start_dt"] - EVENT_BUFFER <= dt) &
            (events_nov["end_dt"]   + EVENT_BUFFER >= dt)
        )
        ev_rows = events_nov[ev_mask]
        in_event = 1 if len(ev_rows) > 0 else 0
        ev_type  = ev_rows["event_type"].iloc[0] if in_event else "none"
        hse      = float((dt - ev_rows["start_dt"].iloc[0]).total_seconds() / 3600) if in_event else 0.0
        hue      = float((ev_rows["end_dt"].iloc[0] - dt).total_seconds() / 3600)   if in_event else 0.0

        # zone hour mean — use whatever numeric column holds the value
        zhm_row = zone_hour_means[
            (zone_hour_means["zone"] == zone) &
            (zone_hour_means["hour"] == h)
        ]
        val_col = "trips" if "trips" in zone_hour_means.columns else zone_hour_means.select_dtypes("number").columns[-1]
        zhm_val = float(zhm_row[val_col].iloc[0]) if len(zhm_row) else 20.0

        rows.append({
            "hour": h, "day_of_week": dt.dayofweek,
            "is_weekend": int(dt.dayofweek >= 5),
            "month": dt.month, "week_of_year": dt.isocalendar().week,
            "day_of_month": dt.day,
            "is_payday": int(dt.day <= 3 or dt.day >= 28),
            "temp_c": temp_c, "rain_mm": rain_mm,
            "humidity_pct": humidity, "wind_kmh": wind_kmh,
            "rain_class": rain_class, "rain_3h": rain_3h,
            "in_event_window": in_event,
            "hours_since_event_start": max(hse, 0.0),
            "hours_until_event_end":   max(hue, 0.0),
            "zone_enc": ZONE_ENC.get(zone, 0),
            "zone_hour_mean": zhm_val,
            # metadata (not features)
            "_dt": dt, "_rain_mm": rain_mm,
            "_ev_type": ev_type, "_in_event": in_event,
        })
    return pd.DataFrame(rows)

def get_event_summary(row) -> str:
    parts = []
    if row["_rain_mm"] > 0:
        parts.append(f"🌧 Rain {row['_rain_mm']:.1f} mm at {row['hour']:02d}:00")
    if row["_in_event"]:
        parts.append(f"📅 Event: {row['_ev_type'].replace('_',' ').title()}")
    return " | ".join(parts) if parts else "☀ Clear, no events"

# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════
st.title("🚖 Addis Ride Demand Forecast")
st.caption("Qiyas AI Hackathon #2 — Addis Ride Demand Forecasting Challenge")

with st.sidebar:
    st.header("Forecast Settings")
    zone = st.selectbox("📍 Zone", CANONICAL_ZONES, index=CANONICAL_ZONES.index("Bole"))
    chosen_date = st.date_input(
        "📅 Date (Nov 1–14 2025)",
        value=NOV_START,
        min_value=NOV_START,
        max_value=NOV_END,
    )
    run_btn = st.button("🔮 Generate Forecast", type="primary", use_container_width=True)
    st.markdown("---")
    st.caption("The app automatically looks up weather forecasts and events — no manual input needed.")

if not run_btn:
    st.info("👈 Choose a zone and date in the sidebar, then click **Generate Forecast**.")
    st.stop()

# date range guard
if not (NOV_START <= chosen_date <= NOV_END):
    st.error(f"⚠️ Please pick a date between {NOV_START} and {NOV_END}.")
    st.stop()

# build features
feat_df = build_features(zone, chosen_date)

# predict
if model is not None and feature_cols is not None:
    X = feat_df[feature_cols]
    preds = np.clip(model.predict(X), 0, None).round(0).astype(int)
else:
    # fallback: use zone_hour_mean
    preds = feat_df["zone_hour_mean"].round(0).astype(int).values
    st.warning("Model file not loaded — showing zone-hour mean as fallback.")

avg_fare  = fare_map.get(zone, 40.0)
drivers   = np.round(preds / 1.3, 0).astype(int)
revenue   = np.round(preds * avg_fare, 0).astype(int)
peak_hour = int(feat_df.iloc[np.argmax(preds)]["hour"])

# ── summary cards ─────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("📍 Zone",       zone)
col2.metric("🕐 Peak Hour",  f"{peak_hour:02d}:00")
col3.metric("🚗 Peak Trips", f"{preds.max()}")
col4.metric("💰 Est. Revenue", f"{revenue.sum():,} Birr")

st.markdown("---")

# ── chart ─────────────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Get typical zone profile from zone_hour_means
typical = zone_hour_means[zone_hour_means["zone"] == zone].sort_values("hour")["trips"].values

fig, ax = plt.subplots(figsize=(12, 4))
ax.fill_between(range(24), typical, alpha=0.15, color="#0077BB", label="Typical profile")
ax.plot(range(24), typical, color="#0077BB", linewidth=1.5, linestyle="--", alpha=0.6)
ax.plot(range(24), preds,   color="#EE7733", linewidth=2.5, marker="o", markersize=5, label="Forecast")

# shade event windows
shaded = False
for _, row in feat_df.iterrows():
    if row["_in_event"]:
        ax.axvspan(row["hour"] - 0.5, row["hour"] + 0.5, alpha=0.15, color="#CC3311")
        if not shaded:
            ax.axvspan(0, 0, alpha=0.3, color="#CC3311", label="Event window")
            shaded = True

ax.axvline(peak_hour, color="#CC3311", linestyle=":", linewidth=1.5, alpha=0.7)
ax.set_xlabel("Hour of day"); ax.set_ylabel("Predicted trips"); ax.set_xticks(range(0, 24, 2))
ax.set_title(f"Hourly Forecast — {zone} | {chosen_date}")
ax.legend(); ax.set_xlim(0, 23); ax.set_ylim(bottom=0)
plt.tight_layout()
st.pyplot(fig)
plt.close()

# ── detail table ──────────────────────────────────────────────────────────────
st.subheader("📊 Hourly Breakdown")
table = pd.DataFrame({
    "Hour":             [f"{h:02d}:00" for h in range(24)],
    "Predicted Trips":  preds,
    "Drivers Needed":   drivers,
    "Est. Revenue (Birr)": revenue,
    "Weather / Events": [get_event_summary(feat_df.iloc[h]) for h in range(24)],
})
st.dataframe(table, use_container_width=True, hide_index=True)

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"**How it works:** The model looks up weather forecasts and events for {zone} on {chosen_date}, "
    f"builds 24 feature rows, and runs them through a LightGBM model trained on Jan–Oct 2025 trip history. "
    f"Revenue = predicted trips × historical avg fare ({avg_fare:.0f} Birr) for {zone}. "
    f"Drivers = predicted trips ÷ 1.3 trips/driver-hour."
)
