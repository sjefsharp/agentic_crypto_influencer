import json
import os
import requests
import base64
import urllib.parse
from flask import Flask, request
from threading import Thread
from config.key_constants import X_CLIENT_ID, X_CLIENT_SECRET, X_REDIRECT_URI, X_SCOPES
import logging
from error_management.error_manager import ErrorManager

errormanager = ErrorManager()

app = Flask(__name__)


# --- Functie om de tokens te verkrijgen en op te slaan ---
def get_and_save_tokens(code: str):
    if not code:
        raise ValueError("Geen autorisatiecode ontvangen.")
    if not X_CLIENT_ID or not X_CLIENT_SECRET or not X_REDIRECT_URI:
        raise ValueError("Niet alle vereiste omgevingsvariabelen zijn ingesteld.")

    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
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
        response = requests.post(TOKEN_URL, data=token_params, headers=headers)
        response.raise_for_status()
        tokens = response.json()
    except requests.exceptions.RequestException as e:
        errormanager.handle_error(e)
        return False

    logging.info("Tokens succesvol verkregen!")

    refresh_token = str(tokens.get("refresh_token", ""))
    access_token = str(tokens.get("access_token", ""))
    token_data = {
        "client_id": X_CLIENT_ID,
        "client_secret": X_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "access_token": access_token,
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, "tokens.json")

    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=4)

    logging.info("Refresh token opgeslagen in tokens.json.")

    # Sluit de server netjes af na succesvolle verwerking
    try:
        requests.post("http://127.0.0.1:5000/shutdown")
    except requests.exceptions.ConnectionError:
        # This is expected, as the server will shut down before the request completes.
        logging.info("Server shutdown request sent.")
    return True


@app.route("/shutdown", methods=["POST"])
def shutdown():
    """Sluit de Flask-server op een schone manier af."""
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Niet draaiend met de Werkzeug-ontwikkelserver")
    func()
    return "Server shutting down..."


@app.route("/callback", methods=["GET"])
def callback():
    """Verwerkt de callback van de autorisatie en genereert de tokens."""
    code = request.args.get("code")

    if code:
        print("-" * 50)
        print("Autorisatiecode ontvangen. Tokens ophalen...")

        # Start een nieuwe thread om de tokens te verkrijgen en op te slaan
        # Dit voorkomt dat de browser vastloopt
        Thread(target=get_and_save_tokens, args=(code,)).start()

        return (
            "Autorisatie succesvol! De tokens worden opgeslagen in een bestand. Je kunt deze terminal sluiten.",
            200,
        )
    else:
        return "Fout: Geen autorisatiecode gevonden.", 400


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
        "De server zal automatisch de tokens opslaan en afsluiten nadat je de app hebt geautoriseerd."
    )

    # Start de lokale server
    app.run(port=5000)
