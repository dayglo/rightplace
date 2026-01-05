"""Integration tests for health endpoint."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for /health endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """Should return 200 OK when server is healthy."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client: TestClient):
        """Should return expected health check response structure."""
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert "status" in data
        assert "model_loaded" in data
        assert "enrolled_count" in data
        assert "uptime_seconds" in data

    def test_health_check_status_healthy(self, client: TestClient):
        """Should return 'healthy' status."""
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert data["status"] == "healthy"

    def test_health_check_model_loaded_bool(self, client: TestClient):
        """Should return boolean for model_loaded."""
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert isinstance(data["model_loaded"], bool)

    def test_health_check_enrolled_count_type(self, client: TestClient):
        """Should return integer for enrolled_count."""
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert isinstance(data["enrolled_count"], int)
        assert data["enrolled_count"] >= 0

    def test_health_check_uptime_type(self, client: TestClient):
        """Should return numeric uptime in seconds."""
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
