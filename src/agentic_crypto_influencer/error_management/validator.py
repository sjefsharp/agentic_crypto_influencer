"""
Enhanced input validation with comprehensive error handling.

This module provides robust validation functions with detailed error messages
and context for better user experience and debugging.
"""

import re
from typing import Any
from urllib.parse import urlparse

from src.agentic_crypto_influencer.config.logging_config import get_logger
from src.agentic_crypto_influencer.error_management.exceptions import ValidationError

logger = get_logger("error_management.validation")


class Validator:
    """Comprehensive validation utility with detailed error reporting."""

    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        min_length: int = 0,
        max_length: int | None = None,
        pattern: str | None = None,
        required: bool = True,
        strip_whitespace: bool = True,
    ) -> str:
        """
        Validate string input with comprehensive checks.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            min_length: Minimum required length
            max_length: Maximum allowed length
            pattern: Regex pattern to match
            required: Whether the field is required
            strip_whitespace: Whether to strip leading/trailing whitespace

        Returns:
            Validated and optionally stripped string

        Raises:
            ValidationError: If validation fails
        """
        # Handle None/empty values
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                raise ValidationError(
                    f"{field_name} is required",
                    field=field_name,
                    value=value,
                    context={"validation_type": "required"},
                )
            return ""

        # Convert to string if not already
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception as e:
                raise ValidationError(
                    f"{field_name} must be convertible to string",
                    field=field_name,
                    value=value,
                    context={"validation_type": "type_conversion", "original_error": str(e)},
                ) from e

        # Strip whitespace if requested
        if strip_whitespace:
            value = value.strip()

        # Check length constraints
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters long",
                field=field_name,
                value=value,
                context={
                    "validation_type": "min_length",
                    "min_length": min_length,
                    "actual_length": len(value),
                },
            )

        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must not exceed {max_length} characters",
                field=field_name,
                value=value[:100],  # Truncate for logging
                context={
                    "validation_type": "max_length",
                    "max_length": max_length,
                    "actual_length": len(value),
                },
            )

        # Check pattern if provided
        if pattern is not None:
            try:
                if not re.match(pattern, value):
                    raise ValidationError(
                        f"{field_name} does not match required format",
                        field=field_name,
                        value=value[:100],  # Truncate for logging
                        context={"validation_type": "pattern", "pattern": pattern},
                    )
            except re.error as e:
                logger.error(
                    f"Invalid regex pattern for {field_name}: {pattern}", extra={"error": str(e)}
                )
                raise ValidationError(
                    f"Internal validation error for {field_name}",
                    field=field_name,
                    value=value[:100],
                    context={"validation_type": "regex_error", "regex_error": str(e)},
                ) from e

        return str(value)

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        min_value: int | None = None,
        max_value: int | None = None,
        required: bool = True,
    ) -> int | None:
        """
        Validate integer input.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            required: Whether the field is required

        Returns:
            Validated integer or None if not required and empty

        Raises:
            ValidationError: If validation fails
        """
        if value is None or value == "":
            if required:
                raise ValidationError(
                    f"{field_name} is required",
                    field=field_name,
                    value=value,
                    context={"validation_type": "required"},
                )
            return None

        # Try to convert to integer
        try:
            if isinstance(value, str):
                value = value.strip()
            int_value = int(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"{field_name} must be a valid integer",
                field=field_name,
                value=value,
                context={"validation_type": "type_conversion", "original_error": str(e)},
            ) from e

        # Check range constraints
        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field=field_name,
                value=int_value,
                context={"validation_type": "min_value", "min_value": min_value},
            )

        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} must not exceed {max_value}",
                field=field_name,
                value=int_value,
                context={"validation_type": "max_value", "max_value": max_value},
            )

        return int_value

    @staticmethod
    def validate_url(
        value: Any,
        field_name: str,
        required: bool = True,
        allowed_schemes: list[str] | None = None,
    ) -> str | None:
        """
        Validate URL format.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            required: Whether the field is required
            allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])

        Returns:
            Validated URL or None if not required and empty

        Raises:
            ValidationError: If validation fails
        """
        if allowed_schemes is None:
            allowed_schemes = ["http", "https"]

        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                raise ValidationError(
                    f"{field_name} is required",
                    field=field_name,
                    value=value,
                    context={"validation_type": "required"},
                )
            return None

        url_str = str(value).strip()

        try:
            parsed = urlparse(url_str)
        except Exception as e:
            raise ValidationError(
                f"{field_name} must be a valid URL",
                field=field_name,
                value=url_str,
                context={"validation_type": "url_parse", "original_error": str(e)},
            ) from e

        # Check scheme
        if not parsed.scheme:
            raise ValidationError(
                f"{field_name} must include a scheme (e.g., https://)",
                field=field_name,
                value=url_str,
                context={"validation_type": "missing_scheme", "allowed_schemes": allowed_schemes},
            )

        if parsed.scheme.lower() not in [s.lower() for s in allowed_schemes]:
            raise ValidationError(
                f"{field_name} must use one of these schemes: {', '.join(allowed_schemes)}",
                field=field_name,
                value=url_str,
                context={
                    "validation_type": "invalid_scheme",
                    "scheme": parsed.scheme,
                    "allowed_schemes": allowed_schemes,
                },
            )

        # Check netloc (domain)
        if not parsed.netloc:
            raise ValidationError(
                f"{field_name} must include a valid domain",
                field=field_name,
                value=url_str,
                context={"validation_type": "missing_domain"},
            )

        return url_str

    @staticmethod
    def validate_email(value: Any, field_name: str, required: bool = True) -> str | None:
        """
        Validate email format.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            required: Whether the field is required

        Returns:
            Validated email or None if not required and empty

        Raises:
            ValidationError: If validation fails
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                raise ValidationError(
                    f"{field_name} is required",
                    field=field_name,
                    value=value,
                    context={"validation_type": "required"},
                )
            return None

        email_str = str(value).strip().lower()

        # Basic email pattern (more comprehensive than simple regex)
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email_str):
            raise ValidationError(
                f"{field_name} must be a valid email address",
                field=field_name,
                value=email_str,
                context={"validation_type": "email_format"},
            )

        # Additional checks
        if ".." in email_str:
            raise ValidationError(
                f"{field_name} cannot contain consecutive dots",
                field=field_name,
                value=email_str,
                context={"validation_type": "consecutive_dots"},
            )

        if len(email_str) > 254:  # RFC 5321 limit
            raise ValidationError(
                f"{field_name} is too long (maximum 254 characters)",
                field=field_name,
                value=email_str[:100],
                context={"validation_type": "email_too_long", "length": len(email_str)},
            )

        return email_str

    @staticmethod
    def validate_choice(
        value: Any,
        field_name: str,
        choices: list[Any],
        required: bool = True,
        case_sensitive: bool = True,
    ) -> Any | None:
        """
        Validate that value is one of the allowed choices.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            choices: List of allowed values
            required: Whether the field is required
            case_sensitive: Whether string comparison should be case sensitive

        Returns:
            Validated choice or None if not required and empty

        Raises:
            ValidationError: If validation fails
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                raise ValidationError(
                    f"{field_name} is required",
                    field=field_name,
                    value=value,
                    context={"validation_type": "required", "choices": choices},
                )
            return None

        # For string comparisons, handle case sensitivity
        if isinstance(value, str) and not case_sensitive:
            value_to_check = value.lower()
            choices_to_check = [str(c).lower() if isinstance(c, str) else c for c in choices]
        else:
            value_to_check = value
            choices_to_check = choices

        if value_to_check not in choices_to_check:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(map(str, choices))}",
                field=field_name,
                value=value,
                context={
                    "validation_type": "invalid_choice",
                    "choices": choices,
                    "case_sensitive": case_sensitive,
                },
            )

        # Return original case if case insensitive match
        if isinstance(value, str) and not case_sensitive:
            for original_choice in choices:
                if isinstance(original_choice, str) and original_choice.lower() == value.lower():
                    return original_choice

        return value

    @staticmethod
    def validate_dict(
        value: Any, field_name: str, required_keys: list[str] | None = None, required: bool = True
    ) -> dict[str, Any] | None:
        """
        Validate dictionary input.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            required_keys: List of keys that must be present
            required: Whether the field is required

        Returns:
            Validated dictionary or None if not required and empty

        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if required:
                raise ValidationError(
                    f"{field_name} is required",
                    field=field_name,
                    value=value,
                    context={"validation_type": "required"},
                )
            return None

        if not isinstance(value, dict):
            raise ValidationError(
                f"{field_name} must be a dictionary",
                field=field_name,
                value=type(value).__name__,
                context={"validation_type": "type_mismatch", "expected_type": "dict"},
            )

        # Check required keys
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                raise ValidationError(
                    f"{field_name} is missing required keys: {', '.join(missing_keys)}",
                    field=field_name,
                    value=list(value.keys()),  # type: ignore[arg-type]
                    context={
                        "validation_type": "missing_keys",
                        "missing_keys": missing_keys,
                        "required_keys": required_keys,
                    },
                )

        return value  # type: ignore[return-value]


# Convenience function for validating API keys
def validate_api_key(key: Any, service_name: str) -> str:
    """Validate API key format and presence."""
    return Validator.validate_string(
        key,
        f"{service_name} API key",
        min_length=10,
        max_length=500,
        required=True,
        strip_whitespace=True,
    )


# Convenience function for validating tweet content
def validate_tweet_content(content: Any) -> str:
    """Validate tweet content according to X/Twitter requirements."""
    validated_content = Validator.validate_string(
        content,
        "tweet content",
        min_length=1,
        max_length=280,
        required=True,
        strip_whitespace=True,
    )

    # Additional checks for tweet content
    if len(validated_content.encode("utf-8")) > 280 * 4:  # Unicode characters can be up to 4 bytes
        raise ValidationError(
            "Tweet content contains too many multi-byte characters",
            field="tweet_content",
            value=validated_content[:100],
            context={
                "validation_type": "encoding_length",
                "byte_length": len(validated_content.encode("utf-8")),
            },
        )

    return validated_content


# Convenience function for validating user IDs
def validate_user_id(user_id: Any, service_name: str = "user") -> str:
    """Validate user ID format."""
    return Validator.validate_string(
        user_id,
        f"{service_name} ID",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        required=True,
        strip_whitespace=True,
    )
