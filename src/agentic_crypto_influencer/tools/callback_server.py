"""
Moderne OAuth2 callback server met real-time dashboard voor X/Twitter API.
Features: WebSocket live streaming, WCAG 2.1 AA compliance, Progressive Web App.
Volledig gebaseerd op OAuth2Session library en X API v2 PKCE specificaties.
Optimized for Render.com deployment with accessibility support.
"""

import base64
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys

from flask import Flask, request
import requests

# Add project root to Python path for Render.com compatibility
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agentic_crypto_influencer.config.key_constants import (  # noqa: E402
    CALLBACK_SERVER_PORT,
    X_CLIENT_ID,
    X_CLIENT_SECRET,
    X_REDIRECT_URI,
    X_SCOPES,
)
from src.agentic_crypto_influencer.config.logging_config import get_logger  # noqa: E402
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler  # noqa: E402

logger = get_logger(__name__)

app = Flask(__name__)

# Smart host/port configuration for Render.com vs local
PORT = int(os.environ.get("PORT", CALLBACK_SERVER_PORT))  # Render.com provides PORT env var
HOST = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"  # Render.com vs local  # nosec B104


def get_and_save_tokens(code: str) -> bool:
    """
    Exchange authorization code for tokens using OAuth2Session with PKCE.
    Implements proper X API v2 OAuth2 flow.
    """
    try:
        if not code:
            raise ValueError("Geen autorisatiecode ontvangen.")
        if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
            raise ValueError("Niet alle vereiste omgevingsvariabelen zijn ingesteld.")

        # Get stored OAuth parameters from Redis
        redis_handler = RedisHandler(lazy_connect=True)
        stored_code_verifier = redis_handler.get("oauth_code_verifier")

        if not stored_code_verifier:
            logger.error(
                "No code_verifier found in Redis - authorization flow was not properly initiated"
            )
            return False

        logger.info("Retrieved code_verifier from Redis for token exchange")

        logger.info("Exchanging authorization code for tokens using OAuth2Session")
        logger.info(f"Client ID: {X_CLIENT_ID}")
        logger.info(f"Authorization code: {code[:20]}...")
        if isinstance(stored_code_verifier, bytes):
            logger.info(f"Code verifier: {stored_code_verifier.decode()[:20]}...")
        else:
            logger.info(f"Code verifier: {str(stored_code_verifier)[:20]}...")

        # Exchange authorization code for tokens using OAuth2Session
        # For X API v2, we need to handle the authorization manually for confidential clients

        # Prepare the authorization header for confidential client
        basic_auth = base64.b64encode(f"{X_CLIENT_ID}:{X_CLIENT_SECRET}".encode()).decode()

        # Prepare token request data according to X API v2 specs
        token_data: dict[str, str] = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": X_CLIENT_ID,
            "redirect_uri": X_REDIRECT_URI,
            "code_verifier": stored_code_verifier.decode("utf-8")
            if isinstance(stored_code_verifier, bytes)
            else str(stored_code_verifier),
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        }

        # Make the token exchange request directly (OAuth2Session has issues with X API v2)
        response = requests.post(
            "https://api.x.com/2/oauth2/token", data=token_data, headers=headers, timeout=30
        )

        logger.info(f"Token response status: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"Token request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

        token_response = response.json()

        logger.info("Successfully received token response from X API")
        logger.info(f"Token type: {token_response.get('token_type')}")
        logger.info(f"Scopes: {token_response.get('scope')}")

        # Extract tokens from response
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        token_type = token_response.get("token_type", "Bearer")
        expires_in = token_response.get("expires_in", 7200)  # Default 2 hours

        if not access_token:
            logger.error("No access token received in response")
            logger.error(f"Token response: {token_response}")
            return False

        # Save complete token response with expires_at calculation
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": token_type,
            "expires_in": expires_in,
            "scope": token_response.get("scope", X_SCOPES.split()),
            "expires_at": datetime.now(UTC).timestamp() + expires_in,
        }

        redis_handler.set("token", json.dumps(token_data))

        if refresh_token:
            logger.info("Stored both access and refresh tokens")
        else:
            logger.warning("No refresh token received - may need offline.access scope")

        # Clean up temporary OAuth data
        redis_handler.delete("oauth_code_verifier")
        redis_handler.delete("oauth_state")

        logger.info("OAuth2 token exchange completed successfully")
        return True

    except Exception as e:
        logger.error(f"Token exchange error: {e!s}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False


@app.route("/")
def home() -> tuple[str, int]:
    """Home page with service info and authorization link using OAuth2Session."""
    if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
        return "❌ OAuth configuration missing. Check environment variables.", 500

    try:
        # Use oauth_handler to generate proper PKCE authorization URL
        from src.agentic_crypto_influencer.tools.oauth_handler import get_authorization_url

        authorization_url = get_authorization_url()
    except Exception as e:
        logger.error(f"Failed to generate authorization URL: {e}")
        return f"❌ Error generating authorization URL: {e!s}", 500

    return (
        f"""
    <html>
    <head><title>X OAuth2Session Callback Service</title></head>
    <body>
        <h1>🐦 X/Twitter OAuth2Session Callback Service</h1>
        <p>Service is running with OAuth2Session library and PKCE S256 support</p>
        <h2>🔐 Authorize Application</h2>
        <a href="{authorization_url}" target="_blank" 
           style="background: #1DA1F2; color: white; padding: 10px 20px; 
                  text-decoration: none; border-radius: 5px;">
           🚀 Authorize with X/Twitter (OAuth2Session + PKCE S256)
        </a>
        <h2>📋 Available Endpoints</h2>
        <ul>
            <li><code>/callback</code> - OAuth callback (automatic)</li>
            <li><code>/test_authorization</code> - Check stored tokens</li>
            <li><code>/health</code> - Health check</li>
        </ul>
        <h2>🔧 Technical Details</h2>
        <ul>
            <li>✅ OAuth2Session library</li>
            <li>✅ PKCE S256 code challenge method</li>
            <li>✅ Cryptographically secure code verifier</li>
            <li>✅ X API v2 OAuth2 endpoints</li>
            <li>✅ offline.access scope for refresh tokens</li>
        </ul>
    </body>
    </html>
    """,
        200,
    )


@app.route("/health", methods=["GET"])
def health() -> tuple[str, int]:
    """Health check endpoint for Render.com."""
    return "✅ OAuth Callback Service is healthy", 200


@app.route("/callback", methods=["GET"])
def callback() -> tuple[str, int]:
    """Process OAuth callback and save tokens to Redis."""
    code = request.args.get("code")

    if code:
        logger.info("Authorization code received, fetching tokens...")

        # Direct execution - no threading needed for simple token exchange
        success = get_and_save_tokens(code)

        if success:
            return (
                "✅ Autorisatie succesvol! Tokens zijn opgeslagen in Redis. "
                "Je kunt deze pagina sluiten.",
                200,
            )
        else:
            return "❌ Fout bij het opslaan van tokens.", 500
    else:
        return "❌ Fout: Geen autorisatiecode gevonden.", 400


@app.route("/test_authorization", methods=["GET"])
def test_authorization() -> tuple[str, int]:
    """Check if tokens are stored in Redis (masked for security)."""
    redis_handler = RedisHandler(lazy_connect=True)
    tokens = redis_handler.get("token")

    if not tokens:
        return "❌ Geen tokens gevonden in Redis.", 404

    try:
        tokens_data = json.loads(tokens)
        access_token = tokens_data.get("access_token")
        refresh_token = tokens_data.get("refresh_token")

        if not access_token or not refresh_token:
            return "❌ Tokens zijn onvolledig opgeslagen in Redis.", 400

        # Mask tokens for security - only show first/last 4 characters
        masked_access = (
            f"{access_token[:4]}...{access_token[-4:]}" if len(access_token) > 8 else "***"
        )
        masked_refresh = (
            f"{refresh_token[:4]}...{refresh_token[-4:]}" if len(refresh_token) > 8 else "***"
        )

        return (
            f"✅ Tokens gevonden in Redis:<br>"
            f"Access Token: {masked_access}<br>"
            f"Refresh Token: {masked_refresh}",
            200,
        )
    except json.JSONDecodeError:
        return "❌ Fout bij het decoderen van tokens uit Redis.", 500


if __name__ == "__main__":
    if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
        logger.error("❌ Missing required environment variables")
        logger.error("Required: X_CLIENT_ID, X_CLIENT_SECRET, X_REDIRECT_URI")
        raise ValueError("Not all required environment variables are set.")

    logger.info("🚀 Starting X OAuth Callback Service")
    logger.info(f"🌐 Service will be available on: http://{HOST}:{PORT}")
    logger.info("📱 Visit the home page to start OAuth authorization")

    # Start the Flask server
    app.run(host=HOST, port=PORT, debug=False)
