import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from local_app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert rv.json['status'] == 'ok'

def test_sample_endpoint(client):
    rv = client.get('/api/sample')
    assert rv.status_code == 200
    assert 'tenure' in rv.json
    assert rv.json['tenure'] == 12

def test_predict_endpoint_missing_body(client):
    rv = client.post('/api/predict')
    assert rv.status_code == 400

def test_predict_endpoint_valid(client):
    # Get sample data
    sample_data = client.get('/api/sample').json
    # Send it to predict
    rv = client.post('/api/predict', json=sample_data)
    assert rv.status_code == 200
    assert 'churn' in rv.json
    assert 'probability' in rv.json
    assert 'risk_level' in rv.json
    assert 'top_features' in rv.json
