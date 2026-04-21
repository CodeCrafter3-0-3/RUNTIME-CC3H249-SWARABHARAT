import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from nlp_engine import nlp_engine
from forecasting_engine import forecaster
from clustering_engine import clustering_engine
from security import hash_password, verify_password, sanitize_input

def test_nlp_sentiment():
    result = nlp_engine.sentiment_analysis("This is terrible and awful")
    assert result['sentiment'] == 'negative'
    assert result['confidence'] > 0

def test_nlp_entities():
    text = "Call me at 9876543210 in Delhi"
    entities = nlp_engine.extract_entities(text)
    assert len(entities['contacts']) > 0
    assert len(entities['locations']) > 0

def test_nlp_keywords():
    keywords = nlp_engine.keyword_extraction("water supply problem water shortage")
    assert 'water' in keywords

def test_forecasting():
    reports = [{'time': '2026-01-01T10:00:00'} for _ in range(10)]
    result = forecaster.forecast_next_week(reports)
    assert 'forecast' in result

def test_clustering():
    reports = [
        {'issue': 'Water', 'location': 'Delhi', 'urgency': 'High'},
        {'issue': 'Water', 'location': 'Delhi', 'urgency': 'High'},
        {'issue': 'Health', 'location': 'Mumbai', 'urgency': 'Low'}
    ]
    clusters = clustering_engine.cluster_by_similarity(reports)
    assert len(clusters) > 0

def test_password_hashing():
    password = "test123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_input_sanitization():
    dirty = "<script>alert('xss')</script>Hello"
    clean = sanitize_input(dirty)
    assert '<script>' not in clean

def test_geographic_clustering():
    reports = [
        {'issue': 'Water', 'location': 'Delhi'},
        {'issue': 'Water', 'location': 'Delhi'},
        {'issue': 'Water', 'location': 'Delhi'},
        {'issue': 'Health', 'location': 'Mumbai'}
    ]
    clusters = clustering_engine.geographic_clustering(reports)
    assert len(clusters) > 0
    assert clusters[0]['location'] == 'Delhi'

def test_text_complexity():
    simple = "I need water"
    complex_text = "The infrastructure deterioration necessitates immediate intervention"
    
    result1 = nlp_engine.text_complexity(simple)
    result2 = nlp_engine.text_complexity(complex_text)
    
    assert result1['complexity'] == 'simple'
    assert result2['avg_word_length'] > result1['avg_word_length']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
