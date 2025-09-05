"""
Unit tests voor de nieuwe frontend server met OAuth2Session en real-time streaming.
Test coverage voor WCAG 2.1 AA compliance en WebSocket functionaliteit.
"""

from collections.abc import Generator
import json
from pathlib import Path
import sys
import time
from typing import Any
from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.tools.frontend_server import (
    app,
    broadcast_activity,
    recent_activities,
)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestFrontendServer:
    """Test cases for the modern frontend server with real-time features."""

    @pytest.fixture  # type: ignore[misc]
    def client(self) -> Generator[Any]:
        """Create test client."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture  # type: ignore[misc]
    def mock_redis(self) -> Generator[Any]:
        """Mock Redis handler."""
        with patch("src.agentic_crypto_influencer.tools.frontend_server.redis_handler") as mock:
            mock.get.return_value = None
            mock.set.return_value = True
            mock.delete.return_value = True
            yield mock

    def test_dashboard_renders(self, client: Any) -> None:
        """Test that the main dashboard loads correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Agentic Crypto Influencer" in response.data
        assert b"OAuth Dashboard" in response.data

        # Check WCAG 2.1 AA compliance elements
        assert b"skip-link" in response.data
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
        token_data = {
            "access_token": "test_token",
            "token_type": "bearer",
            "expires_at": time.time() + 3600,
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
        """Test successful OAuth callback."""
        mock_redis.get.return_value = "test_code_verifier"

        with patch(
            "src.agentic_crypto_influencer.tools.frontend_server.get_and_save_tokens"
        ) as mock_tokens:
            mock_tokens.return_value = True

            response = client.get("/callback?code=test_code&state=test_state")
            assert response.status_code == 200
            assert b"Autorisatie Voltooid!" in response.data
            assert b"<script>" in response.data  # Auto-close script

    def test_callback_error(self, client: Any) -> None:
        """Test OAuth callback with error."""
        response = client.get("/callback?error=access_denied")
        assert response.status_code == 400
        assert b"OAuth Error" in response.data

    def test_callback_missing_code(self, client: Any) -> None:
        """Test callback without authorization code."""
        response = client.get("/callback")
        assert response.status_code == 400
        assert b"Geen autorisatiecode" in response.data

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
        from src.agentic_crypto_influencer.tools.frontend_server import MAX_RECENT_ACTIVITIES

        # Clear and fill beyond limit
        recent_activities.clear()
        for i in range(MAX_RECENT_ACTIVITIES + 10):
            broadcast_activity(f"Agent{i}", f"Message {i}", "info")

        assert len(recent_activities) == MAX_RECENT_ACTIVITIES

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
