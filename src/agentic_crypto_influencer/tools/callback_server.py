import base64
import json
import logging
from threading import Thread
import urllib.parse

from flask import Flask, request
import requests
from src.agentic_crypto_influencer.config.key_constants import (
    X_CLIENT_ID,
    X_CLIENT_SECRET,
    X_REDIRECT_URI,
    X_SCOPES,
)
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler

errormanager = ErrorManager()

app = Flask(__name__)


# --- Functie om de tokens te verkrijgen en op te slaan ---
def get_and_save_tokens(code: str) -> bool:
    if not code:
        raise ValueError("Geen autorisatiecode ontvangen.")
    if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
        raise ValueError("Niet alle vereiste omgevingsvariabelen zijn ingesteld.")

    token_url = "https://api.twitter.com/2/oauth2/token"  # nosec B105 - This is a public API endpoint, not a password
    token_params: dict[str, str] = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": X_REDIRECT_URI,
        "code_verifier": "challenge",  # Moet overeenkomen met 'code_challenge'
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
        errormanager.handle_error(e)
        return False

    logging.info("Tokens succesvol verkregen!")

    access_token = str(tokens.get("access_token", ""))
    refresh_token = str(tokens.get("refresh_token", ""))

    redis_handler = RedisHandler()
    redis_handler.set(
        "token",
        json.dumps({"access_token": access_token, "refresh_token": refresh_token}),
    )
    logging.info("Access and refresh tokens opgeslagen in Redis.")

    # Sluit de server netjes af na succesvolle verwerking
    try:
        requests.post("http://127.0.0.1:5000/shutdown", timeout=30)
    except requests.exceptions.ConnectionError:
        # This is expected, as the server will shut down before the request completes.
        logging.info("Server shutdown request sent.")
    return True


@app.route("/shutdown", methods=["POST"])  # type: ignore[misc]
def shutdown() -> str:
    """Sluit de Flask-server op een schone manier af."""
    terminate_func = request.environ.get("flask._terminate_server")
    if terminate_func is None:
        raise RuntimeError("De server ondersteunt geen schone afsluiting.")
    terminate_func()
    return "Server shutting down..."


@app.route("/callback", methods=["GET"])  # type: ignore[misc]
def callback() -> tuple[str, int]:
    """Verwerkt de callback van de autorisatie en genereert de tokens."""
    code = request.args.get("code")

    if code:
        print("-" * 50)
        print("Autorisatiecode ontvangen. Tokens ophalen...")

        # Start een nieuwe thread om de tokens te verkrijgen en op te slaan
        # Dit voorkomt dat de browser vastloopt
        Thread(target=get_and_save_tokens, args=(code,)).start()

        return (
            "Autorisatie succesvol! De tokens worden opgeslagen in een bestand. "
            "Je kunt deze terminal sluiten.",
            200,
        )
    else:
        return "Fout: Geen autorisatiecode gevonden.", 400


@app.route("/test_authorization", methods=["GET"])  # type: ignore[misc]
def test_authorization() -> tuple[str, int]:
    """Controleer of de access en refresh tokens correct zijn opgeslagen in Redis."""
    redis_handler = RedisHandler()
    tokens = redis_handler.get("token")

    if not tokens:
        return "Geen tokens gevonden in Redis.", 404

    try:
        tokens_data = json.loads(tokens)
        access_token = tokens_data.get("access_token")
        refresh_token = tokens_data.get("refresh_token")

        if not access_token or not refresh_token:
            return "Tokens zijn onvolledig opgeslagen in Redis.", 400

        return (
            f"Access Token: {access_token}<br>Refresh Token: {refresh_token}",
            200,
        )
    except json.JSONDecodeError:
        return "Fout bij het decoderen van tokens uit Redis.", 500


if __name__ == "__main__":
    if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
        raise ValueError("Niet alle vereiste omgevingsvariabelen zijn ingesteld.")
    # Bouw de autorisatie-URL en druk deze af voor de gebruiker
    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    auth_params: dict[str, str] = {
        "response_type": "code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": X_REDIRECT_URI,
        "scope": X_SCOPES,
        "state": "state",
        "code_challenge": "challenge",
        "code_challenge_method": "plain",
    }

    authorization_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"

    print("--- Stap 1: Autorisatie ---")
    print("1. Zorg ervoor dat je dit script draait.")
    print("2. Ga naar de volgende URL in je browser om toestemming te geven:")
    print(authorization_url)
    print(
        "De server zal automatisch de tokens opslaan en afsluiten nadat je de app "
        "hebt geautoriseerd."
    )

    # Start de lokale server
    app.run(port=5000)
