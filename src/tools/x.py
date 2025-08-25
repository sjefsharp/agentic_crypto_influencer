import base64
import json
import os
import requests

from config.key_constants import (
    X_ENDPOINT,
    X_TWEETS_ENDPOINT,
)
from error_management.error_manager import ErrorManager


class X:
    def __init__(self):
        self.access_token = self._load_access_token()
        self.x_endpoint = f"{X_ENDPOINT}{X_TWEETS_ENDPOINT}"

    def _load_access_token(self):
        """Loads the access token from tokens.json."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, "tokens.json")

        if not os.path.exists(token_path):
            raise FileNotFoundError(
                "tokens.json not found. Please run callback_server.py first to authenticate."
            )
        with open(token_path, "r") as f:
            token_data = json.load(f)
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("Access token not found in tokens.json.")
            return access_token

    def _load_refresh_token(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, "tokens.json")
        with open(token_path, "r") as f:
            token_data = json.load(f)
            refresh_token = token_data.get("refresh_token")
            if not refresh_token:
                raise ValueError("Refresh token not found in tokens.json.")
            return refresh_token

    def _save_tokens(self, access_token: str, refresh_token: str) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, "tokens.json")
        with open(token_path, "r") as f:
            token_data = json.load(f)
        token_data["access_token"] = access_token
        token_data["refresh_token"] = refresh_token
        with open(token_path, "w") as f:
            json.dump(token_data, f, indent=4)

    def _refresh_access_token(self):
        from config.key_constants import X_CLIENT_ID, X_CLIENT_SECRET, X_REDIRECT_URI

        TOKEN_URL = "https://api.x.com/2/oauth2/token"
        refresh_token = self._load_refresh_token()
        from typing import Dict

        token_params: Dict[str, str] = {
            "refresh_token": str(refresh_token),
            "grant_type": "refresh_token",
            "client_id": str(X_CLIENT_ID),
            "redirect_uri": str(X_REDIRECT_URI),
        }
        basic_auth = base64.b64encode(
            f"{X_CLIENT_ID}:{X_CLIENT_SECRET}".encode()
        ).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        }
        response = requests.post(TOKEN_URL, data=token_params, headers=headers)
        response.raise_for_status()
        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token", refresh_token)
        self._save_tokens(access_token, refresh_token)
        self.access_token = access_token

    def post(self, post: str):
        if not post or len(post) > 280:
            raise ValueError("Post must be between 1 and 280 characters")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"text": post}

        try:
            response = requests.post(
                self.x_endpoint,
                json=payload,
                headers=headers,
            )
            if response.status_code == 401:
                # Refresh token and retry
                self._refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.post(
                    self.x_endpoint,
                    json=payload,
                    headers=headers,
                )
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while posting on X. Message: {str(e)}"
            )

        if response.status_code != 201:
            raise Exception(
                f"Request returned an error: {response.status_code} {response.text}"
            )

        try:
            return response.json()
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while processing the response from X. Message: {str(e)}"
            )


def main():
    error_manager = ErrorManager()
    try:
        x = X()
        post = "Post"
        result = x.post(post)
        print("--- Results ---")
        print(result)
    except (ValueError, RuntimeError) as e:
        error_message = error_manager.handle_error(e)
        print(error_message)
    except Exception as e:
        error_message = error_manager.handle_error(e)
        print(error_message)


if __name__ == "__main__":
    main()
