from unittest.mock import patch
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_feedback_correct():
    with patch("src.main.record_feedback", return_value=True) as record:
        response = client.post("/feedback", json={"correct": True, "predicted_animal": "dog", "actual_animal": "dog"})
        assert response.status_code == 200
        record.assert_called_once_with(True)


def test_feedback_incorrect():
    with patch("src.main.record_feedback", return_value=True) as record:
        response = client.post("/feedback", json={"correct": False, "predicted_animal": "horse", "actual_animal": "other"})
        assert response.status_code == 200
        record.assert_called_once_with(False)


def test_feedback_inconsistent():
    with patch("src.main.record_feedback") as record:
        response = client.post("/feedback", json={"correct": True, "predicted_animal": "dog", "actual_animal": "cat"})
        assert response.status_code == 400
        record.assert_not_called()


def test_feedback_publish_failure():
    with patch("src.main.record_feedback", return_value=False):
        response = client.post("/feedback", json={"correct": False, "predicted_animal": "dog", "actual_animal": "cat"})
        assert response.status_code == 503


def test_feedback_invalid_category():
    with patch("src.main.record_feedback") as record:
        response = client.post("/feedback", json={"correct": False, "predicted_animal": "invalid", "actual_animal": "cat"})
        assert response.status_code == 422
        record.assert_not_called()
