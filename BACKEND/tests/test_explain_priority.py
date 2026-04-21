def test_explain_priority_endpoint(client, tmp_path, monkeypatch):
    temp_file = tmp_path / 'reports_explain.json'
    monkeypatch.setenv('REPORTS_FILE', str(temp_file))

    from data_handler import save_report
    analysis = {'issue': 'Health', 'emotion': 'Fear', 'urgency': 'High', 'summary': 'Serious medical need'}
    rid = save_report(analysis, message='Hospital has no staff', location=None, emergency='')

    rv = client.get(f'/analytics/explain_priority?report_id={rid}')
    assert rv.status_code == 200
    d = rv.get_json()
    assert d.get('status') == 'success'
    assert 'explanation' in d
    ex = d['explanation']
    assert ex['final_score'] >= ex['base_score']
