"""
Build the 5-slide HTML presentation and embed all figures as base64.
Run from the project root: python build_slides.py
Output: presentation/team_qiyas_slides.html
"""
import base64, os

os.makedirs("presentation", exist_ok=True)

def b64img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return ""

fig03 = b64img("figures/fig03_demand_trend_with_holidays.png")
fig08 = b64img("figures/fig08_event_study.png")
fig10 = b64img("figures/fig10_model_comparison.png")
fig11 = b64img("figures/fig11_forecast_vs_actual.png")
fig12 = b64img("figures/fig12_feature_importance.png")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Team Qiyas — Addis Ride Demand Forecasting</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

  *{{margin:0;padding:0;box-sizing:border-box;}}

  :root{{
    --accent:#6C63FF;
    --accent2:#00D4AA;
    --bg:#0D0D1A;
    --card:rgba(255,255,255,0.06);
    --border:rgba(255,255,255,0.10);
    --text:#E8E8F0;
    --muted:#8888AA;
  }}

  html,body{{width:100%;height:100%;overflow:hidden;background:var(--bg);font-family:'Inter',sans-serif;color:var(--text);}}

  /* ── SLIDE CONTAINER ── */
  .deck{{width:100vw;height:100vh;position:relative;}}
  .slide{{
    position:absolute;inset:0;
    display:flex;flex-direction:column;justify-content:center;align-items:center;
    padding:48px 72px;
    opacity:0;transform:translateX(60px);
    transition:opacity .45s ease,transform .45s ease;
    pointer-events:none;
  }}
  .slide.active{{opacity:1;transform:translateX(0);pointer-events:all;}}
  .slide.exit{{opacity:0;transform:translateX(-60px);}}

  /* ── BACKGROUND BLOBS ── */
  .blob{{position:fixed;border-radius:50%;filter:blur(120px);opacity:.18;pointer-events:none;z-index:0;}}
  .b1{{width:600px;height:600px;background:var(--accent);top:-180px;left:-150px;}}
  .b2{{width:500px;height:500px;background:var(--accent2);bottom:-140px;right:-100px;}}

  /* ── SLIDE INNER ── */
  .slide > *{{position:relative;z-index:1;width:100%;}}

  /* ── TYPOGRAPHY ── */
  .tag{{font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;
        color:var(--accent2);margin-bottom:10px;}}
  h1{{font-size:clamp(28px,4vw,52px);font-weight:800;line-height:1.1;margin-bottom:16px;
      background:linear-gradient(135deg,#fff 40%,var(--accent));
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
  h2{{font-size:clamp(22px,3vw,38px);font-weight:700;margin-bottom:14px;}}
  .sub{{font-size:clamp(14px,1.5vw,19px);color:var(--muted);margin-bottom:28px;line-height:1.6;}}

  /* ── GRID LAYOUTS ── */
  .cols{{display:grid;gap:24px;width:100%;}}
  .cols-2{{grid-template-columns:1fr 1fr;}}
  .cols-3{{grid-template-columns:repeat(3,1fr);}}

  /* ── CARDS ── */
  .card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:22px 24px;}}
  .card h3{{font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
            color:var(--accent);margin-bottom:8px;}}
  .card .big{{font-size:clamp(22px,3vw,38px);font-weight:800;color:#fff;}}
  .card .note{{font-size:13px;color:var(--muted);margin-top:4px;}}

  /* ── METRIC ROW ── */
  .metrics{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:24px;}}
  .metric{{background:var(--card);border:1px solid var(--border);border-radius:12px;
           padding:16px 22px;flex:1;min-width:130px;}}
  .metric .val{{font-size:28px;font-weight:800;color:#fff;}}
  .metric .lbl{{font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;
                color:var(--accent2);margin-top:4px;}}

  /* ── TABLE ── */
  table{{border-collapse:collapse;width:100%;font-size:13px;}}
  th{{background:rgba(108,99,255,.25);padding:10px 14px;text-align:left;
     font-weight:700;letter-spacing:1px;text-transform:uppercase;font-size:11px;color:var(--accent2);}}
  td{{padding:9px 14px;border-bottom:1px solid var(--border);}}
  tr:last-child td{{border-bottom:none;}}
  tr:hover td{{background:rgba(255,255,255,.04);}}
  .good{{color:#00D4AA;font-weight:700;}}
  .warn{{color:#FF8C42;font-weight:700;}}
  .best{{color:#6C63FF;font-weight:800;}}

  /* ── FIGURE ── */
  .fig{{border-radius:12px;overflow:hidden;border:1px solid var(--border);background:#111;}}
  .fig img{{width:100%;height:100%;object-fit:contain;display:block;}}
  .fig-label{{font-size:11px;color:var(--muted);text-align:center;padding:6px;
              border-top:1px solid var(--border);background:rgba(0,0,0,.3);}}

  /* ── JOIN MAP ── */
  .join-box{{background:var(--card);border:1px solid var(--border);border-radius:12px;
             padding:18px 24px;font-family:monospace;font-size:13px;line-height:2;}}
  .join-arrow{{color:var(--accent2);font-weight:700;}}
  .join-key{{color:var(--accent);}}

  /* ── PILL ── */
  .pill{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:11px;
         font-weight:700;letter-spacing:1px;text-transform:uppercase;margin:3px;}}
  .pill-purple{{background:rgba(108,99,255,.25);color:var(--accent);border:1px solid var(--accent);}}
  .pill-teal{{background:rgba(0,212,170,.15);color:var(--accent2);border:1px solid var(--accent2);}}
  .pill-red{{background:rgba(255,100,100,.15);color:#FF6464;border:1px solid #FF6464;}}

  /* ── SLIDE INDICATOR ── */
  .nav{{
    position:fixed;bottom:28px;left:50%;transform:translateX(-50%);
    display:flex;gap:10px;z-index:100;align-items:center;
  }}
  .dot{{width:8px;height:8px;border-radius:50%;background:var(--border);cursor:pointer;
        transition:all .3s;}}
  .dot.active{{width:24px;border-radius:4px;background:var(--accent);}}

  /* ── ARROW BUTTONS ── */
  .arrow{{
    position:fixed;top:50%;z-index:100;
    background:var(--card);border:1px solid var(--border);
    width:48px;height:48px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    cursor:pointer;font-size:20px;transition:all .2s;
    transform:translateY(-50%);
  }}
  .arrow:hover{{background:var(--accent);border-color:var(--accent);}}
  .arrow-left{{left:20px;}}
  .arrow-right{{right:20px;}}

  /* ── SLIDE NUMBER ── */
  .slide-num{{
    position:fixed;top:24px;right:32px;font-size:12px;
    color:var(--muted);letter-spacing:1px;z-index:100;
  }}

  /* ── PROGRESS BAR ── */
  .progress{{
    position:fixed;top:0;left:0;height:3px;
    background:linear-gradient(90deg,var(--accent),var(--accent2));
    transition:width .4s ease;z-index:200;
  }}

  /* ── HERO ACCENT LINE ── */
  .accent-line{{
    width:60px;height:4px;border-radius:2px;
    background:linear-gradient(90deg,var(--accent),var(--accent2));
    margin-bottom:20px;
  }}

  /* ── STEP LIST ── */
  .steps{{list-style:none;}}
  .steps li{{display:flex;gap:14px;align-items:flex-start;margin-bottom:14px;}}
  .steps li .icon{{
    min-width:32px;height:32px;border-radius:8px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;
    flex-shrink:0;margin-top:2px;
  }}
  .steps li .text{{font-size:14px;color:var(--muted);line-height:1.5;}}
  .steps li .text strong{{color:#fff;}}
</style>
</head>
<body>

<div class="blob b1"></div>
<div class="blob b2"></div>

<div class="progress" id="prog"></div>
<div class="slide-num" id="slideNum">1 / 5</div>

<div class="arrow arrow-left" onclick="prev()">&#8592;</div>
<div class="arrow arrow-right" onclick="next()">&#8594;</div>

<div class="deck" id="deck">

<!-- ═══════════════════════════════════════════════
     SLIDE 1 — The Problem
═══════════════════════════════════════════════ -->
<div class="slide active" id="s1">
  <div class="tag">AI Engineering · Qiyas Team · Oct 2026</div>
  <h1>Forecasting Ride Demand<br>Across Addis Ababa</h1>
  <p class="sub">Predict trips for 12 zones × 24 hours × 14 days = 4,032 forecasts<br>
  Using 10 months of history + weather + city events</p>
  <div class="accent-line"></div>

  <div class="cols cols-3" style="margin-bottom:24px;">
    <div class="card">
      <h3>📦 Trip History</h3>
      <div class="big">~85K</div>
      <div class="note">Zone-hour rows · Jan–Oct 2025<br>Target: <strong>trips</strong> count</div>
    </div>
    <div class="card">
      <h3>🌦️ Weather</h3>
      <div class="big">7,500</div>
      <div class="note">Hourly readings citywide<br>Temp · Rain · Humidity · Wind</div>
    </div>
    <div class="card">
      <h3>📅 Events</h3>
      <div class="big">165</div>
      <div class="note">Holidays · Football · Concerts<br>Conferences · Road closures</div>
    </div>
  </div>

  <div class="cols cols-2">
    <div class="card">
      <h3>🎯 The Problem</h3>
      <div class="note" style="font-size:14px;line-height:1.7;">
        A ride-hailing company needs to know — <em>a day ahead</em> — how many trips each zone will see each hour.
        Without a forecast, drivers are in the wrong place. Riders wait. Revenue is lost.
      </div>
    </div>
    <div class="card">
      <h3>💡 Our Approach</h3>
      <ul class="steps" style="margin-top:6px;">
        <li><div class="icon">1</div><div class="text"><strong>Clean & Join</strong> all 3 raw tables</div></li>
        <li><div class="icon">2</div><div class="text"><strong>Engineer</strong> 18 features from time, weather, events</div></li>
        <li><div class="icon">3</div><div class="text"><strong>Train</strong> LightGBM on 10 months of history</div></li>
        <li><div class="icon">4</div><div class="text"><strong>Deploy</strong> interactive forecast demo</div></li>
      </ul>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════
     SLIDE 2 — Cleaning & Integration
═══════════════════════════════════════════════ -->
<div class="slide" id="s2">
  <div class="tag">Data Engineering · Cleaning &amp; Integration</div>
  <h2>Three Messy Tables → One Clean Training Set</h2>
  <p class="sub">Raw data from 3 sources, joined into a single high-quality training set</p>

  <div class="cols cols-2" style="margin-bottom:20px;">
    <div>
      <div class="join-box">
        <div><span class="join-key">ride_demand_train</span> (left)</div>
        <div class="join-arrow">  └─ MANY-TO-ONE ──►</div>
        <div><span class="join-key">  weather_hourly</span></div>
        <div style="color:var(--muted);font-size:11px;margin-left:28px;">on pickup_hour = timestamp_eat (UTC+3)</div>
        <br/>
        <div><span class="join-key">ride_demand_train</span> (left)</div>
        <div class="join-arrow">  └─ INTERVAL JOIN ──►</div>
        <div><span class="join-key">  events_calendar</span></div>
        <div style="color:var(--muted);font-size:11px;margin-left:28px;">zone match + hour BETWEEN start−1h AND end+1h</div>
      </div>

      <div style="margin-top:14px;">
        <span class="pill pill-teal">83,777 rows preserved</span>
        <span class="pill pill-purple">24.0% inside event window</span>
        <span class="pill pill-red">2,173 unmatched weather → filled</span>
      </div>
    </div>

    <div>
      <table>
        <thead><tr><th>Issue Fixed</th><th>Rows</th><th>Fix</th></tr></thead>
        <tbody>
          <tr><td>50+ zone spellings</td><td class="warn">all rows</td><td>Mapped → 12 canonical</td></tr>
          <tr><td>Negative trips (−1 sentinel)</td><td class="warn">681</td><td>Median imputation</td></tr>
          <tr><td>Weather UTC → EAT (+3h)</td><td class="warn">all weather</td><td>tz_convert</td></tr>
          <tr><td>Temp in Fahrenheit (>50°C)</td><td class="warn">350</td><td>×5/9 − 32</td></tr>
          <tr><td>3 timestamp formats (rides)</td><td class="warn">mixed</td><td>Parsed all 3</td></tr>
          <tr><td>Missing end times (events)</td><td class="warn">4</td><td>Median duration</td></tr>
          <tr><td>Inverted start/end date</td><td class="warn">1</td><td>Swapped</td></tr>
        </tbody>
      </table>

      <div class="card" style="margin-top:14px;padding:12px 16px;">
        <h3>⏰ Clock Proof</h3>
        <div class="note" style="font-size:13px;">
          Weather raw timestamps end in "Z" (UTC). After +3h conversion to EAT,
          temperature peaks at <strong style="color:#fff;">15:00 local time</strong>
          — consistent with Addis Ababa afternoon heat. Wrong clock = wrong join = wrong model.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════
     SLIDE 3 — Key Insights
═══════════════════════════════════════════════ -->
<div class="slide" id="s3">
  <div class="tag">Analysis &amp; Visualization · Key Findings</div>
  <h2>What the Data Tells Us</h2>
  <p class="sub">Two critical patterns the model must learn to produce useful forecasts</p>

  <div class="cols cols-2" style="height:55vh;">
    <div style="display:flex;flex-direction:column;gap:12px;">
      <div class="fig" style="flex:1;">
        <img src="{fig03}" alt="Demand trend Jan-Oct 2025"/>
        <div class="fig-label">
          📈 Finding 1 — City-wide demand <strong>grew +51.9%</strong> from Jan to Oct 2025.
          November forecasts must account for this trend — a static model underestimates.
        </div>
      </div>
      <div class="metrics">
        <div class="metric"><div class="val">+52%</div><div class="lbl">Demand growth</div></div>
        <div class="metric"><div class="val">71%</div><div class="lbl">Holiday drop</div></div>
        <div class="metric"><div class="val">5.8%</div><div class="lbl">Payday uplift</div></div>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;gap:12px;">
      <div class="fig" style="flex:1;">
        <img src="{fig08}" alt="Event study — demand around events"/>
        <div class="fig-label">
          ⚽ Finding 2 — Football matches create a <strong>+91% demand spike</strong>.
          Concerts rank #1 (71 trips/hr vs 28 baseline). Events are essential model features.
        </div>
      </div>
      <div class="metrics">
        <div class="metric"><div class="val">+91%</div><div class="lbl">Football uplift</div></div>
        <div class="metric"><div class="val">2.26×</div><div class="lbl">Rain multiplier</div></div>
        <div class="metric"><div class="val">24%</div><div class="lbl">Zone-hours in event window</div></div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════
     SLIDE 4 — Modeling & Evaluation
═══════════════════════════════════════════════ -->
<div class="slide" id="s4">
  <div class="tag">ML Pipeline · Model Selection &amp; Evaluation</div>
  <h2>LightGBM Beats Baseline by 23%</h2>
  <p class="sub">Train: Jan 1 – Oct 17 &nbsp;|&nbsp; Validate: Oct 18 – Oct 31 &nbsp;|&nbsp; Chronological holdout — never touched test data</p>

  <div class="cols cols-2" style="margin-bottom:16px;">
    <div>
      <table>
        <thead><tr><th>Model</th><th>RMSE</th><th>MAE</th><th>Time</th></tr></thead>
        <tbody>
          <tr><td>Global Mean baseline</td><td class="warn">27.80</td><td class="warn">20.76</td><td>—</td></tr>
          <tr><td>Seasonal Naive baseline</td><td class="warn">12.00</td><td class="warn">7.37</td><td>—</td></tr>
          <tr><td>Ridge (linear)</td><td>14.80</td><td>10.36</td><td>0.2s</td></tr>
          <tr><td>Random Forest</td><td>9.98</td><td>6.27</td><td>11.0s</td></tr>
          <tr><td>HistGradientBoosting</td><td>9.51</td><td>6.08</td><td>3.7s</td></tr>
          <tr style="background:rgba(108,99,255,.12);">
            <td><strong>LightGBM (tuned)</strong></td>
            <td class="best">9.24</td><td class="best">5.85</td><td class="good">3.6s</td>
          </tr>
        </tbody>
      </table>

      <div style="margin-top:12px;">
        <table>
          <thead><tr><th>Ablation — Feature Set</th><th>RMSE</th><th>Improvement</th></tr></thead>
          <tbody>
            <tr><td>Calendar + Zone only</td><td>10.04</td><td>—</td></tr>
            <tr><td>+ Weather</td><td>9.57</td><td class="good">−0.47</td></tr>
            <tr><td>+ Events</td><td>9.78</td><td class="good">−0.26</td></tr>
            <tr><td><strong>All combined</strong></td><td class="best">9.35</td><td class="good">−0.69</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;gap:14px;">
      <div class="card">
        <h3>📊 Rolling-Origin Validation (4 folds)</h3>
        <div class="big">12.10 <span style="font-size:18px;color:var(--muted);">± 2.29</span></div>
        <div class="note">Mean RMSE across folds. Fold 1 high (15.90) because only 6 months of history — expected with growing data.</div>
      </div>
      <div class="fig" style="flex:1;">
        <img src="{fig10}" alt="Model comparison"/>
        <div class="fig-label">fig10 — Validation RMSE for all models tested</div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════
     SLIDE 5 — Errors, Score, Demo
═══════════════════════════════════════════════ -->
<div class="slide" id="s5">
  <div class="tag">Results &amp; Product · Error Analysis &amp; Demo</div>
  <h2>Final Score &amp; Where We Can Still Improve</h2>

  <div class="cols cols-2" style="margin-bottom:16px;">
    <div style="display:flex;flex-direction:column;gap:14px;">
      <div class="metrics">
        <div class="metric"><div class="val">9.24</div><div class="lbl">RMSE trips/hr</div></div>
        <div class="metric"><div class="val">5.85</div><div class="lbl">MAE trips/hr</div></div>
        <div class="metric"><div class="val">88%</div><div class="lbl">R² explained</div></div>
      </div>

      <div class="card">
        <h3>📍 Error by Zone</h3>
        <table>
          <thead><tr><th>Zone</th><th>MAE</th><th>% Error</th></tr></thead>
          <tbody>
            <tr><td>Merkato</td><td class="warn">8.06</td><td>16.4%</td></tr>
            <tr><td>Megenagna</td><td class="warn">7.93</td><td>17.9%</td></tr>
            <tr><td>Bole</td><td>7.39</td><td>16.2%</td></tr>
            <tr><td>Ayat (newest)</td><td>4.20</td><td class="warn">19.7%</td></tr>
          </tbody>
        </table>
      </div>

      <div class="card" style="background:rgba(108,99,255,.12);">
        <h3>🎯 Hardest Hours</h3>
        <div style="font-size:13px;color:var(--muted);line-height:1.8;">
          <strong style="color:#fff;">18:00</strong> — MAE 11.0 (evening rush + events)<br/>
          <strong style="color:#fff;">07:00</strong> — MAE 8.4 (morning commute)<br/>
          <strong style="color:#fff;">17:00</strong> — MAE 8.4 (pre-event travel)<br/>
          <em>Primary cause: uncalendared events we cannot see</em>
        </div>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;gap:14px;">
      <div class="fig" style="flex:1;">
        <img src="{fig11}" alt="Forecast vs Actual"/>
        <div class="fig-label">fig11 — Predicted vs actual trips over the 14-day validation period (3 zones)</div>
      </div>

      <div class="card">
        <h3>🚀 Demo</h3>
        <div class="note" style="font-size:13px;line-height:1.8;">
          Select any zone + date (Nov 1–14) →<br/>
          App auto-looks up <strong style="color:#fff;">weather forecast</strong> + <strong style="color:#fff;">events</strong> →<br/>
          Returns 24-hour forecast curve · peak hour ·<br/>
          drivers needed · expected fares
        </div>
        <div style="margin-top:10px;">
          <code style="background:rgba(0,0,0,.4);padding:6px 12px;border-radius:6px;font-size:12px;color:var(--accent2);">
            streamlit run app/app.py
          </code>
        </div>
      </div>

      <div class="card" style="background:rgba(0,212,170,.08);border-color:rgba(0,212,170,.3);">
        <h3>🔮 What We'd Do With More Time</h3>
        <div style="font-size:13px;color:var(--muted);line-height:1.8;">
          <span class="pill pill-teal">Lag features (last week same hour)</span>
          <span class="pill pill-purple">Zone-specific sub-models for Merkato</span>
          <span class="pill pill-teal">Prediction intervals for operations confidence</span>
          <span class="pill pill-purple">Live event feed integration</span>
        </div>
      </div>
    </div>
  </div>
</div>

</div><!-- /deck -->

<!-- NAV DOTS -->
<div class="nav" id="nav">
  <div class="dot active" onclick="goTo(0)"></div>
  <div class="dot" onclick="goTo(1)"></div>
  <div class="dot" onclick="goTo(2)"></div>
  <div class="dot" onclick="goTo(3)"></div>
  <div class="dot" onclick="goTo(4)"></div>
</div>

<script>
const slides = document.querySelectorAll('.slide');
const dots   = document.querySelectorAll('.dot');
const prog   = document.getElementById('prog');
const snum   = document.getElementById('slideNum');
let cur = 0;

function goTo(n) {{
  slides[cur].classList.remove('active');
  slides[cur].classList.add('exit');
  setTimeout(()=> slides[cur].classList.remove('exit'), 450);
  cur = ((n % slides.length) + slides.length) % slides.length;
  slides[cur].classList.add('active');
  dots.forEach((d,i)=> d.classList.toggle('active', i===cur));
  prog.style.width = ((cur+1)/slides.length*100) + '%';
  snum.textContent = (cur+1) + ' / ' + slides.length;
}}
function next(){{ goTo(cur+1); }}
function prev(){{ goTo(cur-1); }}

document.addEventListener('keydown', e => {{
  if(e.key==='ArrowRight'||e.key===' ') next();
  if(e.key==='ArrowLeft') prev();
}});

// Touch swipe
let tx=0;
document.addEventListener('touchstart', e=> tx=e.touches[0].clientX);
document.addEventListener('touchend',   e=> {{
  const dx = e.changedTouches[0].clientX - tx;
  if(dx < -50) next();
  if(dx >  50) prev();
}});

// Init progress
prog.style.width = '20%';
</script>
</body>
</html>"""

out = "presentation/team_qiyas_slides.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Saved: {out} ({len(html):,} bytes)")
