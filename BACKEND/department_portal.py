from flask import Blueprint, request, jsonify
from functools import wraps
import os, json
from datetime import datetime, timedelta
from data_handler import read_reports

dept_bp    = Blueprint('department', __name__)
SECRET_KEY = os.getenv('JWT_SECRET', 'swarabharat-secret-2026')

# All departments and their issue types
DEPARTMENTS = {
    'hospital':   {'issues': ['Health'],              'label': 'Hospital / Medical',   'color': '#ef4444', 'icon': '🏥'},
    'ambulance':  {'issues': ['Health', 'Accident'],  'label': 'Ambulance Services',   'color': '#dc2626', 'icon': '🚑'},
    'police':     {'issues': ['Safety', 'Accident'],  'label': 'Police Department',    'color': '#1d4ed8', 'icon': '👮'},
    'fire':       {'issues': ['Accident', 'Safety'],  'label': 'Fire Department',      'color': '#ea580c', 'icon': '🚒'},
    'water':      {'issues': ['Water'],               'label': 'Water Supply Dept',    'color': '#0284c7', 'icon': '💧'},
    'education':  {'issues': ['Education'],           'label': 'Education Department', 'color': '#7c3aed', 'icon': '📚'},
    'food':       {'issues': ['Food'],                'label': 'Food & Civil Supplies','color': '#16a34a', 'icon': '🍽️'},
    'employment': {'issues': ['Employment'],          'label': 'Labour & Employment',  'color': '#ca8a04', 'icon': '💼'},
    'ngo':        {'issues': ['Food','Water','Health','Education'], 'label': 'NGO / Volunteers', 'color': '#0891b2', 'icon': '🤝'},
    'admin':      {'issues': ['Other'],               'label': 'General Administration','color': '#6366f1', 'icon': '🏛️'},
}

# Demo credentials (in production use a real DB)
DEMO_USERS = {
    'hospital_admin':   {'password': 'hospital123',   'department': 'hospital'},
    'ambulance_admin':  {'password': 'ambulance123',  'department': 'ambulance'},
    'police_admin':     {'password': 'police123',     'department': 'police'},
    'fire_admin':       {'password': 'fire123',       'department': 'fire'},
    'water_admin':      {'password': 'water123',      'department': 'water'},
    'education_admin':  {'password': 'education123',  'department': 'education'},
    'food_admin':       {'password': 'food123',       'department': 'food'},
    'employment_admin': {'password': 'employment123', 'department': 'employment'},
    'ngo_admin':        {'password': 'ngo123',        'department': 'ngo'},
    'admin':            {'password': 'admin123',      'department': 'admin'},
}

def make_token(username, department):
    try:
        import jwt
        return jwt.encode({
            'username':   username,
            'department': department,
            'exp':        datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
    except Exception:
        import base64
        payload = json.dumps({'username': username, 'department': department})
        return base64.b64encode(payload.encode()).decode()

def decode_token(token):
    try:
        import jwt
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except Exception:
        try:
            import base64
            payload = base64.b64decode(token.encode()).decode()
            return json.loads(payload)
        except Exception:
            return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token required'}), 401
        data = decode_token(token)
        if not data:
            return jsonify({'error': 'Invalid token'}), 401
        request.user = data
        return f(*args, **kwargs)
    return decorated

# ── login ─────────────────────────────────────────────────────────────────────
@dept_bp.route('/login', methods=['POST'])
def login():
    data     = request.get_json(force=True) or {}
    username = data.get('username', '')
    password = data.get('password', '')
    user     = DEMO_USERS.get(username)
    if user and user['password'] == password:
        dept  = user['department']
        token = make_token(username, dept)
        return jsonify({
            'token':      token,
            'department': dept,
            'label':      DEPARTMENTS[dept]['label'],
            'icon':       DEPARTMENTS[dept]['icon'],
            'color':      DEPARTMENTS[dept]['color'],
        })
    return jsonify({'error': 'Invalid credentials'}), 401

# ── list departments ──────────────────────────────────────────────────────────
@dept_bp.route('/list')
def list_departments():
    return jsonify({'departments': [
        {'id': k, 'label': v['label'], 'icon': v['icon'], 'color': v['color']}
        for k, v in DEPARTMENTS.items()
    ]})

# ── my reports ────────────────────────────────────────────────────────────────
@dept_bp.route('/my_reports')
@token_required
def my_reports():
    dept       = request.user.get('department', 'admin')
    issues     = DEPARTMENTS.get(dept, {}).get('issues', [])
    status_f   = request.args.get('status')
    urgency_f  = request.args.get('urgency')
    reports    = read_reports()

    filtered = [r for r in reports if r.get('issue') in issues]
    if status_f:  filtered = [r for r in filtered if r.get('status')  == status_f]
    if urgency_f: filtered = [r for r in filtered if r.get('urgency') == urgency_f]

    return jsonify({'reports': filtered, 'count': len(filtered), 'department': dept})

# ── stats ─────────────────────────────────────────────────────────────────────
@dept_bp.route('/stats')
@token_required
def dept_stats():
    dept     = request.user.get('department', 'admin')
    issues   = DEPARTMENTS.get(dept, {}).get('issues', [])
    reports  = read_reports()
    filtered = [r for r in reports if r.get('issue') in issues]

    today = datetime.now().date().isoformat()
    return jsonify({
        'total':        len(filtered),
        'pending':      sum(1 for r in filtered if r.get('status') == 'Submitted'),
        'acknowledged': sum(1 for r in filtered if r.get('status') == 'Acknowledged'),
        'in_progress':  sum(1 for r in filtered if r.get('status') == 'In Progress'),
        'resolved':     sum(1 for r in filtered if r.get('status') == 'Resolved'),
        'high_urgency': sum(1 for r in filtered if r.get('urgency') == 'High'),
        'today':        sum(1 for r in filtered if r.get('time', '').startswith(today)),
        'department':   dept,
        'label':        DEPARTMENTS.get(dept, {}).get('label', dept),
    })

# ── update status ─────────────────────────────────────────────────────────────
@dept_bp.route('/update_status/<report_id>', methods=['POST'])
@token_required
def update_status(report_id):
    data       = request.get_json(force=True) or {}
    new_status = data.get('status', 'Acknowledged')
    note       = data.get('note', '')
    dept       = request.user.get('department', 'admin')

    from data_handler import get_reports_file
    fp      = get_reports_file()
    reports = read_reports()
    updated = False

    for r in reports:
        if r.get('id') == report_id:
            r['status']     = new_status
            r['updated_at'] = datetime.now().isoformat()
            r['dept_note']  = note
            r['handled_by'] = dept
            updated = True
            break

    if updated:
        with open(fp, 'w', encoding='utf-8') as f:
            for r in reports:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Not found'}), 404
