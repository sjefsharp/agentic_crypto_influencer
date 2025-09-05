"""
Redis key constants for consistent key naming across the application.
Prevents hardcoded strings in Redis operations.
"""

# OAuth Related Keys
REDIS_KEY_ACCESS_TOKEN = "access_token"  # nosec B105
REDIS_KEY_OAUTH_CODE_VERIFIER = "oauth_code_verifier"
REDIS_KEY_OAUTH_STATE = "oauth_state"
REDIS_KEY_TOKEN = "token"  # nosec B105

# Token Expiration Times (in seconds)
OAUTH_CODE_VERIFIER_EXPIRY = 600  # 10 minutes
OAUTH_STATE_EXPIRY = 600  # 10 minutes

# Error Messages
ERROR_REDIS_URL_MISSING = "REDIS_URL must be set in the environment variables."
ERROR_REDIS_CONNECTION = "Could not connect to Redis."
ERROR_REDIS_GET_KEY = "Failed to get key '%s' from Redis: %s"
ERROR_REDIS_SET_KEY = "Failed to set key '%s' in Redis: %s"
ERROR_REDIS_KEY_RETRIEVAL = "Error retrieving key '%s' from Redis: %s"
ERROR_REDIS_KEY_SET = "Error setting key '%s' in Redis: %s"

# Log Messages
LOG_REDIS_CONNECTED = "Connected to Redis at %s"
LOG_REDIS_CONNECTION_FAILED = "Failed to connect to Redis at %s: %s"
