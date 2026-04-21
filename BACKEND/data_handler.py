import os, json, uuid
from datetime import datetime, timezone
from typing import List, Dict

BASE_DIR             = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR     = os.path.join(BASE_DIR, 'data')
DEFAULT_REPORTS_FILE = os.path.join(DEFAULT_DATA_DIR, 'reports.json')

def get_reports_file() -> str:
    path = os.environ.get('REPORTS_FILE')
    if path:
        return path
    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    return DEFAULT_REPORTS_FILE

# Department routing map
DEPT_ROUTING = {
    'Health':     'hospital',
    'Accident':   'police',
    'Safety':     'police',
    'Water':      'water',
    'Food':       'ngo',
    'Education':  'education',
    'Employment': 'employment',
    'Other':      'admin',
}

def save_report(analysis: Dict, message: str = None, location=None,
                emergency: str = None, photo: str = None) -> str:
    report_id  = f"SB-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    issue      = analysis.get('issue', 'Other')
    department = DEPT_ROUTING.get(issue, 'admin')

    report = {
        'id':         report_id,
        'issue':      issue,
        'emotion':    analysis.get('emotion', 'Calm'),
        'urgency':    analysis.get('urgency', 'Medium'),
        'summary':    analysis.get('summary', ''),
        'confidence': analysis.get('confidence', 0.5),
        'model':      analysis.get('model', 'heuristic'),
        'message':    message,
        'location':   location,
        'emergency':  emergency,
        'photo':      photo,
        'department': department,
        'status':     'Submitted',
        'dept_note':  '',
        'time':       datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }

    fp = get_reports_file()
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'a', encoding='utf-8') as f:
        f.write(json.dumps(report, ensure_ascii=False) + '\n')

    # background index rebuild
    try:
        import threading
        def _bg():
            try:
                from embeddings_store import build_and_save_index
                build_and_save_index(read_reports())
            except: pass
        threading.Thread(target=_bg, daemon=True).start()
    except: pass

    return report_id

def read_reports() -> List[Dict]:
    reports = []
    fp = get_reports_file()
    if not os.path.exists(fp):
        return reports
    with open(fp, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                reports.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return reports

def aggregate_reports() -> Dict:
    reports       = read_reports()
    issue_count   = {}
    emotion_count = {}
    for r in reports:
        i = r.get('issue', 'Other');  issue_count[i]   = issue_count.get(i, 0) + 1
        e = r.get('emotion', 'Calm'); emotion_count[e] = emotion_count.get(e, 0) + 1
    return {
        'totalVoices':  len(reports),
        'highUrgency':  sum(1 for r in reports if r.get('urgency') == 'High'),
        'topIssue':     max(issue_count, key=issue_count.get) if issue_count else '-',
        'issues':       issue_count,
        'emotions':     emotion_count,
    }
