import json

def test_build_index_and_search(client, monkeypatch, tmp_path):
    # Ensure a clean REPORTS_FILE pointing to temp file
    temp_reports = tmp_path / 'reports_test.json'
    monkeypatch.setenv('REPORTS_FILE', str(temp_reports))

    # Create two reports
    from data_handler import save_report
    analysis = {'issue': 'Water', 'emotion': 'Distress', 'urgency': 'High', 'summary': 'No water in area'}
    save_report(analysis, message='There is no water supply for days in my locality', location=None, emergency='')
    analysis2 = {'issue': 'Health', 'emotion': 'Fear', 'urgency': 'High', 'summary': 'Hospital short of medicines'}
    save_report(analysis2, message='Local hospital has no medicines and staff', location=None, emergency='')

    # Build index via endpoint
    rv = client.post('/ai/build_index')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get('status') == 'success'

    # Search similar
    rv2 = client.post('/ai/search_similar', json={'text': 'no water supply', 'top_n': 2})
    assert rv2.status_code == 200
    d2 = rv2.get_json()
    assert d2.get('status') == 'success'
    assert isinstance(d2.get('results'), list)
