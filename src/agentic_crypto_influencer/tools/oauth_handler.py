import base64
import hashlib
import json
import logging
import os
import secrets
from typing import Any

from requests_oauthlib import OAuth2Session

from src.agentic_crypto_influencer.config.key_constants import (
    X_AUTHORIZE_ENDPOINT,
    X_CLIENT_ID,
    X_CLIENT_SECRET,
    X_REDIRECT_URI,
    X_SCOPES,
    X_TOKEN_ENDPOINT,
    X_URL,
)
from src.agentic_crypto_influencer.config.oauth_constants import (
    ERROR_CODE_VERIFIER_NOT_FOUND,
    OAUTH_CODE_CHALLENGE_METHOD,
    OAUTH_DEFAULT_SCOPES,
    OAUTH_REDIRECT_URI_LOCAL,
    SUCCESS_PLEASE_AUTHORIZE,
    SUCCESS_TOKENS_SAVED,
    SUCCESS_URL_GENERATED,
    X_AUTHORIZE_URL,
)
from src.agentic_crypto_influencer.config.redis_constants import (
    OAUTH_CODE_VERIFIER_EXPIRY,
    OAUTH_STATE_EXPIRY,
    REDIS_KEY_OAUTH_CODE_VERIFIER,
    REDIS_KEY_OAUTH_STATE,
    REDIS_KEY_TOKEN,
)
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler


def generate_code_verifier() -> str:
    """Generate a cryptographically secure code verifier for PKCE."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")


def generate_code_challenge(code_verifier: str) -> str:
    """Generate code challenge from code verifier using SHA256 method."""
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


class OAuthHandler:
    def __init__(self) -> None:
        self.redis_handler = RedisHandler(lazy_connect=True)
        self.client_id = X_CLIENT_ID
        self.client_secret = X_CLIENT_SECRET
        self.redirect_uri = X_REDIRECT_URI
        self.token_url = f"{X_URL}{X_TOKEN_ENDPOINT}"
        self.auth_url = f"{X_URL}{X_AUTHORIZE_ENDPOINT}"
        self.scopes = X_SCOPES.split()

    def get_authorization_url(self) -> str:
        """
        Generate OAuth2 authorization URL with PKCE according to X API v2 specifications.
        """
        # Generate PKCE parameters
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)

        # Store code_verifier for later use in token exchange (consistent naming)
        self.redis_handler.set(
            REDIS_KEY_OAUTH_CODE_VERIFIER, code_verifier, ex=OAUTH_CODE_VERIFIER_EXPIRY
        )  # Expires in 10 min

        # OAuth2 configuration
        client_id = os.getenv("X_CLIENT_ID")
        redirect_uri = OAUTH_REDIRECT_URI_LOCAL

        # Create OAuth2 session with X API v2 scopes
        oauth = OAuth2Session(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=OAUTH_DEFAULT_SCOPES,
        )

        # Generate authorization URL with PKCE parameters (S256 method as per X API v2 docs)
        authorization_url, state = oauth.authorization_url(
            X_AUTHORIZE_URL,
            code_challenge=code_challenge,
            code_challenge_method=OAUTH_CODE_CHALLENGE_METHOD,
        )

        # Store state for CSRF protection (consistent naming)
        self.redis_handler.set(REDIS_KEY_OAUTH_STATE, state, ex=OAUTH_STATE_EXPIRY)

        print(SUCCESS_URL_GENERATED)
        print(SUCCESS_PLEASE_AUTHORIZE % authorization_url)
        return str(authorization_url)

    def exchange_code_for_tokens(self, code: str) -> dict[str, Any]:
        code_verifier = self.redis_handler.get(REDIS_KEY_OAUTH_CODE_VERIFIER)
        if not code_verifier:
            raise RuntimeError(ERROR_CODE_VERIFIER_NOT_FOUND)

        oauth = OAuth2Session(
            client_id=self.client_id, redirect_uri=self.redirect_uri, scope=self.scopes
        )
        token = oauth.fetch_token(
            token_url=self.token_url,
            client_secret=self.client_secret,
            code_verifier=code_verifier.decode("utf-8")
            if isinstance(code_verifier, bytes)
            else code_verifier,
            code=code,
        )
        self.redis_handler.set(REDIS_KEY_TOKEN, json.dumps(token))
        logging.info(SUCCESS_TOKENS_SAVED)
        return dict(token)

    def refresh_access_token(self) -> dict[str, Any]:
        token_data = self.redis_handler.get("token")
        if not token_data:
            raise RuntimeError("No token found in Redis")

        # Handle both bytes and string data from Redis
        token_str = token_data.decode("utf-8") if isinstance(token_data, bytes) else token_data
        token = json.loads(token_str)

        # Create OAuth2 session
        oauth = OAuth2Session(
            client_id=self.client_id, redirect_uri=self.redirect_uri, scope=self.scopes
        )

        # Twitter OAuth2 refresh - requires Basic auth header
        new_token = oauth.refresh_token(
            token_url=self.token_url,
            refresh_token=token.get("refresh_token", ""),
            client_id=self.client_id,
            client_secret=self.client_secret,
            headers={
                "Authorization": (
                    "Basic "
                    + base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
                ),
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        self.redis_handler.set("token", json.dumps(new_token))
        logging.info("Access token successfully refreshed and saved to Redis.")
        return dict(new_token)


def get_authorization_url() -> str:
    """
    Generate OAuth2 authorization URL with PKCE according to X API v2 specifications.
    This is a standalone function for backwards compatibility.
    """
    handler = OAuthHandler()
    return handler.get_authorization_url()
