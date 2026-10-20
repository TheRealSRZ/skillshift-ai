"""Extract quarterly major-occupation online job-offering counts from DOSM JMI Q2 2026.

Install: python -m pip install pandas openpyxl
Run: python data_pipeline/clean_jmi.py "data/Data JMI Q2 2026.xlsx"
"""
import csv
import sys
from pathlib import Path

import pandas as pd

source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('data/Data JMI Q2 2026.xlsx')
if not source.is_file():
    raise FileNotFoundError(f'Cannot find Excel file: {source}')

# B33:AL43 in the official DOSM Q2 2026 workbook.
raw = pd.read_excel(source, sheet_name='e2-Summary Table BI', header=None, engine='openpyxl')
rows = raw.iloc[32:43, 1:38].values.tolist()
periods = ['2025-Q1', '2025-Q2', '2025-Q3', '2025-Q4', '2026-Q1', '2026-Q2']
positions = [31, 32, 33, 34, 35, 36]
assert [rows[0][i] for i in positions] == ['Q1','Q2','Q3','Q4','Q1','Q2'], 'Unexpected workbook layout'

records = []
for record in rows[1:]:
    occupation = record[0]
    if not isinstance(occupation, str) or occupation.strip() in ('Unclassified', 'Jumlah', ''):
        continue
    for period, idx in zip(periods, positions):
        value = record[idx]
        if not isinstance(value, (int, float)) or pd.isna(value):
            continue
        records.append([period, occupation.strip(), int(value), 'Malaysia', 'online_job_offerings_major_group', 'DOSM JMI Q2 2026', 'https://www.dosm.gov.my/portal-main/release-content/big-data-analytics-job-market-insights-q22026'])

assert any(r[:3] == ['2026-Q1', 'Professionals', 315768] for r in records), 'Q1 verification failed'
assert any(r[:3] == ['2026-Q2', 'Professionals', 285907] for r in records), 'Q2 verification failed'

output = source.with_name('jmi_major_occupation_2025_2026.csv')
with output.open('w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['period','occupation_group','job_offerings','geography','metric','source_title','source_url'])
    writer.writerows(records)
print(f'Success! Wrote {len(records)} records to {output}')
