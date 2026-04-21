from datetime import datetime
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging
from io import StringIO
import time
from functools import wraps

load_dotenv()

# ── safe local imports ──────────────────────────────────────────────────────
from ai_engine import analyze_issue, AI_PROVIDER, OPENAI_API_KEY, HUGGINGFACE_API_KEY
from telemetry import increment as telemetry_increment, get_metrics_text
from data_handler import save_report, read_reports
from ml_engine import calculate_priority_score, detect_trends, predict_escalation, generate_insights, smart_routing, explain_priority
from advanced_ai import generate_ai_insights, analyze_report_with_ai, IssuePredictor, AnomalyDetector, PatternRecognizer, RecommendationEngine
from nlp_engine import nlp_engine
from forecasting_engine import forecaster
from clustering_engine import clustering_engine
from monitoring import monitor
from department_portal import dept_bp

try:
    from embeddings import find_similar
    from embeddings_store import build_and_save_index, search_index, get_index_status
    _HAS_EMBEDDINGS = True
except Exception:
    _HAS_EMBEDDINGS = False

try:
    from heatmap_generator import generate_heatmap_data, get_hotspots
    _HAS_HEATMAP = True
except Exception:
    _HAS_HEATMAP = False

try:
    from translation import translate_text, detect_language as detect_lang
    _HAS_TRANSLATION = True
except Exception:
    _HAS_TRANSLATION = False

try:
    from vision_engine import analyze_image, verify_authenticity
    _HAS_VISION = True
except Exception:
    _HAS_VISION = False

try:
    from security import sanitize_input, rate_limit_strict, validate_phone
    _HAS_SECURITY = True
except Exception:
    _HAS_SECURITY = False
    def sanitize_input(x): return x
    def validate_phone(x): return True
    def rate_limit_strict(**kw):
        def dec(f): return f
        return dec

# ── app setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.register_blueprint(dept_bp, url_prefix='/department')

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger('swara')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

@app.before_request
def _inc():
    try: telemetry_increment('total_requests', 1)
    except: pass

# ── rate limiter ─────────────────────────────────────────────────────────────
_RATE_STORE = {}
RATE_LIMIT  = int(os.getenv('RATE_LIMIT', '60'))
RATE_WINDOW = int(os.getenv('RATE_WINDOW', '60'))

