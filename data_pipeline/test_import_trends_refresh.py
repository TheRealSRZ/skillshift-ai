"""Safe smoke tests for SkillShift AI's DOSM quarterly trend importer.

Run from repository root: python data_pipeline/test_import_trends_refresh.py
Does not modify the real CSV or the production trend JSON.
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / 'data_pipeline' / 'import_trends.py'
SOURCE = ROOT / 'data' / 'jmi_major_occupation_2025_2026.csv'


def run_import(inp, out):
    return subprocess.run(
        [sys.executable, str(IMPORTER), '--input', str(inp), '--output', str(out)],
        cwd=ROOT, text=True, capture_output=True,
    )


def write_rows(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    with SOURCE.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    if not fields or not rows:
        raise RuntimeError('Input CSV is empty or lacks headers')
    with tempfile.TemporaryDirectory(prefix='skillshift_trend_test_') as folder:
        tmp = Path(folder)
        source_copy = tmp / 'unchanged.csv'
        standard_out = tmp / 'standard.json'
        write_rows(source_copy, fields, rows)
        p = run_import(source_copy, standard_out)
        assert p.returncode == 0, f'Baseline import failed: {p.stderr}'
        baseline = json.loads(standard_out.read_text(encoding='utf-8'))
        assert baseline['previous_period'] == '2026-Q1' and baseline['latest_period'] == '2026-Q2'
        print('PASS 1: Real CSV imports unchanged and compares Q1 -> Q2 2026')

        # Clearly synthetic Q3 test: reuse Q2 counts with a +1 change for each group.
        # Do not give this data to users, mix it into production evidence, or commit it.
        q2_rows = [row for row in rows if row['period'] == '2026-Q2']
        assert q2_rows, 'No Q2 2026 observations found'
        fake_q3 = []
        for row in q2_rows:
            altered = dict(row)
            altered['period'] = '2026-Q3'
            altered['job_offerings'] = str(int(row['job_offerings']) + 1)
            fake_q3.append(altered)
        future_in = tmp / 'SYNTHETIC_Q3_DO_NOT_PUBLISH.csv'
        future_out = tmp / 'synthetic_output.json'
        write_rows(future_in, fields, rows + fake_q3)
        p = run_import(future_in, future_out)
        assert p.returncode == 0, f'Synthetic refresh failed: {p.stderr}'
        result = json.loads(future_out.read_text(encoding='utf-8'))
        assert result['previous_period'] == '2026-Q2'
        assert result['latest_period'] == '2026-Q3'
        assert len(result['group_comparisons']) == len(q2_rows)
        assert all(c['absolute_change'] == 1 for c in result['group_comparisons'])
        print(f'PASS 2: Synthetic Q3 input refreshes Q2 -> Q3 for {len(q2_rows)} groups')

        duplicate_in = tmp / 'duplicate.csv'
        duplicate_out = tmp / 'duplicate_output.json'
        write_rows(duplicate_in, fields, rows + [dict(rows[-1])])
        p = run_import(duplicate_in, duplicate_out)
        assert p.returncode != 0 and 'duplicate' in p.stderr.lower(), p.stderr
        assert not duplicate_out.exists()
        print('PASS 3: Duplicate period/group is rejected without producing output')

        invalid_rows = [dict(r) for r in rows]
        invalid_rows[0]['job_offerings'] = '-1'
        bad_in = tmp / 'invalid.csv'
        bad_out = tmp / 'invalid_output.json'
        write_rows(bad_in, fields, invalid_rows)
        p = run_import(bad_in, bad_out)
        assert p.returncode != 0 and 'nonnegative integer' in p.stderr.lower(), p.stderr
        assert not bad_out.exists()
        print('PASS 4: Negative job-offering counts are rejected')

        gap_rows = [dict(r) for r in rows if r['period'] != '2026-Q1']
        gap_in = tmp / 'gap.csv'
        gap_out = tmp / 'gap_output.json'
        write_rows(gap_in, fields, gap_rows)
        p = run_import(gap_in, gap_out)
        assert p.returncode != 0 and 'not consecutive' in p.stderr.lower(), p.stderr
        assert not gap_out.exists()
        print('PASS 5: Nonconsecutive latest quarters are rejected')

    print('SUCCESS: 5 trend importer smoke tests passed; temporary synthetic files removed.')


if __name__ == '__main__':
    main()
