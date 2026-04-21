import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with patch("redis.Redis") as mock_redis_cls:
    mock_redis_cls.return_value = MagicMock()
    from main import app, r


@pytest.fixture(autouse=True)
def reset_redis():
    r.reset_mock()


client = TestClient(app)


def test_health_returns_ok():
    """Health endpoint returns 200 and status ok when Redis is reachable."""
    r.ping.return_value = True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_job_returns_job_id():
    """POST /jobs pushes to queue, sets status, returns a UUID job_id."""
    r.lpush.return_value = 1
    r.hset.return_value = 1
    response = client.post("/jobs")
    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert len(body["job_id"]) == 36


def test_get_job_returns_queued_status():
    """GET /jobs/{id} returns the job status correctly."""
    r.hget.return_value = b"queued"
    response = client.get("/jobs/test-job-id-123")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    r.hget.assert_called_once_with("job:test-job-id-123", "status")


def test_get_job_returns_completed_status():
    """GET /jobs/{id} returns completed status correctly."""
    r.hget.return_value = b"completed"
    response = client.get("/jobs/finished-job-456")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_get_job_not_found_returns_404():
    """GET /jobs/{id} for non-existent job returns HTTP 404."""
    r.hget.return_value = None
    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 404
    assert "detail" in response.json()
