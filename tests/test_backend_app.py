from fastapi.testclient import TestClient

from backend.main import app


def test_openapi_schema_is_available():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Red Roadmap API"
    assert "delete" in schema["paths"]["/api/missions"]
    assert "/api/missions/{task_id}/reminder" in schema["paths"]
    assert "/api/reminders/due" in schema["paths"]
