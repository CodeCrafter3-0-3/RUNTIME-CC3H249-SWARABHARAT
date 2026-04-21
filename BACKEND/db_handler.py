import psycopg2
from psycopg2.extras import RealDictCursor
import os
import uuid
from datetime import datetime

USE_DB = os.getenv('USE_DATABASE', 'false').lower() == 'true'
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db():
    if USE_DB and DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return None

def save_report_db(analysis, message, location=None, emergency=None):
    conn = get_db()
    if not conn:
        from data_handler import save_report
        return save_report(analysis, message, location, emergency)
    
    report_id = str(uuid.uuid4())[:8]
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO reports (id, message, issue, emotion, urgency, summary, location, emergency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (
        report_id,
        message,
        analysis.get('issue'),
        analysis.get('emotion'),
        analysis.get('urgency'),
        analysis.get('summary'),
        location,
        emergency
    ))
    
    conn.commit()
    cur.close()
    conn.close()
    return report_id

def read_reports_db():
    conn = get_db()
    if not conn:
        from data_handler import read_reports
        return read_reports()
    
    cur = conn.cursor()
    cur.execute('SELECT * FROM reports ORDER BY created_at DESC LIMIT 1000')
    reports = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(r) for r in reports]

def update_report_status_db(report_id, status):
    conn = get_db()
    if not conn:
        return False
    
    cur = conn.cursor()
    cur.execute('''
        UPDATE reports SET status = %s, updated_at = NOW()
        WHERE id = %s
    ''', (status, report_id))
    
    updated = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return updated