def rate_limited(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            ip  = request.remote_addr or 'local'
            now = int(time.time())
            e   = _RATE_STORE.get(ip, {'count': 0, 'reset': now + RATE_WINDOW})
            if now > e['reset']:
                e = {'count': 0, 'reset': now + RATE_WINDOW}
            e['count'] += 1
            _RATE_STORE[ip] = e
            if e['count'] > RATE_LIMIT:
                return jsonify({'status': 'error', 'message': 'Too many requests'}), 429
        except: pass
        return f(*args, **kwargs)
    return wrapper

# ═══════════════════════════════════════════════════════════════════════════
# CORE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    return jsonify({'status': 'ok', 'message': 'SwaraBharat Backend Live 🚀'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'SwaraBharat backend running'})

# ── submit ───────────────────────────────────────────────────────────────────
@app.route('/submit', methods=['POST'])
@rate_limit_strict(max_requests=10, window=60)
def submit():
    try:
        data = request.get_json(silent=True) or {}
        message   = sanitize_input((data.get('issue') or '').strip())
        emergency = sanitize_input((data.get('emergency') or '').strip())
        photo     = data.get('photo')          # base64 string, optional

        # location validation
        raw_loc  = data.get('location')
        location = None
        if isinstance(raw_loc, dict):
            try:
                lat = float(raw_loc['latitude'])
                lng = float(raw_loc['longitude'])
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    location = {'latitude': lat, 'longitude': lng}
            except: pass
        elif isinstance(raw_loc, str):
            location = sanitize_input(raw_loc[:200])

        if len(message) < 3:
            return jsonify({'status': 'error', 'message': 'Too short'}), 400
        if len(message) > 2000:
            return jsonify({'status': 'error', 'message': 'Too long'}), 400

        # AI analysis
        analysis = analyze_issue(message)

        # image analysis if photo provided
        image_analysis = None
        if photo and _HAS_VISION:
            try: image_analysis = analyze_image(photo)
            except: pass

        report_id = save_report(analysis, message, location, emergency, photo=photo)

        return jsonify({
            'status': 'success',
            'analysis': analysis,
            'report_id': report_id,
            'image_analysis': image_analysis
        })
    except Exception:
        logger.exception('Submit error')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ── dashboard ────────────────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    try:
        reports = read_reports()
        issue_count   = {}
        emotion_count = {}
        for r in reports:
            i = r.get('issue', 'Other');  issue_count[i]   = issue_count.get(i, 0) + 1
            e = r.get('emotion', 'Calm'); emotion_count[e] = emotion_count.get(e, 0) + 1
        return jsonify({
            'totalVoices': len(reports),
            'highUrgency': sum(1 for r in reports if r.get('urgency') == 'High'),
            'topIssue':    max(issue_count, key=issue_count.get) if issue_count else '-',
            'issues':      issue_count,
            'emotions':    emotion_count
        })
    except Exception:
        logger.exception('Dashboard error')
        return jsonify({'totalVoices': 0, 'highUrgency': 0, 'topIssue': '-', 'issues': {}, 'emotions': {}}), 500

# ── reports ──────────────────────────────────────────────────────────────────
@app.route('/reports')
def reports_endpoint():
    try:
        dept   = request.args.get('department')
        status = request.args.get('status')
        reps   = read_reports()

        # department filter maps issue types
        DEPT_MAP = {
            'health':      ['Health'],
            'police':      ['Safety', 'Accident'],
            'fire':        ['Accident', 'Safety'],
            'water':       ['Water'],
            'education':   ['Education'],
            'food':        ['Food'],
            'employment':  ['Employment'],
            'hospital':    ['Health'],
            'ambulance':   ['Health', 'Accident'],
            'ngo':         ['Food', 'Water', 'Health', 'Education'],
        }
        if dept and dept in DEPT_MAP:
            reps = [r for r in reps if r.get('issue') in DEPT_MAP[dept]]
        if status:
            reps = [r for r in reps if r.get('status') == status]

        return jsonify({'status': 'success', 'reports': reps})
    except Exception:
        logger.exception('Reports error')
        return jsonify({'status': 'error', 'reports': []}), 500

# ── update status ─────────────────────────────────────────────────────────────
@app.route('/update_status/<report_id>', methods=['POST'])
def update_status(report_id):
    try:
        data       = request.get_json(force=True) or {}
        new_status = data.get('status', 'Submitted')
        dept_note  = data.get('note', '')
        reports    = read_reports()
        updated    = False
        for r in reports:
            if r.get('id') == report_id:
                r['status']     = new_status
                r['updated_at'] = datetime.now().isoformat()
                if dept_note:
                    r['dept_note'] = dept_note
                updated = True
                break
        if updated:
            fp = os.path.join(DATA_DIR, 'reports.json')
            with open(fp, 'w', encoding='utf-8') as f:
                for r in reports:
                    f.write(json.dumps(r, ensure_ascii=False) + '\n')
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Not found'}), 404
    except Exception:
        logger.exception('Update status error')
        return jsonify({'status': 'error'}), 500

# ── export csv ────────────────────────────────────────────────────────────────
@app.route('/export_csv')
def export_csv():
    try:
        reports = read_reports()
        out = StringIO()
        out.write('ID,Time,Message,Issue,Emotion,Urgency,Status,Location,Emergency,Summary\n')
        for r in reports:
            loc = ''
            if isinstance(r.get('location'), dict):
                loc = f"{r['location'].get('latitude','')},{r['location'].get('longitude','')}"
            elif r.get('location'):
                loc = str(r['location'])
            summary = (r.get('summary') or '').replace('"', '""')
            message = (r.get('message') or '').replace('"', '""')
            out.write(f'"{r.get("id","")}","{r.get("time","")}","{message}","{r.get("issue","")}","{r.get("emotion","")}","{r.get("urgency","")}","{r.get("status","")}","{loc}","{r.get("emergency","")}","{summary}"\n')
        resp = app.response_class(out.getvalue(), mimetype='text/csv')
        resp.headers.set('Content-Disposition', 'attachment', filename='swara_reports.csv')
        return resp
    except Exception:
        logger.exception('Export CSV error')
        return jsonify({'status': 'error'}), 500

# ═══════════════════════════════════════════════════════════════════════════
# AI / DEMO ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/demo_analyze', methods=['POST'])
def demo_analyze():
    try:
        data    = request.get_json(force=True) or {}
        message = (data.get('message') or '').strip()
        if not message:
            return jsonify({'status': 'error', 'message': 'No message'}), 400
        analysis = analyze_issue(message)
        # also run NLP
        sentiment = nlp_engine.sentiment_analysis(message)
        keywords  = nlp_engine.keyword_extraction(message)
        return jsonify({'status': 'success', 'analysis': analysis, 'sentiment': sentiment, 'keywords': keywords})
    except Exception:
        logger.exception('Demo analyze error')
        return jsonify({'status': 'error'}), 500

@app.route('/demo_status')
def demo_status():
    try:
        return jsonify({
            'status': 'success',
            'ai_provider':        AI_PROVIDER,
            'has_openai_key':     bool(OPENAI_API_KEY),
            'has_huggingface_key': bool(HUGGINGFACE_API_KEY),
            'ai_live':            bool(OPENAI_API_KEY or HUGGINGFACE_API_KEY)
        })
    except Exception:
        return jsonify({'status': 'error', 'has_openai_key': False, 'ai_live': False}), 500

@app.route('/demo_quota')
def demo_quota():
    try:
        from ai_engine import get_quota_status
        return jsonify({'status': 'success', 'quota': get_quota_status()})
    except Exception:
        return jsonify({'status': 'error', 'quota': {}}), 500

@app.route('/demo_examples')
def demo_examples():
    samples = [
        'There is no clean drinking water in our neighbourhood for weeks.',
        'The primary school has no teacher and my child cannot study.',
        'Heavy traffic and no street lights, we fear for safety at night.',
        "Local hospital doesn't have basic medicines and staff.",
        'I lost my job and there are no local opportunities.',
        'There was a major road accident near the highway, people are injured.',
        'Our area has no food supply, children are starving.',
    ]
    examples = []
    for s in samples:
        try:    a = analyze_issue(s)
        except: a = {'issue': 'Other', 'emotion': 'Calm', 'urgency': 'Medium', 'summary': 'Analysis unavailable.'}
        examples.append({'message': s, 'analysis': a})
    return jsonify({'status': 'success', 'examples': examples})

# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/analytics/trends')
def analytics_trends():
    try:
        reports = read_reports()
        hours   = int(request.args.get('hours', 24))
        return jsonify({'status': 'success', 'trends': detect_trends(reports, hours)})
    except Exception:
        logger.exception('Trends error')
        return jsonify({'status': 'error'}), 500

@app.route('/analytics/insights')
def analytics_insights():
    try:
        return jsonify({'status': 'success', 'insights': generate_insights(read_reports())})
    except Exception:
        logger.exception('Insights error')
        return jsonify({'status': 'error'}), 500

@app.route('/analytics/predict', methods=['POST'])
def analytics_predict():
    try:
        data    = request.get_json(force=True) or {}
        report  = data.get('report', {})
        reports = read_reports()
        return jsonify({'status': 'success', 'prediction': predict_escalation(report, reports)})
    except Exception:
        logger.exception('Predict error')
        return jsonify({'status': 'error'}), 500

@app.route('/analytics/route', methods=['POST'])
def analytics_route():
    try:
        data   = request.get_json(force=True) or {}
        report = data.get('report', {})
        return jsonify({'status': 'success', 'routing': smart_routing(report)})
    except Exception:
        logger.exception('Route error')
        return jsonify({'status': 'error'}), 500

@app.route('/analytics/explain_priority')
def analytics_explain_priority():
    try:
        rid     = request.args.get('report_id')
        if not rid:
            return jsonify({'status': 'error', 'message': 'report_id required'}), 400
        reports = read_reports()
        report  = next((r for r in reports if r.get('id') == rid), None)
        if not report:
            return jsonify({'status': 'error', 'message': 'not found'}), 404
        return jsonify({'status': 'success', 'explanation': explain_priority(report)})
    except Exception:
        logger.exception('Explain priority error')
        return jsonify({'status': 'error'}), 500

@app.route('/analytics/priority')
def analytics_priority():
    try:
        import statistics
        reports = read_reports()
        scores  = [calculate_priority_score(r) for r in reports]
        if not scores:
            return jsonify({'status': 'success', 'count': 0, 'average': 0, 'distribution': {}})
        dist = {'low': 0, 'medium': 0, 'high': 0}
        for s in scores:
            if s >= 75:   dist['high']   += 1
            elif s >= 40: dist['medium'] += 1
            else:         dist['low']    += 1
        return jsonify({'status': 'success', 'count': len(scores), 'average': round(statistics.mean(scores), 1), 'distribution': dist})
    except Exception:
        logger.exception('Priority error')
        return jsonify({'status': 'error'}), 500

# ═══════════════════════════════════════════════════════════════════════════
# AI ADVANCED ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/ai/insights')
def ai_insights():
    try:
        return jsonify({'status': 'success', 'insights': generate_ai_insights(read_reports())})
    except Exception:
        logger.exception('AI insights error')
        return jsonify({'status': 'error'}), 500

@app.route('/ai/predictions')
def ai_predictions():
    try:
        return jsonify({'status': 'success', 'predictions': IssuePredictor().predict_next_24h(read_reports())})
    except Exception:
        logger.exception('Predictions error')
        return jsonify({'status': 'error'}), 500

@app.route('/ai/anomalies')
def ai_anomalies():
    try:
        return jsonify({'status': 'success', 'anomalies': AnomalyDetector().detect_anomalies(read_reports())})
    except Exception:
        logger.exception('Anomalies error')
        return jsonify({'status': 'error'}), 500

@app.route('/ai/patterns')
def ai_patterns():
    try:
        return jsonify({'status': 'success', 'patterns': PatternRecognizer().find_recurring_issues(read_reports())})
    except Exception:
        logger.exception('Patterns error')
        return jsonify({'status': 'error'}), 500

@app.route('/ai/analyze_report/<report_id>')
def ai_analyze_report(report_id):
    try:
        reports = read_reports()
        report  = next((r for r in reports if r.get('id') == report_id), None)
        if not report:
            return jsonify({'status': 'error', 'message': 'Not found'}), 404
        return jsonify({'status': 'success', 'analysis': analyze_report_with_ai(report, reports)})
    except Exception:
        logger.exception('AI analyze report error')
        return jsonify({'status': 'error'}), 500

@app.route('/ai/recommendations/<report_id>')
def ai_recommendations(report_id):
    try:
        reports = read_reports()
        report  = next((r for r in reports if r.get('id') == report_id), None)
        if not report:
            return jsonify({'status': 'error', 'message': 'Not found'}), 404
        return jsonify({'status': 'success', 'recommendations': RecommendationEngine().recommend_actions(report, reports)})
    except Exception:
        logger.exception('Recommendations error')
        return jsonify({'status': 'error'}), 500

@app.route('/ai/search_similar', methods=['POST'])
def ai_search_similar():
    try:
        data    = request.get_json(force=True) or {}
        text    = data.get('text', '')
        top_n   = int(data.get('top_n', 5))
        reports = read_reports()
        if _HAS_EMBEDDINGS:
            try:
                idx = search_index(text, top_n=top_n)
                if idx:
                    rm = {r.get('id'): r for r in reports}
                    results = [{'id': x.get('id'), 'score': x.get('score'), 'report': rm.get(x.get('id'), {})} for x in idx]
                    return jsonify({'status': 'success', 'results': results})
            except: pass
            results = find_similar(text, reports, top_n=top_n)
        else:
            results = []
        return jsonify({'status': 'success', 'results': results})
    except Exception:
        logger.exception('Search similar error')
        return jsonify({'status': 'error', 'results': []}), 500

@app.route('/ai/build_index', methods=['POST'])
def ai_build_index():
    try:
        if not _HAS_EMBEDDINGS:
            return jsonify({'status': 'error', 'message': 'Embeddings not available'}), 500
        return jsonify(build_and_save_index(read_reports()))
    except Exception:
        logger.exception('Build index error')
        return jsonify({'status': 'error'}), 500

@app.route('/ai/index_status')
def ai_index_status():
    try:
        if not _HAS_EMBEDDINGS:
            return jsonify({'status': 'success', 'index_status': {'count': 0, 'last_built': None}})
        return jsonify({'status': 'success', 'index_status': get_index_status()})
    except Exception:
        return jsonify({'status': 'error', 'index_status': {}}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ML ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/ml/nlp_analysis', methods=['POST'])
def nlp_analysis():
    try:
        data = request.get_json(force=True) or {}
        text = data.get('text', '')
        return jsonify({
            'status':     'success',
            'sentiment':  nlp_engine.sentiment_analysis(text),
            'entities':   nlp_engine.extract_entities(text),
            'keywords':   nlp_engine.keyword_extraction(text),
            'complexity': nlp_engine.text_complexity(text)
        })
    except Exception:
        logger.exception('NLP analysis error')
        return jsonify({'status': 'error'}), 500

@app.route('/ml/forecast')
def forecast():
    try:
        reports = read_reports()
        return jsonify({
            'status':       'success',
            'forecast':     forecaster.forecast_next_week(reports),
            'seasonality':  forecaster.detect_seasonality(reports),
            'velocity':     forecaster.calculate_velocity(reports)
        })
    except Exception:
        logger.exception('Forecast error')
        return jsonify({'status': 'error'}), 500

@app.route('/ml/clusters')
def ml_clusters():
    try:
        reports = read_reports()
        return jsonify({
            'status':               'success',
            'similarity_clusters':  clustering_engine.cluster_by_similarity(reports)[:10],
            'geographic_clusters':  clustering_engine.geographic_clustering(reports)[:10],
            'outliers':             clustering_engine.find_outliers(reports)
        })
    except Exception:
        logger.exception('Clusters error')
        return jsonify({'status': 'error'}), 500

# ═══════════════════════════════════════════════════════════════════════════
# HEATMAP / TRANSLATION / VISION / MONITORING
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/heatmap')
def heatmap():
    try:
        if not _HAS_HEATMAP:
            return jsonify({'status': 'error', 'message': 'Heatmap not available'}), 500
        return jsonify({'status': 'success', 'heatmap': generate_heatmap_data()})
    except Exception:
        return jsonify({'status': 'error'}), 500

@app.route('/hotspots')
def hotspots():
    try:
        if not _HAS_HEATMAP:
            return jsonify({'status': 'error'}), 500
        threshold = int(request.args.get('threshold', 5))
        return jsonify({'status': 'success', 'hotspots': get_hotspots(threshold)})
    except Exception:
        return jsonify({'status': 'error'}), 500

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data   = request.get_json(force=True) or {}
        text   = data.get('text', '')
        target = data.get('target', 'en')
        if not _HAS_TRANSLATION:
            return jsonify({'status': 'success', 'translated': text, 'detected_language': 'en'})
        return jsonify({'status': 'success', 'translated': translate_text(text, target), 'detected_language': detect_lang(text)})
    except Exception:
        return jsonify({'status': 'error'}), 500

@app.route('/analyze_image', methods=['POST'])
def analyze_image_route():
    try:
        data       = request.get_json(force=True) or {}
        image_data = data.get('image')
        if not image_data:
            return jsonify({'status': 'error', 'message': 'No image'}), 400
        if not _HAS_VISION:
            return jsonify({'status': 'error', 'message': 'Vision not available'}), 500
        return jsonify({'status': 'success', 'analysis': analyze_image(image_data), 'authentic': verify_authenticity(image_data)})
    except Exception:
        return jsonify({'status': 'error'}), 500

@app.route('/monitoring/health')
def health_check():
    try:
        return jsonify({'status': 'success', 'health': monitor.get_health_status()})
    except Exception:
        return jsonify({'status': 'error'}), 500

@app.route('/metrics')
def metrics():
    try:
        return app.response_class(get_metrics_text(), mimetype='text/plain; version=0.0.4')
    except Exception:
        return app.response_class('# error\n', mimetype='text/plain'), 500

@app.route('/stats')
def stats():
    try:
        since   = request.args.get('since')
        reports = read_reports()
        if since:
            try:
                since_dt = datetime.fromisoformat(since)
                reports  = [r for r in reports if datetime.fromisoformat(r.get('time', '')) >= since_dt]
            except: pass
        issues = {}
        for r in reports:
            issues[r.get('issue', 'Other')] = issues.get(r.get('issue', 'Other'), 0) + 1
        return jsonify({'status': 'success', 'totalVoices': len(reports), 'highUrgency': sum(1 for r in reports if r.get('urgency') == 'High'), 'issues': issues})
    except Exception:
        logger.exception('Stats error')
        return jsonify({'status': 'error'}), 500

# ── run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port  = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=port, debug=debug)
