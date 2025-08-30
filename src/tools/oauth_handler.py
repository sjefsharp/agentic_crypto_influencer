import base64
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict

from requests_oauthlib import OAuth2Session

from config.key_constants import (
    X_AUTHORIZE_ENDPOINT,
    X_CLIENT_ID,
    X_CLIENT_SECRET,
    X_REDIRECT_URI,
    X_SCOPES,
    X_TOKEN_ENDPOINT,
    X_URL,
)
from tools.redis_handler import RedisHandler


class OAuthHandler:
    def __init__(self):
        self.redis_handler = RedisHandler()
        self.client_id = X_CLIENT_ID
        self.client_secret = X_CLIENT_SECRET
        self.redirect_uri = X_REDIRECT_URI
        self.token_url = f"{X_URL}{X_TOKEN_ENDPOINT}"
        self.auth_url = f"{X_URL}{X_AUTHORIZE_ENDPOINT}"
        self.scopes = X_SCOPES.split()

    def get_authorization_url(self) -> str:
        code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
        code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)
        code_challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        # Keep code_challenge as bytes to satisfy type checkers; strip padding as bytes
        code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).rstrip(b"=")

        self.redis_handler.set("code_verifier", code_verifier)

        oauth = OAuth2Session(
            client_id=self.client_id, redirect_uri=self.redirect_uri, scope=self.scopes
        )
        authorization_url, state = oauth.authorization_url(  # type: ignore
            self.auth_url, code_challenge=code_challenge, code_challenge_method="S256"
        )
        self.redis_handler.set("oauth_state", state)
        return str(authorization_url)

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        code_verifier = self.redis_handler.get("code_verifier")
        if not code_verifier:
            raise RuntimeError("Code verifier not found in Redis")

        oauth = OAuth2Session(
            client_id=self.client_id, redirect_uri=self.redirect_uri, scope=self.scopes
        )
        token = oauth.fetch_token(  # type: ignore
            token_url=self.token_url,
            client_secret=self.client_secret,
            code_verifier=code_verifier.decode("utf-8"),
            code=code,
        )
        self.redis_handler.set("token", json.dumps(token))
        logging.info("Tokens successfully saved to Redis.")
        return dict(token)

    def refresh_access_token(self) -> Dict[str, Any]:
        token_data = self.redis_handler.get("token")
        if not token_data:
            raise RuntimeError("No token found in Redis")

        token = json.loads(token_data)
        oauth = OAuth2Session(
            client_id=self.client_id, redirect_uri=self.redirect_uri, scope=self.scopes
        )
        new_token = oauth.refresh_token(  # type: ignore
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=token.get("refresh_token", ""),
            headers={
                "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}"
            },
        )
        self.redis_handler.set("token", json.dumps(new_token))
        logging.info("Access token successfully refreshed and saved to Redis.")
        return dict(new_token)
