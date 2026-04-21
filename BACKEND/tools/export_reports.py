"""Utility to export reports to a JSON array or CSV from the newline-delimited storage.
Usage: python tools/export_reports.py --json out.json
"""
import argparse
import json
from pathlib import Path
import os

REPORTS_FILE = os.environ.get('REPORTS_FILE') or str(Path(__file__).resolve().parents[1] / 'data' / 'reports.json')

def read_reports(path):
    reports = []
    p = Path(path)
    if not p.exists():
        print('No reports file found at', path)
        return reports
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                reports.append(json.loads(line))
            except Exception:
                continue
    return reports

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', help='Write JSON array to file')
    parser.add_argument('--csv', help='Write CSV to file')
    args = parser.parse_args()

    reports = read_reports(REPORTS_FILE)
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        print('Wrote', len(reports), 'reports to', args.json)
    if args.csv:
        with open(args.csv, 'w', encoding='utf-8') as f:
            f.write('time,issue,emotion,urgency,summary\n')
            for r in reports:
                summary = (r.get('summary') or '').replace('"','""')
                f.write(f"{r.get('time','')},{r.get('issue','')},{r.get('emotion','')},{r.get('urgency','')},\"{summary}\"\n")
        print('Wrote', len(reports), 'reports to', args.csv)

if __name__ == '__main__':
    main()
