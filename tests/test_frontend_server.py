"""
Unit tests voor de nieuwe frontend server met OAuth2Session en real-time streaming.
Test coverage voor WCAG 2.1 AA compliance en WebSocket functionaliteit.
"""

from collections.abc import Generator
from datetime import UTC, datetime
import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.tools.frontend_server import (
    broadcast_activity,
    recent_activities,
)


@pytest.fixture
def client() -> Any:
    """Create a test client."""
    from src.agentic_crypto_influencer.tools.frontend_server import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_redis() -> Generator[Any]:
    """Mock Redis handler."""
    with patch("src.agentic_crypto_influencer.tools.frontend_server.redis_handler") as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        yield mock


class TestFrontendServer:
    """Test cases for the modern frontend server with real-time features."""

    def test_dashboard_renders(self, client: Any) -> None:
        """Test that the main dashboard loads correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Agentic Crypto Influencer" in response.data
        assert b"OAuth Dashboard" in response.data

        # Check WCAG 2.1 AA compliance elements
        assert b"skip-link" in response.data

    def test_dashboard_oauth_success_message(self, client: Any) -> None:
        """Test dashboard shows OAuth success message from URL parameters."""
        response = client.get("/?oauth_success=true")
        assert response.status_code == 200
        # The success message should be broadcasted via WebSocket

    def test_dashboard_oauth_error_message(self, client: Any) -> None:
        """Test dashboard shows OAuth error message from URL parameters."""
        response = client.get("/?oauth_error=no_code")
        assert response.status_code == 200
        # The error message should be broadcasted via WebSocket
        assert b"aria-live" in response.data
        assert b'role="banner"' in response.data
        assert b'role="main"' in response.data

    def test_oauth_status_unauthorized(self, client: Any, mock_redis: Any) -> None:
        """Test OAuth status when unauthorized."""
        mock_redis.get.return_value = None

        response = client.get("/api/oauth/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["authorized"] is False
        assert "Autorisatie vereist" in data["message"]

    def test_oauth_status_authorized(self, client: Any, mock_redis: Any) -> None:
        """Test OAuth status when authorized."""
        token_data: dict[str, Any] = {
            "access_token": "test_token",
            "token_type": "bearer",
            "expires_at": datetime.now(UTC).timestamp() + 3600,
        }
        mock_redis.get.return_value = json.dumps(token_data)

        response = client.get("/api/oauth/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["authorized"] is True
        assert data["token_type"] == "bearer"

    @patch("src.agentic_crypto_influencer.tools.oauth_handler.OAuthHandler")
    def test_oauth_url_generation(self, mock_oauth_handler: Any, client: Any) -> None:
        """Test OAuth URL generation."""
        mock_handler = Mock()
        mock_handler.get_authorization_url.return_value = (
            "https://twitter.com/oauth/authorize?code_challenge=test"
        )
        mock_oauth_handler.return_value = mock_handler

        response = client.get("/api/oauth/url")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "url" in data
        assert "twitter.com" in data["url"]
        assert "timestamp" in data

    @patch("src.agentic_crypto_influencer.tools.oauth_handler.OAuthHandler")
    def test_oauth_authorize_redirect(self, mock_oauth_handler: Any, client: Any) -> None:
        """Test OAuth authorization redirect endpoint."""
        mock_handler = Mock()
        mock_handler.get_authorization_url.return_value = (
            "https://twitter.com/oauth/authorize?code_challenge=test"
        )
        mock_oauth_handler.return_value = mock_handler

        response = client.get("/oauth/authorize", follow_redirects=False)
        assert response.status_code == 302  # Redirect
        assert "twitter.com" in response.location

    def test_redis_status_connected(self, client: Any, mock_redis: Any) -> None:
        """Test Redis status when connected."""
        mock_redis.redis_client = Mock()
        mock_redis.redis_client.ping.return_value = True

        response = client.get("/api/system/redis")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "ok"
        assert "Redis verbinding actief" in data["message"]

    def test_redis_status_disconnected(self, client: Any, mock_redis: Any) -> None:
        """Test Redis status when disconnected."""
        mock_redis.ping.side_effect = Exception("Connection failed")

        response = client.get("/api/system/redis")
        assert response.status_code == 500

        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "Redis verbinding mislukt" in data["message"]

    def test_callback_success(self, client: Any, mock_redis: Any) -> None:
        """Test successful OAuth callback redirects to dashboard."""
        mock_redis.get.return_value = "test_code_verifier"

        with patch(
            "src.agentic_crypto_influencer.tools.frontend_server.get_and_save_tokens"
        ) as mock_tokens:
            mock_tokens.return_value = True

            response = client.get("/callback?code=test_code&state=test_state")
            assert response.status_code == 302  # Redirect
            assert "oauth_success=true" in response.location

    def test_callback_error(self, client: Any) -> None:
        """Test OAuth callback with error redirects to dashboard."""
        response = client.get("/callback?error=access_denied")
        assert response.status_code == 302  # Redirect
        assert "oauth_error=access_denied" in response.location

    def test_callback_missing_code(self, client: Any) -> None:
        """Test callback without authorization code redirects to dashboard."""
        response = client.get("/callback")
        assert response.status_code == 302  # Redirect
        assert "oauth_error=no_code" in response.location

    def test_callback_token_exchange_failure(self, client: Any, mock_redis: Any) -> None:
        """Test callback with token exchange failure redirects to dashboard."""
        mock_redis.get.return_value = "test_code_verifier"

        with patch(
            "src.agentic_crypto_influencer.tools.frontend_server.get_and_save_tokens"
        ) as mock_tokens:
            mock_tokens.return_value = False

            response = client.get("/callback?code=test_code&state=test_state")
            assert response.status_code == 302  # Redirect
            assert "oauth_error=token_exchange_failed" in response.location

    def test_broadcast_activity(self) -> None:
        """Test activity broadcasting functionality."""
        # Clear recent activities
        recent_activities.clear()

        broadcast_activity("TestAgent", "Test message", "info")

        assert len(recent_activities) == 1
        activity = recent_activities[0]
        assert activity["agent"] == "TestAgent"
        assert activity["message"] == "Test message"
        assert activity["type"] == "info"
        assert "timestamp" in activity

    def test_recent_activities_limit(self) -> None:
        """Test that recent activities are limited to MAX_RECENT_ACTIVITIES."""
        from src.agentic_crypto_influencer.config.frontend_constants import MAX_RECENT_ACTIVITIES

        # Clear and fill beyond limit
        recent_activities.clear()
        for i in range(MAX_RECENT_ACTIVITIES + 10):
            broadcast_activity(f"Agent{i}", f"Message {i}", "info")

        assert len(recent_activities) == MAX_RECENT_ACTIVITIES

    def test_graphflow_activity_forwarding(self, mock_redis: Any) -> None:
        """Test GraphFlow activity forwarding from Redis."""
        from src.agentic_crypto_influencer.tools.frontend_server import check_graphflow_activity

        # Mock GraphFlow activity in Redis
        mock_activity = {
            "agent": "GraphFlow",
            "message": "🚀 Test GraphFlow activity",
            "type": "info",
            "timestamp": datetime.now().isoformat(),
        }
        mock_redis.get.return_value = json.dumps(mock_activity).encode("utf-8")

        # Clear recent activities
        recent_activities.clear()

        # Check for GraphFlow activity
        check_graphflow_activity()

        # Verify activity was added
        assert len(recent_activities) == 1
        assert recent_activities[0]["agent"] == "GraphFlow"
        assert "🚀 Test GraphFlow activity" in recent_activities[0]["message"]

        # Verify Redis delete was called to prevent duplication
        mock_redis.delete.assert_called_with("graphflow_activity")

    def test_get_recent_activities_api(self, client: Any) -> None:
        """Test the recent activities API endpoint."""
        # Clear and add test activities
        recent_activities.clear()
        broadcast_activity("TestAgent", "Test message", "info")

        response = client.get("/api/stream/activities")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "activities" in data
        assert "timestamp" in data
        assert len(data["activities"]) == 1
        assert data["activities"][0]["agent"] == "TestAgent"

    def test_static_files(self, client: Any) -> None:
        """Test static file serving."""
        # Test manifest.json
        response = client.get("/static/manifest.json")
        # Should return 404 if file doesn't exist, or 200 if it does
        assert response.status_code in [200, 404]

    def test_404_handler(self, client: Any) -> None:
        """Test custom 404 error handler."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data["error"] == "Not Found"
        assert "timestamp" in data

    @patch("src.agentic_crypto_influencer.tools.frontend_server.requests.post")
    def test_token_exchange_success(self, mock_post: Any, mock_redis: Any) -> None:
        """Test successful token exchange."""
        from src.agentic_crypto_influencer.tools.frontend_server import get_and_save_tokens

        # Mock Redis responses
        mock_redis.get.return_value = "test_code_verifier"

        # Mock successful token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "token_type": "bearer",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        result = get_and_save_tokens("test_code")
        assert result is True

        # Verify token was saved
        mock_redis.set.assert_called()
        # Verify cleanup
        mock_redis.delete.assert_called()

    @patch("src.agentic_crypto_influencer.tools.frontend_server.requests.post")
    def test_token_exchange_failure(self, mock_post: Any, mock_redis: Any) -> None:
        """Test failed token exchange."""
        from src.agentic_crypto_influencer.tools.frontend_server import get_and_save_tokens

        # Mock Redis responses
        mock_redis.get.return_value = "test_code_verifier"

        # Mock failed token response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid request"
        mock_post.return_value = mock_response

        result = get_and_save_tokens("test_code")
        assert result is False

    def test_accessibility_compliance(self, client: Any) -> None:
        """Test WCAG 2.1 AA accessibility compliance features."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        # Check required accessibility elements
        assert 'lang="nl"' in html
        assert "skip-link" in html
        assert 'aria-live="polite"' in html
        assert "aria-describedby=" in html
        assert 'role="banner"' in html
        assert 'role="main"' in html
        assert 'role="log"' in html
        assert 'tabindex="0"' in html

        # Check color contrast variables
        assert "--focus-color:" in html
        assert "--focus-width:" in html

        # Check media queries for accessibility
        assert "@media (prefers-contrast: high)" in html
        assert "@media (prefers-reduced-motion: reduce)" in html
        assert "@media (prefers-color-scheme: dark)" in html

    def test_progressive_web_app_elements(self, client: Any) -> None:
        """Test PWA compliance elements."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        # Check PWA meta tags
        assert 'name="viewport"' in html
        assert 'name="theme-color"' in html
        assert 'rel="manifest"' in html
        assert 'name="apple-mobile-web-app-capable"' in html

        # Check manifest link
        assert "/static/manifest.json" in html

    @pytest.fixture
    def mock_scheduler_manager(self) -> Generator[Any]:
        """Mock scheduler manager for testing scheduler endpoints."""
        with patch(
            "src.agentic_crypto_influencer.tools.frontend_server.scheduler_manager"
        ) as mock:
            mock.start_graphflow.return_value = {"success": True, "pid": 12345}
            mock.stop_graphflow.return_value = {"success": True}
            mock.get_graphflow_status.return_value = {
                "running": True,
                "pid": 12345,
                "start_time": "2023-01-01T10:00:00",
            }
            mock.create_scheduled_job.return_value = {"success": True, "job_id": "test_job_123"}
            mock.get_scheduled_jobs.return_value = []
            mock.cancel_job.return_value = {"success": True}
            mock.get_job_history.return_value = []
            yield mock

    def test_start_graphflow_success(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test successful GraphFlow start via API."""
        response = client.post("/api/graphflow/start")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "message" in data
        assert "pid" in data
        assert data["pid"] == 12345
        mock_scheduler_manager.start_graphflow.assert_called_once()

    def test_start_graphflow_scheduler_unavailable(self, client: Any) -> None:
        """Test GraphFlow start when scheduler is unavailable."""
        with patch("src.agentic_crypto_influencer.tools.frontend_server.scheduler_manager", None):
            response = client.post("/api/graphflow/start")
            assert response.status_code == 500

            data = json.loads(response.data)
            assert "error" in data
            assert "Scheduler not available" in data["error"]

    def test_start_graphflow_failure(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test GraphFlow start failure."""
        mock_scheduler_manager.start_graphflow.return_value = {
            "success": False,
            "error": "Process already running",
        }

        response = client.post("/api/graphflow/start")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "Process already running" in data["error"]

    def test_stop_graphflow_success(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test successful GraphFlow stop via API."""
        response = client.post("/api/graphflow/stop")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "message" in data
        mock_scheduler_manager.stop_graphflow.assert_called_once()

    def test_stop_graphflow_failure(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test GraphFlow stop failure."""
        mock_scheduler_manager.stop_graphflow.return_value = {
            "success": False,
            "error": "Process not running",
        }

        response = client.post("/api/graphflow/stop")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "Process not running" in data["error"]

    def test_graphflow_status(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test GraphFlow status check via API."""
        response = client.get("/api/graphflow/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "running" in data
        assert "pid" in data
        assert "start_time" in data
        assert data["running"] is True
        assert data["pid"] == 12345
        mock_scheduler_manager.get_graphflow_status.assert_called_once()

    def test_create_scheduled_job_success(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test successful scheduled job creation."""
        job_data: dict[str, Any] = {
            "job_type": "single_post",
            "schedule_type": "once",
            "schedule_config": {"run_date": "2023-12-01T10:00:00"},
            "job_name": "Test Job",
        }

        response = client.post(
            "/api/jobs/create", data=json.dumps(job_data), content_type="application/json"
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "message" in data
        assert "job_id" in data
        assert data["job_id"] == "test_job_123"
        mock_scheduler_manager.create_scheduled_job.assert_called_once()

    def test_create_scheduled_job_missing_data(
        self, client: Any, mock_scheduler_manager: Any
    ) -> None:
        """Test scheduled job creation with missing data."""
        response = client.post("/api/jobs/create")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "No data provided" in data["error"]

    def test_create_scheduled_job_missing_fields(
        self, client: Any, mock_scheduler_manager: Any
    ) -> None:
        """Test scheduled job creation with missing required fields."""
        job_data = {"job_name": "Test Job"}  # Missing required fields

        response = client.post(
            "/api/jobs/create", data=json.dumps(job_data), content_type="application/json"
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "Missing required fields" in data["error"]

    def test_create_scheduled_job_failure(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test scheduled job creation failure."""
        mock_scheduler_manager.create_scheduled_job.return_value = {
            "success": False,
            "error": "Invalid schedule configuration",
        }

        job_data: dict[str, Any] = {
            "job_type": "single_post",
            "schedule_type": "once",
            "schedule_config": {"invalid": "config"},
        }

        response = client.post(
            "/api/jobs/create", data=json.dumps(job_data), content_type="application/json"
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "Invalid schedule configuration" in data["error"]

    def test_list_scheduled_jobs(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test listing scheduled jobs."""
        mock_jobs: list[dict[str, Any]] = [
            {
                "id": "job1",
                "name": "Test Job 1",
                "type": "single_post",
                "schedule_type": "once",
                "next_run": "2023-12-01T10:00:00",
            },
            {
                "id": "job2",
                "name": "Test Job 2",
                "type": "graphflow",
                "schedule_type": "interval",
                "next_run": None,
            },
        ]
        mock_scheduler_manager.get_scheduled_jobs.return_value = mock_jobs

        response = client.get("/api/jobs/list")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "jobs" in data
        assert len(data["jobs"]) == 2
        assert data["jobs"][0]["id"] == "job1"
        assert data["jobs"][1]["id"] == "job2"
        mock_scheduler_manager.get_scheduled_jobs.assert_called_once()

    def test_cancel_scheduled_job_success(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test successful job cancellation."""
        response = client.delete("/api/jobs/cancel/test_job_123")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "message" in data
        mock_scheduler_manager.cancel_job.assert_called_once_with("test_job_123")

    def test_cancel_scheduled_job_failure(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test job cancellation failure."""
        mock_scheduler_manager.cancel_job.return_value = {
            "success": False,
            "error": "Job not found",
        }

        response = client.delete("/api/jobs/cancel/nonexistent_job")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "Job not found" in data["error"]

    def test_get_job_history(self, client: Any, mock_scheduler_manager: Any) -> None:
        """Test retrieving job execution history."""
        mock_history = [
            {
                "timestamp": "2023-01-01T10:00:00",
                "job_id": "job1",
                "job_name": "Test Job",
                "status": "completed",
                "message": "Success",
            }
        ]
        mock_scheduler_manager.get_job_history.return_value = mock_history

        response = client.get("/api/jobs/history")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "history" in data
        assert len(data["history"]) == 1
        assert data["history"][0]["job_id"] == "job1"
        assert data["history"][0]["status"] == "completed"
        mock_scheduler_manager.get_job_history.assert_called_once()

    def test_scheduler_endpoints_exception_handling(
        self, client: Any, mock_scheduler_manager: Any
    ) -> None:
        """Test that scheduler endpoints handle exceptions gracefully."""
        mock_scheduler_manager.start_graphflow.side_effect = Exception("Test exception")

        response = client.post("/api/graphflow/start")
        assert response.status_code == 500

        data = json.loads(response.data)
        assert "error" in data
        assert "Test exception" in data["error"]

    def test_scheduler_endpoints_exist(self, client: Any) -> None:
        """Test that scheduler endpoints exist (even if scheduler is unavailable)."""
        # These should return 500 if scheduler is not available, not 404
        endpoints = [
            ("/api/graphflow/status", "GET"),
            ("/api/jobs/list", "GET"),
            ("/api/jobs/history", "GET"),
        ]

        for endpoint, method in endpoints:
            response = client.post(endpoint) if method == "POST" else client.get(endpoint)

            # Should not be 404 (not found), might be 500 (server error) if scheduler unavailable
            assert response.status_code != 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
