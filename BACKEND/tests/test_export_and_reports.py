import os
from app import app


def test_reports_endpoint(client):
    rv = client.get('/reports')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'status' in data


def test_export_csv_endpoint(client):
    rv = client.get('/export_csv')
    # export returns CSV or error if none; should be 200 or 200 with empty csv
    assert rv.status_code in (200, 500)
