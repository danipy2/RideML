import os, glob, pandas as pd

checks = []

def chk(label, condition, detail=''):
    status = 'PASS' if condition else 'FAIL'
    checks.append((label, status, detail))

# Submission
sub = pd.read_csv('submission/team_qiyas_submission.csv')
chk('Submission: 4032 rows',           len(sub)==4032,         str(len(sub)))
chk('Submission: correct columns',     list(sub.columns)==['row_id','predicted_trips'])
chk('Submission: no negatives',        int((sub['predicted_trips']<0).sum())==0)
chk('Submission: no NaN',             int(sub['predicted_trips'].isna().sum())==0)
chk('Submission: 4032 unique row_ids', sub['row_id'].nunique()==4032)

# Key files
required_files = [
    'data/processed/master_train.csv',
    'data/processed/master_test.csv',
    'data/processed/data_dictionary_master.csv',
    'models/final_model.joblib',
    'models/feature_list.joblib',
    'reports/A_cleaning_and_integration.md',
    'reports/B_analysis_report.md',
    'reports/D_model_evaluation.md',
    'reports/stretch_zone_equity.md',
    'README.md',
    'requirements.txt',
    'app/app.py',
    'app/assets/final_model.joblib',
    'figures/figure_captions.md',
]
for f in required_files:
    chk('File exists: ' + f, os.path.exists(f))

# Figures
fig_names = [
    'fig01_gaps_and_missingness',
    'fig02_before_after_cleaning',
    'fig03_demand_trend_with_holidays',
    'fig04_hour_by_weekday_heatmap',
    'fig05_zone_profiles',
    'fig06_weather_timezone_check',
    'fig07_rain_effect',
    'fig08_event_study',
    'fig09_holiday_effects',
    'fig10_model_comparison',
    'fig11_forecast_vs_actual',
    'fig12_feature_importance',
]
for fn in fig_names:
    chk('Figure: ' + fn, os.path.exists('figures/' + fn + '.png'))

# Notebooks
for nb in ['01_cleaning_and_integration','02_analysis_report','03_visualizations','04_modeling_and_evaluation']:
    chk('Notebook: ' + nb, os.path.exists('notebooks/' + nb + '.ipynb'))

# No absolute paths in src files
for pyf in glob.glob('src/*.py'):
    with open(pyf, encoding='utf-8', errors='ignore') as fh:
        content = fh.read()
    has_abs = 'c:/qiays' in content.lower() or 'c:\\users' in content.lower()
    chk('No abs path: ' + pyf, not has_abs, 'ABSOLUTE PATH FOUND' if has_abs else '')

# Print results
maxlen = max(len(c[0]) for c in checks)
for label, status, detail in checks:
    sym = '[OK]' if status == 'PASS' else '[!!]'
    line = sym + ' ' + status + '  ' + label
    if detail:
        line += '  -> ' + detail
    print(line)

fails = [c for c in checks if c[1] == 'FAIL']
print()
print(str(len(checks) - len(fails)) + '/' + str(len(checks)) + ' checks passed.')
if fails:
    print('FAILURES:')
    for f in fails:
        print('  FAIL: ' + f[0] + ' ' + f[2])
