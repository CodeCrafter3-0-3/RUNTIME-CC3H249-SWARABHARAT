import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/swarabharat')

def create_tables():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id VARCHAR(50) PRIMARY KEY,
            message TEXT NOT NULL,
            issue VARCHAR(50),
            emotion VARCHAR(50),
            urgency VARCHAR(20),
            summary TEXT,
            location VARCHAR(200),
            emergency VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Submitted',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_urgency ON reports(urgency);
        CREATE INDEX IF NOT EXISTS idx_issue ON reports(issue);
        CREATE INDEX IF NOT EXISTS idx_created ON reports(created_at);
        CREATE INDEX IF NOT EXISTS idx_status ON reports(status);
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            department VARCHAR(100),
            role VARCHAR(50) DEFAULT 'officer',
            created_at TIMESTAMP DEFAULT NOW()
        );
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tables created")

def migrate_from_json():
    from data_handler import read_reports
    
    reports = read_reports()
    if not reports:
        print("No reports to migrate")
        return
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    for r in reports:
        cur.execute('''
            INSERT INTO reports (id, message, issue, emotion, urgency, summary, location, emergency, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', (
            r.get('id'),
            r.get('message'),
            r.get('issue'),
            r.get('emotion'),
            r.get('urgency'),
            r.get('summary'),
            r.get('location'),
            r.get('emergency'),
            r.get('status', 'Submitted'),
            r.get('time', datetime.now().isoformat())
        ))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Migrated {len(reports)} reports")

if __name__ == '__main__':
    create_tables()
    migrate_from_json()
