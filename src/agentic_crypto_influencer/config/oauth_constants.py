"""
OAuth authentication flow constants.
Contains endpoints, scopes, error messages and flow-specific configurations.
"""

# OAuth Flow Constants
OAUTH_CODE_CHALLENGE_METHOD = "S256"
OAUTH_REDIRECT_URI_LOCAL = "http://localhost:5000/callback"

# OAuth Scopes
OAUTH_SCOPE_TWEET_READ = "tweet.read"
OAUTH_SCOPE_TWEET_WRITE = "tweet.write"
OAUTH_SCOPE_USERS_READ = "users.read"
OAUTH_SCOPE_OFFLINE_ACCESS = "offline.access"

# Default OAuth Scopes List
OAUTH_DEFAULT_SCOPES = [
    OAUTH_SCOPE_TWEET_READ,
    OAUTH_SCOPE_TWEET_WRITE,
    OAUTH_SCOPE_USERS_READ,
    OAUTH_SCOPE_OFFLINE_ACCESS,
]

# X API Endpoints (fallbacks if not in environment)
X_AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
X_TOKEN_URL_FALLBACK = "https://api.x.com/2/oauth2/token"  # nosec B105

# OAuth Error Messages
ERROR_CODE_VERIFIER_NOT_FOUND = "Code verifier not found in Redis"
ERROR_TOKENS_NOT_FOUND = "No tokens found in Redis"
ERROR_INVALID_TOKENS = "Invalid tokens format in Redis"
ERROR_TOKEN_REFRESH_FAILED = "Failed to refresh access token"  # nosec B105

# OAuth Success Messages
SUCCESS_TOKENS_SAVED = "Tokens successfully saved to Redis."
SUCCESS_URL_GENERATED = "Authorization URL generated with PKCE S256 method"
SUCCESS_PLEASE_AUTHORIZE = "Please go to %s and authorize the application."

# Token Structure Keys
TOKEN_KEY_ACCESS_TOKEN = "access_token"  # nosec B105
TOKEN_KEY_REFRESH_TOKEN = "refresh_token"  # nosec B105
TOKEN_KEY_TOKEN_TYPE = "token_type"  # nosec B105
TOKEN_KEY_EXPIRES_AT = "expires_at"  # nosec B105

# Default Token Values
TOKEN_TYPE_BEARER = "bearer"  # nosec B105

# HTTP Headers
HEADER_AUTHORIZATION = "Authorization"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_BASIC_PREFIX = "Basic"
HEADER_BEARER_PREFIX = "Bearer"
CONTENT_TYPE_FORM_URLENCODED = "application/x-www-form-urlencoded"

# OAuth Grant Types
GRANT_TYPE_AUTHORIZATION_CODE = "authorization_code"
GRANT_TYPE_REFRESH_TOKEN = "refresh_token"  # nosec B105
