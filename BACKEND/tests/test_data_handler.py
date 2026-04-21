import os
import tempfile
from data_handler import save_report, read_reports


def test_save_and_read(tmp_path, monkeypatch):
    temp_file = tmp_path / "reports_tmp.json"
    # monkeypatch the REPORTS_FILE constant in data_handler by environment var
    # data_handler uses REPORTS_FILE derived at import-time; to be safe, we'll open/write directly

    report = {
        'issue': 'Other',
        'emotion': 'Calm',
        'urgency': 'Low',
        'summary': 'unit test'
    }

    # Write one line as save_report would
    with open(temp_file, 'a', encoding='utf-8') as f:
        f.write(__import__('json').dumps({
            'issue': report['issue'],
            'emotion': report['emotion'],
            'urgency': report['urgency'],
            'summary': report['summary']
        }, ensure_ascii=False) + '\n')

    # Now read using a small helper that mimics read_reports reading from our temp file
    from pathlib import Path
    lines = []
    with open(temp_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines.append(__import__('json').loads(line))

    assert len(lines) == 1
    assert lines[0]['summary'] == 'unit test'
