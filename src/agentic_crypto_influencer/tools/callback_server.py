"""
OAuth callback server for X/Twitter API authentication.
Optimized for Render.com deployment as a web service.
"""

import base64
import json
import os
from pathlib import Path
import sys
import urllib.parse

# Add project root to Python path for Render.com compatibility
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, request  # noqa: E402
import requests  # noqa: E402

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
    """Get OAuth tokens and save to Redis."""
    if not code:
        raise ValueError("Geen autorisatiecode ontvangen.")
    if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
        raise ValueError("Niet alle vereiste omgevingsvariabelen zijn ingesteld.")

    token_url = "https://api.twitter.com/2/oauth2/token"  # nosec B105
    token_params: dict[str, str] = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": X_REDIRECT_URI,
        "code_verifier": "challenge",
    }

    basic_auth = base64.b64encode(f"{X_CLIENT_ID}:{X_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_auth}",
    }

    try:
        response = requests.post(token_url, data=token_params, headers=headers, timeout=30)
        response.raise_for_status()
        tokens = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Token request failed: {e}")
        return False

    logger.info("Tokens succesvol verkregen!")

    access_token = str(tokens.get("access_token", ""))
    refresh_token = str(tokens.get("refresh_token", ""))

    redis_handler = RedisHandler()
    redis_handler.set(
        "token",
        json.dumps({"access_token": access_token, "refresh_token": refresh_token}),
    )
    logger.info("Access and refresh tokens opgeslagen in Redis.")
    return True


@app.route("/")  # type: ignore[misc]
def home() -> tuple[str, int]:
    """Home page with service info and authorization link."""
    if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
        return "❌ OAuth configuration missing. Check environment variables.", 500

    # Build authorization URL
    auth_url = "https://twitter.com/i/oauth2/authorize"
    auth_params: dict[str, str] = {
        "response_type": "code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": X_REDIRECT_URI,
        "scope": X_SCOPES,
        "state": "state",
        "code_challenge": "challenge",
        "code_challenge_method": "plain",
    }
    authorization_url = f"{auth_url}?{urllib.parse.urlencode(auth_params)}"

    return (
        f"""
    <html>
    <head><title>X OAuth Callback Service</title></head>
    <body>
        <h1>🐦 X/Twitter OAuth Callback Service</h1>
        <p>Service is running on Render.com</p>
        <h2>🔐 Authorize Application</h2>
        <a href="{authorization_url}" target="_blank" 
           style="background: #1DA1F2; color: white; padding: 10px 20px; 
                  text-decoration: none; border-radius: 5px;">
           🚀 Authorize with X/Twitter
        </a>
        <h2>📋 Available Endpoints</h2>
        <ul>
            <li><code>/callback</code> - OAuth callback (automatic)</li>
            <li><code>/test_authorization</code> - Check stored tokens</li>
            <li><code>/health</code> - Health check</li>
        </ul>
    </body>
    </html>
    """,
        200,
    )


@app.route("/health", methods=["GET"])  # type: ignore[misc]
def health() -> tuple[str, int]:
    """Health check endpoint for Render.com."""
    return "✅ OAuth Callback Service is healthy", 200


@app.route("/callback", methods=["GET"])  # type: ignore[misc]
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


@app.route("/test_authorization", methods=["GET"])  # type: ignore[misc]
def test_authorization() -> tuple[str, int]:
    """Check if tokens are stored in Redis (masked for security)."""
    redis_handler = RedisHandler()
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
