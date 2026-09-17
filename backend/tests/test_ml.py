from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.models import MLPrediction
from datetime import datetime, timezone

client = TestClient(app)

def test_ml_prediction_endpoint_not_found():
    response = client.get('/ml/prediction/pr/999')
    assert response.status_code == 404
