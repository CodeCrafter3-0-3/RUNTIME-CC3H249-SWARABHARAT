def test_index_status_endpoint(client, tmp_path, monkeypatch):
    temp_reports = tmp_path / 'reports_idx.json'
    monkeypatch.setenv('REPORTS_FILE', str(temp_reports))

    from data_handler import save_report
    analysis = {'issue': 'Water', 'emotion': 'Distress', 'urgency': 'High', 'summary': 'No water supply'}
    save_report(analysis, message='No water in area', location=None, emergency='')

    rv = client.post('/ai/build_index')
    assert rv.status_code == 200
    d = rv.get_json()
    assert d.get('status') == 'success'
    assert 'last_built' in d

    rv2 = client.get('/ai/index_status')
    assert rv2.status_code == 200
    d2 = rv2.get_json()
    assert d2.get('status') == 'success'
    assert d2.get('index_status', {}).get('last_built') is not None
