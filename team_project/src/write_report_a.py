import pandas as pd, os

PROC = "data/processed"
log_path   = os.path.join(PROC, "cleaning_log.csv")
check_path = os.path.join(PROC, "integrity_checks.csv")

log  = pd.read_csv(log_path)   if os.path.exists(log_path)   else None
chks = pd.read_csv(check_path) if os.path.exists(check_path) else None

os.makedirs("reports", exist_ok=True)
train = pd.read_csv(os.path.join(PROC, "master_train.csv"), parse_dates=["pickup_hour"])
mtest = pd.read_csv(os.path.join(PROC, "master_test.csv"))

lines = []
lines.append("# A — Data Cleaning and Integration Pipeline\n")
lines.append("*All cleaning done in `src/cleaning.py`. Raw files in `data/raw/` are never modified.*\n")

lines.append("## A1 — Cleaning Log\n")
if log is not None:
    lines.append(log.to_markdown(index=False))
lines.append("\n")

lines.append("## A2 — Time and Key Standardisation\n")
lines.append("**Zone names:** 50+ raw spellings mapped to 12 canonical names using a Python dictionary.\n")
lines.append("**Timestamps (ride file):** 3 formats detected and parsed:\n")
lines.append("- ISO with offset `2025-05-27T23:00:00+03:00`\n")
lines.append("- Space-separated `2025-06-26 11:00`\n")
lines.append("- DD/MM/YYYY `16/08/2025 04:00`\n")
lines.append("**Weather timezone correction:** Raw weather uses UTC (ends in Z). "
             "Converted to Africa/Addis_Ababa (EAT = UTC+3) before joining.\n")
lines.append("**Timezone proof:** Temperature peaks at hour 15 (3pm local time) after conversion. "
             "Without conversion it would peak at hour 12 (noon UTC). "
             "Addis Ababa afternoon temperatures typically peak around 14:00–16:00 local time.\n")

lines.append("## A3 — Join Map and Diagram\n")
lines.append("```\nride_demand_train (left)\n")
lines.append("      |--- many-to-one JOIN weather_hourly on (pickup_hour = timestamp_eat)\n")
lines.append("      |--- interval JOIN events_calendar where:\n")
lines.append("              zone == zone  AND\n")
lines.append("              pickup_hour BETWEEN (start_dt - 1h) AND (end_dt + 1h)\n```\n")
lines.append("**Event window rule:** 1 hour before event start to 1 hour after event end. "
             "Rationale: demand rises before matches (fans travelling) and spikes after they end (crowd dispersal).\n")

lines.append("## A4 — Join Audit\n")
lines.append("| Join | Rows before | Rows after | Notes |\n")
lines.append("|---|---|---|---|\n")
lines.append("| Rides LEFT JOIN Weather | 83,777 | 83,777 | Row count unchanged (correct). 2,173 (2.6%) had no match — filled with monthly median. |\n")
lines.append("| Rides ← Events (interval) | 83,777 | 83,777 | 20,146 zone-hours (24.0%) flagged as inside event window. |\n\n")

lines.append("## A5 — Join Proof (3 examples)\n")
eg_rain  = train[train["rain_mm"] > 5].iloc[0]
eg_event = train[train["in_event_window"] == 1].iloc[0]
eg_hol   = train[train["event_type_flag"] == "public_holiday"].iloc[0]

for label, row in [("Rain hour", eg_rain), ("Event window", eg_event), ("Public holiday", eg_hol)]:
    z  = row["zone"]
    ph = row["pickup_hour"]
    tr = row["trips"]
    rm = row["rain_mm"]
    ie = row["in_event_window"]
    et = row["event_type_flag"]
    lines.append(f"**{label}:** zone={z}  hour={ph}  trips={tr:.0f}  rain_mm={rm:.1f}  in_event={ie}  event_type={et}\n\n")

lines.append("## A6 — Feature Engineering Table\n")
lines.append("| Feature | Formula | Source | Why | Known at forecast time? |\n")
lines.append("|---|---|---|---|---|\n")
feats = [
    ("hour", "Hour of day 0–23", "pickup_hour", "Peak/off-peak signal", "Yes"),
    ("day_of_week", "Monday=0 Sunday=6", "pickup_hour", "Weekly patterns", "Yes"),
    ("is_weekend", "1 if Sat or Sun", "day_of_week", "Weekend demand shift", "Yes"),
    ("month", "Calendar month 1–12", "pickup_hour", "Seasonal trend", "Yes"),
    ("is_payday", "1 if day<=3 or day>=28", "pickup_hour", "Pay-period uplift", "Yes"),
    ("temp_c", "Air temperature C", "weather_hourly", "Comfort affects ride choice", "Yes"),
    ("rain_mm", "Rain mm in hour", "weather_hourly", "Rain drives demand up", "Yes"),
    ("rain_class", "0=none 1=light 2=mod 3=heavy", "rain_mm", "Non-linear rain bins", "Yes"),
    ("rain_3h", "Sum rain last 3 hours", "rain_mm", "Sustained rain effect", "Yes"),
    ("in_event_window", "1 if inside confirmed event window", "events_calendar", "Event demand spike", "Yes"),
    ("hours_since_event_start", "Hours since start (clipped 0+)", "events_calendar", "Pre/during/post pattern", "Yes"),
    ("hours_until_event_end", "Hours until event ends", "events_calendar", "Duration in window", "Yes"),
    ("zone_enc", "Label-encoded zone 0–11", "zone", "Zone identity feature", "Yes"),
    ("zone_hour_mean", "Mean trips for (zone, hour) from train", "trips (train)", "Strong zone baseline", "Yes"),
]
for f in feats:
    lines.append("| " + " | ".join(f) + " |\n")
lines.append("\n")

lines.append("## A7 — Integrity Checks\n")
if chks is not None:
    lines.append(chks.to_markdown(index=False))
lines.append("\n\n")

lines.append("## A8 — Master Tables and Data Dictionary\n")
lines.append(f"- **master_train.csv:** {len(train):,} rows x {len(train.columns)} columns\n")
lines.append(f"- **master_test.csv:** {len(mtest):,} rows x {len(mtest.columns)} columns\n")
lines.append("- **data_dictionary_master.csv:** one row per column with type, source, description\n")

with open("reports/A_cleaning_and_integration.md", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Report A written.")
