"""Unit tests for FastAPI REST endpoints."""
from fastapi.testclient import TestClient
from backend.api.routes import app

client = TestClient(app)


def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["ffmpeg"]["available"] is True
    assert "video_spec" in data
    assert data["video_spec"]["width"] == 1080
    assert data["video_spec"]["height"] == 1920


def test_api_projects_list():
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_generate_enqueue():
    response = client.post(
        "/api/generate",
        json={"topic": "Test Short Topic", "category": "science", "auto_publish": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["job_id"].startswith("job_")


def test_api_nonexistent_project():
    response = client.get("/api/projects/non_existent_id_12345")
    assert response.status_code == 404
