"""
Advanced ML Engine for SWARABHARAT
- Predictive Analytics
- Trend Detection
- Priority Scoring
- Multi-language Support
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict
import json

# Multi-language keyword detection
LANGUAGE_PATTERNS = {
    'hindi': {
        'water': ['पानी', 'जल', 'पीने का पानी'],
        'health': ['अस्पताल', 'बीमार', 'डॉक्टर', 'दवा'],
        'emergency': ['आपातकाल', 'तुरंत', 'जल्दी', 'बचाओ'],
        'food': ['खाना', 'भोजन', 'भूख'],
        'education': ['स्कूल', 'शिक्षा', 'पढ़ाई']
    },
    'bengali': {
        'water': ['জল', 'পানি'],
        'health': ['হাসপাতাল', 'অসুস্থ', 'ডাক্তার'],
        'emergency': ['জরুরি', 'তাড়াতাড়ি']
    },
    'tamil': {
        'water': ['தண்ணீர்', 'நீர்'],
        'health': ['மருத்துவமனை', 'நோய்'],
        'emergency': ['அவசரம்', 'உடனடி']
    },
    'telugu': {
        'water': ['నీరు', 'నీటి'],
        'health': ['ఆసుపత్రి', 'అనారోగ్యం'],
        'emergency': ['అత్యవసరం', 'తక్షణం']
    }
}

def detect_language(text: str) -> str:
    """Detect language from text"""
    for lang, patterns in LANGUAGE_PATTERNS.items():
        for category, words in patterns.items():
            for word in words:
                if word in text:
                    return lang
    return 'english'

def calculate_priority_score(report: Dict) -> int:
    """Calculate priority score (0-100) based on multiple factors"""
    score = 50  # base
    
    # Urgency weight
    if report.get('urgency') == 'High':
        score += 30
    elif report.get('urgency') == 'Medium':
        score += 15
    
    # Issue type weight
    critical_issues = ['Health', 'Accident', 'Safety']
    if report.get('issue') in critical_issues:
        score += 20
    
    # Emotion weight
    if report.get('emotion') in ['Fear', 'Distress']:
        score += 10
    
    # Emergency contact provided
    if report.get('emergency'):
        score += 5
    
    # Location provided
    if report.get('location'):
        score += 5
    
    return min(100, max(0, score))

def detect_trends(reports: List[Dict], hours: int = 24) -> Dict:
    """Detect emerging trends in last N hours"""
    cutoff = datetime.now() - timedelta(hours=hours)
    recent = []
    
    for r in reports:
        try:
            report_time = datetime.fromisoformat(r.get('time', ''))
            if report_time >= cutoff:
                recent.append(r)
        except:
            continue
    
    if not recent:
        return {'trending_issues': [], 'hotspots': [], 'alert_level': 'normal'}
    
    # Issue frequency
    issues = Counter([r.get('issue', 'Other') for r in recent])
    trending = issues.most_common(3)
    
    # High urgency spike detection
    high_urgency_count = sum(1 for r in recent if r.get('urgency') == 'High')
    alert_level = 'critical' if high_urgency_count > len(recent) * 0.3 else 'normal'
    
    return {
        'trending_issues': [{'issue': i[0], 'count': i[1]} for i in trending],
        'total_recent': len(recent),
        'high_urgency_count': high_urgency_count,
        'alert_level': alert_level
    }

def predict_escalation(report: Dict, historical: List[Dict]) -> Dict:
    """Predict if issue will escalate based on patterns"""
    issue_type = report.get('issue', 'Other')
    
    # Find similar past issues
    similar = [r for r in historical if r.get('issue') == issue_type]
    
    if len(similar) < 5:
        return {'risk': 'unknown', 'confidence': 0}
    
    # Calculate escalation rate
    high_urgency = sum(1 for r in similar if r.get('urgency') == 'High')
    escalation_rate = high_urgency / len(similar)
    
    risk = 'high' if escalation_rate > 0.4 else 'medium' if escalation_rate > 0.2 else 'low'
    
    return {
        'risk': risk,
        'confidence': min(100, len(similar) * 2),
        'similar_cases': len(similar),
        'escalation_rate': round(escalation_rate * 100, 1)
    }

def generate_insights(reports: List[Dict]) -> Dict:
    """Generate actionable insights from all reports"""
    if not reports:
        return {}
    
    total = len(reports)
    
    # Issue distribution
    issues = Counter([r.get('issue', 'Other') for r in reports])
    
    # Emotion analysis
    emotions = Counter([r.get('emotion', 'Calm') for r in reports])
    
    # Urgency breakdown
    urgency = Counter([r.get('urgency', 'Medium') for r in reports])
    
    # Location coverage
    with_location = sum(1 for r in reports if r.get('location'))
    
    # Emergency contacts
    with_emergency = sum(1 for r in reports if r.get('emergency'))
    
    # Response time estimate (based on urgency)
    avg_response_time = {
        'High': '< 30 min',
        'Medium': '2-4 hours',
        'Low': '24-48 hours'
    }
    
    return {
        'total_reports': total,
        'top_issue': issues.most_common(1)[0][0] if issues else 'None',
        'dominant_emotion': emotions.most_common(1)[0][0] if emotions else 'Calm',
        'location_coverage': round(with_location / total * 100, 1) if total > 0 else 0,
        'emergency_contacts': with_emergency,
        'response_estimates': avg_response_time,
        'issue_breakdown': dict(issues),
        'emotion_breakdown': dict(emotions),
        'urgency_breakdown': dict(urgency)
    }

def smart_routing(report: Dict) -> Dict:
    """Route report to appropriate department with recommendations"""
    issue = report.get('issue', 'Other')
    urgency = report.get('urgency', 'Medium')
    location = report.get('location')
    
    # Department mapping
    departments = {
        'Water': 'Water Supply Department',
        'Health': 'Health & Medical Services',
        'Food': 'Food & Civil Supplies',
        'Education': 'Education Department',
        'Safety': 'Police & Public Safety',
        'Employment': 'Labour & Employment',
        'Accident': 'Emergency Services',
        'Other': 'General Administration'
    }
    
    # Action recommendations
    actions = {
        'Health': ['Dispatch ambulance', 'Alert nearest hospital', 'Notify medical officer'],
        'Accident': ['Alert emergency services', 'Dispatch police', 'Medical assistance'],
        'Water': ['Inspect supply line', 'Deploy water tanker', 'Check quality'],
        'Safety': ['Increase patrol', 'Install lighting', 'Community alert'],
        'Food': ['Verify supply chain', 'Distribute rations', 'Check PDS'],
        'Education': ['Teacher deployment', 'Infrastructure check', 'Student welfare'],
        'Employment': ['Job fair notification', 'Skill training', 'NREGA enrollment']
    }
    
    priority = calculate_priority_score(report)
    
    return {
        'department': departments.get(issue, 'General Administration'),
        'priority_score': priority,
        'recommended_actions': actions.get(issue, ['Review and assess']),
        'response_time': '< 30 min' if urgency == 'High' else '2-4 hours' if urgency == 'Medium' else '24-48 hours',
        'requires_location': issue in ['Health', 'Accident', 'Safety'],
        'has_location': bool(location)
    }


def explain_priority(report: Dict) -> Dict:
    """Return a breakdown of how the priority score was calculated."""
    base = 50
    details = []
    score = base

    # Urgency weight
    if report.get('urgency') == 'High':
        details.append({'factor': 'urgency', 'value': 'High', 'points': 30})
        score += 30
    elif report.get('urgency') == 'Medium':
        details.append({'factor': 'urgency', 'value': 'Medium', 'points': 15})
        score += 15
    else:
        details.append({'factor': 'urgency', 'value': 'Low', 'points': 0})

    # Issue type weight
    critical_issues = ['Health', 'Accident', 'Safety']
    if report.get('issue') in critical_issues:
        details.append({'factor': 'issue_type', 'value': report.get('issue'), 'points': 20})
        score += 20
    else:
        details.append({'factor': 'issue_type', 'value': report.get('issue', 'Other'), 'points': 0})

    # Emotion
    if report.get('emotion') in ['Fear', 'Distress']:
        details.append({'factor': 'emotion', 'value': report.get('emotion'), 'points': 10})
        score += 10
    else:
        details.append({'factor': 'emotion', 'value': report.get('emotion', 'Calm'), 'points': 0})

    # Emergency contact
    if report.get('emergency'):
        details.append({'factor': 'emergency_contact', 'value': True, 'points': 5})
        score += 5
    else:
        details.append({'factor': 'emergency_contact', 'value': False, 'points': 0})

    # Location
    if report.get('location'):
        details.append({'factor': 'location', 'value': True, 'points': 5})
        score += 5
    else:
        details.append({'factor': 'location', 'value': False, 'points': 0})

    return {
        'base_score': base,
        'final_score': min(100, score),
        'details': details
    }
