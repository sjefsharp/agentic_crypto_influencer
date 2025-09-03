"""
Key constants module for environment variable access.

Provides centralized access to all environment variables used throughout the application.
All variables use standardized naming conventions for consistency.
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variable constants with standardized naming

# Google API Keys
GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# X (Twitter) API Configuration - Standardized naming
X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
X_USER_ID = os.getenv("X_USER_ID")

# X API Endpoints (these remain as constants since they're not configurable)
X_URL = os.getenv("X_URL", "https://api.twitter.com")
X_AUTHORIZE_ENDPOINT = os.getenv("X_AUTHORIZE_ENDPOINT", "https://twitter.com/i/oauth2/authorize")
X_TOKEN_ENDPOINT = os.getenv("X_TOKEN_ENDPOINT", "https://api.twitter.com/2/oauth2/token")
X_TWEETS_ENDPOINT = os.environ.get("X_TWEETS_ENDPOINT", "https://api.twitter.com/2/tweets")
X_PERSONALIZED_TRENDS_ENDPOINT = os.getenv(
    "X_PERSONALIZED_TRENDS_ENDPOINT", "https://api.twitter.com/1.1/trends/place.json"
)

# OAuth Configuration
X_REDIRECT_URI = os.getenv("X_REDIRECT_URI", "http://localhost:5000/callback")
X_SCOPES = os.getenv(
    "X_SCOPES",
    "tweet.read tweet.write tweet.moderate.write users.email users.read follows.read "
    "follows.write offline.access space.read mute.read mute.write like.read like.write "
    "list.read list.write block.read block.write bookmark.read bookmark.write media.write",
)

# Callback Server Configuration
CALLBACK_SERVER_HOST = os.getenv("CALLBACK_SERVER_HOST", "127.0.0.1")
CALLBACK_SERVER_PORT = int(os.getenv("CALLBACK_SERVER_PORT", "5000"))

# Database Configuration
REDIS_URL = os.getenv("REDIS_URL")

# Bitvavo API Configuration
BITVAVO_API_KEY = os.getenv("BITVAVO_API_KEY")
BITVAVO_API_SECRET = os.getenv("BITVAVO_API_SECRET")


def get_configuration_value(
    env_key: str, config_path: str | None = None, default: str | None = None
) -> str | None:
    """
    Get a configuration value with fallback from environment to new config system.

    Args:
        env_key: Environment variable name
        config_path: Path in new configuration system (for future use)
        default: Default value

    Returns:
        Configuration value or default
    """
    # For now, just use environment variables
    # Future versions will integrate with the configuration manager
    return os.getenv(env_key, default)


def validate_required_keys(required_keys: list[str]) -> dict[str, bool]:
    """
    Validate that required keys are present.

    Args:
        required_keys: List of required environment variable names

    Returns:
        Dictionary mapping key names to their presence status
    """
    status = {}
    for key in required_keys:
        value = os.getenv(key)
        status[key] = bool(value and value.strip())
    return status


def get_api_key_status() -> dict[str, bool]:
    """
    Get status of all API keys.

    Returns:
        Dictionary showing which API keys are configured
    """
    api_keys = {
        "GOOGLE_GENAI_API_KEY": GOOGLE_GENAI_API_KEY,
        "GOOGLE_API_KEY": GOOGLE_API_KEY,
        "X_CLIENT_ID": X_CLIENT_ID,
        "X_CLIENT_SECRET": X_CLIENT_SECRET,
        "BITVAVO_API_KEY": BITVAVO_API_KEY,
        "BITVAVO_API_SECRET": BITVAVO_API_SECRET,
    }

    return {key: bool(value) for key, value in api_keys.items()}
