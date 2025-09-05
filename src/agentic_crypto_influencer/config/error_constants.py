"""
Error messages and validation patterns for consistent error handling.
Contains all hardcoded error messages used throughout the application.
"""

# Validation Error Messages
ERROR_VALIDATION_GENERAL = "VALIDATION_ERROR"
ERROR_URL_SCHEME_REQUIRED = "%s must include a scheme (e.g., https://)"

# API Error Messages
ERROR_API_CONNECTION = "API_CONNECTION_ERROR"
ERROR_API_TIMEOUT = "API_TIMEOUT_ERROR"
ERROR_API_RATE_LIMIT = "API_RATE_LIMIT_ERROR"
ERROR_API_AUTHENTICATION = "API_AUTHENTICATION_ERROR"

# Configuration Error Messages
ERROR_CONFIG_MISSING_API_CREDENTIALS = "Missing or invalid Bitvavo API credentials"
ERROR_CONFIG_MISSING_VALUE = "Missing configuration value"

# Circuit Breaker Messages
CIRCUIT_BREAKER_CLOSED_RECOVERY = "Circuit breaker for %s closed after successful recovery"
CIRCUIT_BREAKER_OPENED_FAILURES = "Circuit breaker for %s opened after %s failures"
CIRCUIT_BREAKER_REOPENED_FAILURE = (
    "Circuit breaker for %s re-opened due to failure in half-open state"
)
CIRCUIT_BREAKER_HALF_OPEN = "Circuit breaker for %s entering half-open state"
CIRCUIT_BREAKER_IS_OPEN = "Circuit breaker is open for %s"

# Retry Error Messages
RETRY_NON_RETRYABLE = "Non-retryable error in %s: %s: %s"
RETRY_ATTEMPTS_EXHAUSTED = "All retry attempts exhausted for %s"
RETRY_ATTEMPT_MESSAGE = "Retrying %s (attempt %s/%s) after %s seconds delay"

# Data Processing Error Messages
ERROR_DATA_PROCESSING = "DATA_PROCESSING_ERROR"
ERROR_INVALID_DATA_FORMAT = "Invalid data format"
ERROR_MISSING_REQUIRED_FIELD = "Missing required field: %s"

# X API Specific Error Messages
ERROR_X_TOKEN_INVALID = "Invalid or expired X API token"
ERROR_X_POST_FAILED = "Failed to post to X API"
ERROR_X_AUTH_FAILED = "X API authentication failed"

# Bitvavo API Error Messages
ERROR_BITVAVO_CONNECTION = "Failed to connect to Bitvavo API"
ERROR_BITVAVO_MARKET_DATA = "Failed to fetch market data"
ERROR_BITVAVO_INVALID_MARKET = "Invalid market symbol"

# Generic Success Messages
SUCCESS_OPERATION_COMPLETED = "Operation completed successfully"
SUCCESS_CONNECTION_ESTABLISHED = "Connection established"
SUCCESS_DATA_RETRIEVED = "Data retrieved successfully"
