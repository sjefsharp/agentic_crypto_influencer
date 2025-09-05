"""
Application-wide constants for validation, limits, and general configuration.
Contains numeric constants, limits, and other application settings.
"""

# Character Limits
MAX_TWEET_LENGTH = 280
MIN_STRING_LENGTH_DEFAULT = 1

# Time Constants (in seconds)
TIMEOUT_DEFAULT = 30
RETRY_DELAY_DEFAULT = 1
RETRY_MAX_ATTEMPTS_DEFAULT = 3

# Cache and Storage Limits
MAX_ACTIVITIES_CACHE = 50
TOKEN_CACHE_DURATION = 600  # 10 minutes

# API Rate Limiting
RATE_LIMIT_WINDOW = 900  # 15 minutes
RATE_LIMIT_MAX_REQUESTS = 100

# Circuit Breaker Settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # seconds
CIRCUIT_BREAKER_HALF_OPEN_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL_DEFAULT = "INFO"
LOG_FORMAT_JSON = "json"
LOG_FORMAT_CONSOLE = "console"

# Validation Patterns
PATTERN_EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PATTERN_URL_SCHEME = r"^https?://"
PATTERN_API_KEY_MIN_LENGTH = 10

# HTTP Status Codes
HTTP_STATUS_OK = 200
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

# Environment Detection
ENV_VAR_PORT = "PORT"
ENV_VAR_LOG_LEVEL = "LOG_LEVEL"
ENV_VAR_FLASK_SECRET = "FLASK_SECRET_KEY"

# Market Data
DEFAULT_MARKET_SYMBOL = "BTC-EUR"
MARKET_DATA_CACHE_DURATION = 60  # 1 minute

# Agent Names (moved from individual files for consistency)
AGENT_NAME_SEARCH = "SearchAgent"
AGENT_NAME_SUMMARY = "SummaryAgent"
AGENT_NAME_PUBLISH = "PublishAgent"
AGENT_NAME_REVIEW = "ReviewAgent"

# Tool Names
TOOL_NAME_VALIDATOR = "LengthValidator"
TOOL_NAME_BITVAVO = "BitvavoHandler"
TOOL_NAME_OAUTH = "OAuthHandler"
TOOL_NAME_REDIS = "RedisHandler"
TOOL_NAME_POST = "PostHandler"
TOOL_NAME_TRENDS = "TrendsHandler"

# Component Names for Logging
COMPONENT_CIRCUIT_BREAKER = "circuit_breaker"
COMPONENT_ERROR_MANAGEMENT = "error_management"
COMPONENT_RETRY = "retry"
