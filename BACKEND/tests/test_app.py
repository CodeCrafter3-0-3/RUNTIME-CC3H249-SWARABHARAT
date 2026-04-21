import json
import os
import pytest

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'ok'


def test_submit_and_dashboard(client, tmp_path, monkeypatch):
    # Use temp file for reports via env var
    temp_file = tmp_path / "reports_test.json"
    monkeypatch.setenv('REPORTS_FILE', str(temp_file))

    # POST submit
    rv = client.post('/submit', json={'issue': 'Test issue for pytest'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'success'
    assert 'analysis' in data

    # Dashboard should return counts
    rv2 = client.get('/dashboard')
    assert rv2.status_code == 200
    d2 = rv2.get_json()
    assert 'totalVoices' in d2
    assert isinstance(d2['totalVoices'], int)


def test_demo_models(client):
    rv = client.get('/demo_models')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'success'
    assert isinstance(data['models'], list)
    assert any(m.get('id') == 'heuristic' for m in data['models'])


def test_demo_analyze_with_model_hint(client):
    rv = client.post('/demo_analyze', json={
        'message': 'There is no water supply in our area for 2 days',
        'model': 'heuristic'
    })
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'success'
    assert 'analysis' in data
    assert data['analysis']['model'] == 'heuristic'


def test_submit_with_location_object(client, tmp_path, monkeypatch):
    temp_file = tmp_path / "reports_location_test.json"
    monkeypatch.setenv('REPORTS_FILE', str(temp_file))

    rv = client.post('/submit', json={
        'issue': 'Need urgent medical help for accident victim',
        'location': {
            'latitude': 30.8193,
            'longitude': 75.5559
        },
        'emergency': '+919876543210'
    })

    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'success'
    assert data.get('report_id')
