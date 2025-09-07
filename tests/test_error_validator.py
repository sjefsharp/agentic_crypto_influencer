"""
Tests for error_management.validator using pytest best practices.
"""

import pytest
from src.agentic_crypto_influencer.error_management.exceptions import ValidationError
from src.agentic_crypto_influencer.error_management.validator import Validator


class TestValidateString:
    """Test cases for validate_string method."""

    @pytest.mark.unit
    def test_validate_string_valid(self) -> None:
        """Test validation with valid string."""
        result = Validator.validate_string("test value", "test_field")
        assert result == "test value"

    @pytest.mark.unit
    def test_validate_string_strip_whitespace(self) -> None:
        """Test string validation with whitespace stripping."""
        result = Validator.validate_string("  test value  ", "test_field")
        assert result == "test value"

    @pytest.mark.unit
    def test_validate_string_required_none(self) -> None:
        """Test validation fails for None when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_string(None, "test_field")

        assert "test_field is required" in str(exc_info.value)
        assert exc_info.value.field == "test_field"

    @pytest.mark.unit
    def test_validate_string_required_empty(self) -> None:
        """Test validation fails for empty string when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_string("", "test_field")

        assert "test_field is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_string_not_required_none(self) -> None:
        """Test validation passes for None when not required."""
        result = Validator.validate_string(None, "test_field", required=False)
        assert result == ""

    @pytest.mark.unit
    def test_validate_string_not_required_empty(self) -> None:
        """Test validation passes for empty string when not required."""
        result = Validator.validate_string("", "test_field", required=False)
        assert result == ""

    @pytest.mark.unit
    def test_validate_string_min_length_valid(self) -> None:
        """Test validation with minimum length constraint."""
        result = Validator.validate_string("hello", "test_field", min_length=3)
        assert result == "hello"

    @pytest.mark.unit
    def test_validate_string_min_length_invalid(self) -> None:
        """Test validation fails when below minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_string("hi", "test_field", min_length=5)

        assert "must be at least 5 characters long" in str(exc_info.value)
        assert exc_info.value.context["min_length"] == 5
        assert exc_info.value.context["actual_length"] == 2

    @pytest.mark.unit
    def test_validate_string_max_length_valid(self) -> None:
        """Test validation with maximum length constraint."""
        result = Validator.validate_string("hello", "test_field", max_length=10)
        assert result == "hello"

    @pytest.mark.unit
    def test_validate_string_max_length_invalid(self) -> None:
        """Test validation fails when exceeding maximum length."""
        long_string = "a" * 20
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_string(long_string, "test_field", max_length=10)

        assert "must not exceed 10 characters" in str(exc_info.value)
        assert exc_info.value.context["max_length"] == 10
        assert exc_info.value.context["actual_length"] == 20

    @pytest.mark.unit
    def test_validate_string_pattern_valid(self) -> None:
        """Test validation with regex pattern match."""
        result = Validator.validate_string("test123", "test_field", pattern=r"^[a-z]+\d+$")
        assert result == "test123"

    @pytest.mark.unit
    def test_validate_string_pattern_invalid(self) -> None:
        """Test validation fails when pattern doesn't match."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_string("TEST123", "test_field", pattern=r"^[a-z]+\d+$")

        assert "does not match required format" in str(exc_info.value)
        assert exc_info.value.context["pattern"] == r"^[a-z]+\d+$"

    @pytest.mark.unit
    def test_validate_string_invalid_regex(self) -> None:
        """Test validation with invalid regex pattern."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_string("test", "test_field", pattern="[")

        assert "Internal validation error" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "regex_error"

    @pytest.mark.unit
    def test_validate_string_type_conversion(self) -> None:
        """Test validation with non-string input."""
        result = Validator.validate_string(123, "test_field")
        assert result == "123"

    @pytest.mark.unit
    def test_validate_string_no_strip(self) -> None:
        """Test validation without stripping whitespace."""
        result = Validator.validate_string("  test  ", "test_field", strip_whitespace=False)
        assert result == "  test  "


class TestValidateInteger:
    """Test cases for validate_integer method."""

    @pytest.mark.unit
    def test_validate_integer_valid(self) -> None:
        """Test validation with valid integer."""
        result = Validator.validate_integer(42, "test_field")
        assert result == 42

    @pytest.mark.unit
    def test_validate_integer_string_valid(self) -> None:
        """Test validation with string integer."""
        result = Validator.validate_integer("42", "test_field")
        assert result == 42

    @pytest.mark.unit
    def test_validate_integer_string_with_whitespace(self) -> None:
        """Test validation with string integer with whitespace."""
        result = Validator.validate_integer("  42  ", "test_field")
        assert result == 42

    @pytest.mark.unit
    def test_validate_integer_required_none(self) -> None:
        """Test validation fails for None when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_integer(None, "test_field")

        assert "test_field is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_integer_required_empty(self) -> None:
        """Test validation fails for empty string when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_integer("", "test_field")

        assert "test_field is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_integer_not_required_none(self) -> None:
        """Test validation passes for None when not required."""
        result = Validator.validate_integer(None, "test_field", required=False)
        assert result is None

    @pytest.mark.unit
    def test_validate_integer_invalid_string(self) -> None:
        """Test validation fails for invalid integer string."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_integer("not_a_number", "test_field")

        assert "must be a valid integer" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "type_conversion"

    @pytest.mark.unit
    def test_validate_integer_min_value_valid(self) -> None:
        """Test validation with minimum value constraint."""
        result = Validator.validate_integer(10, "test_field", min_value=5)
        assert result == 10

    @pytest.mark.unit
    def test_validate_integer_min_value_invalid(self) -> None:
        """Test validation fails when below minimum value."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_integer(3, "test_field", min_value=5)

        assert "must be at least 5" in str(exc_info.value)
        assert exc_info.value.context["min_value"] == 5

    @pytest.mark.unit
    def test_validate_integer_max_value_valid(self) -> None:
        """Test validation with maximum value constraint."""
        result = Validator.validate_integer(5, "test_field", max_value=10)
        assert result == 5

    @pytest.mark.unit
    def test_validate_integer_max_value_invalid(self) -> None:
        """Test validation fails when exceeding maximum value."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_integer(15, "test_field", max_value=10)

        assert "must not exceed 10" in str(exc_info.value)
        assert exc_info.value.context["max_value"] == 10


class TestValidateUrl:
    """Test cases for validate_url method."""

    @pytest.mark.unit
    def test_validate_url_valid_http(self) -> None:
        """Test validation with valid HTTP URL."""
        result = Validator.validate_url("http://example.com", "test_field")
        assert result == "http://example.com"

    @pytest.mark.unit
    def test_validate_url_valid_https(self) -> None:
        """Test validation with valid HTTPS URL."""
        result = Validator.validate_url("https://example.com", "test_field")
        assert result == "https://example.com"

    @pytest.mark.unit
    def test_validate_url_required_none(self) -> None:
        """Test validation fails for None when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_url(None, "test_field")

        assert "test_field is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_url_not_required_none(self) -> None:
        """Test validation passes for None when not required."""
        result = Validator.validate_url(None, "test_field", required=False)
        assert result is None

    @pytest.mark.unit
    def test_validate_url_invalid_format(self) -> None:
        """Test validation fails for invalid URL format."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_url("not_a_url", "test_field")

        assert "must include a scheme" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "missing_scheme"

    @pytest.mark.unit
    def test_validate_url_scheme_restriction(self) -> None:
        """Test validation with allowed schemes restriction."""
        result = Validator.validate_url(
            "https://example.com", "test_field", allowed_schemes=["https"]
        )
        assert result == "https://example.com"

    @pytest.mark.unit
    def test_validate_url_invalid_scheme(self) -> None:
        """Test validation fails for disallowed scheme."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_url(
                "ftp://example.com", "test_field", allowed_schemes=["http", "https"]
            )

        assert "must use one of these schemes" in str(exc_info.value)
        assert exc_info.value.context["allowed_schemes"] == ["http", "https"]

    @pytest.mark.unit
    def test_validate_url_type_conversion(self) -> None:
        """Test validation with non-string URL input."""
        result = Validator.validate_url("https://example.com", "test_field")
        assert result == "https://example.com"

    @pytest.mark.unit
    def test_validate_url_missing_scheme(self) -> None:
        """Test validation fails for URL without scheme."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_url("example.com", "test_field")

        assert "must include a scheme" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "missing_scheme"

    @pytest.mark.unit
    def test_validate_url_missing_domain(self) -> None:
        """Test validation fails for URL without domain."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_url("https://", "test_field")

        assert "must include a valid domain" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "missing_domain"


class TestValidateEmail:
    """Test cases for validate_email method."""

    @pytest.mark.unit
    def test_validate_email_valid(self) -> None:
        """Test validation with valid email."""
        result = Validator.validate_email("test@example.com", "test_field")
        assert result == "test@example.com"

    @pytest.mark.unit
    def test_validate_email_uppercase(self) -> None:
        """Test validation converts email to lowercase."""
        result = Validator.validate_email("TEST@EXAMPLE.COM", "test_field")
        assert result == "test@example.com"

    @pytest.mark.unit
    def test_validate_email_required_none(self) -> None:
        """Test validation fails for None when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_email(None, "test_field")

        assert "test_field is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_email_not_required_none(self) -> None:
        """Test validation passes for None when not required."""
        result = Validator.validate_email(None, "test_field", required=False)
        assert result is None

    @pytest.mark.unit
    def test_validate_email_invalid_format(self) -> None:
        """Test validation fails for invalid email format."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_email("invalid-email", "test_field")

        assert "must be a valid email address" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "email_format"

    @pytest.mark.unit
    def test_validate_email_consecutive_dots(self) -> None:
        """Test validation fails for consecutive dots."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_email("test..user@example.com", "test_field")

        assert "cannot contain consecutive dots" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "consecutive_dots"

    @pytest.mark.unit
    def test_validate_email_too_long(self) -> None:
        """Test validation fails for email that's too long."""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_email(long_email, "test_field")

        assert "is too long" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "email_too_long"


class TestValidateChoice:
    """Test cases for validate_choice method."""

    @pytest.mark.unit
    def test_validate_choice_valid(self) -> None:
        """Test validation with valid choice."""
        result = Validator.validate_choice("option1", "test_field", ["option1", "option2"])
        assert result == "option1"

    @pytest.mark.unit
    def test_validate_choice_case_sensitive(self) -> None:
        """Test validation with case sensitive choices."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_choice("OPTION1", "test_field", ["option1", "option2"])

        assert "must be one of" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_choice_case_insensitive(self) -> None:
        """Test validation with case insensitive choices."""
        result = Validator.validate_choice(
            "OPTION1", "test_field", ["option1", "option2"], case_sensitive=False
        )
        assert result == "option1"  # Returns original case from choices

    @pytest.mark.unit
    def test_validate_choice_required_none(self) -> None:
        """Test validation fails for None when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_choice(None, "test_field", ["option1", "option2"])

        assert "test_field is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_choice_not_required_none(self) -> None:
        """Test validation passes for None when not required."""
        result = Validator.validate_choice(
            None, "test_field", ["option1", "option2"], required=False
        )
        assert result is None

    @pytest.mark.unit
    def test_validate_choice_invalid(self) -> None:
        """Test validation fails for invalid choice."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_choice("option3", "test_field", ["option1", "option2"])

        assert "must be one of: option1, option2" in str(exc_info.value)
        assert exc_info.value.context["choices"] == ["option1", "option2"]


class TestValidateDict:
    """Test cases for validate_dict method."""

    @pytest.mark.unit
    def test_validate_dict_valid(self) -> None:
        """Test validation with valid dictionary."""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = Validator.validate_dict(test_dict, "test_field")
        assert result == test_dict

    @pytest.mark.unit
    def test_validate_dict_required_none(self) -> None:
        """Test validation fails for None when required."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_dict(None, "test_field")

        assert "test_field is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_dict_not_required_none(self) -> None:
        """Test validation passes for None when not required."""
        result = Validator.validate_dict(None, "test_field", required=False)
        assert result is None

    @pytest.mark.unit
    def test_validate_dict_not_dict(self) -> None:
        """Test validation fails for non-dictionary."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_dict("not a dict", "test_field")

        assert "must be a dictionary" in str(exc_info.value)
        assert exc_info.value.context["expected_type"] == "dict"

    @pytest.mark.unit
    def test_validate_dict_required_keys_present(self) -> None:
        """Test validation with required keys present."""
        test_dict = {"key1": "value1", "key2": "value2", "key3": "value3"}
        result = Validator.validate_dict(test_dict, "test_field", required_keys=["key1", "key2"])
        assert result == test_dict

    @pytest.mark.unit
    def test_validate_dict_required_keys_missing(self) -> None:
        """Test validation fails when required keys are missing."""
        test_dict = {"key1": "value1"}
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_dict(test_dict, "test_field", required_keys=["key1", "key2"])

        assert "is missing required keys: key2" in str(exc_info.value)
        assert exc_info.value.context["missing_keys"] == ["key2"]


class TestConvenienceFunctions:
    """Test cases for convenience validation functions."""

    @pytest.mark.unit
    def test_validate_api_key_valid(self) -> None:
        """Test API key validation with valid key."""
        from src.agentic_crypto_influencer.error_management.validator import validate_api_key

        result = validate_api_key("valid_api_key_123456", "TestService")
        assert result == "valid_api_key_123456"

    @pytest.mark.unit
    def test_validate_api_key_too_short(self) -> None:
        """Test API key validation fails for short key."""
        from src.agentic_crypto_influencer.error_management.validator import validate_api_key

        with pytest.raises(ValidationError):
            validate_api_key("short", "TestService")

    @pytest.mark.unit
    def test_validate_tweet_content_valid(self) -> None:
        """Test tweet content validation with valid content."""
        from src.agentic_crypto_influencer.error_management.validator import validate_tweet_content

        result = validate_tweet_content("This is a valid tweet content!")
        assert result == "This is a valid tweet content!"

    @pytest.mark.unit
    def test_validate_tweet_content_too_long(self) -> None:
        """Test tweet content validation fails for content too long."""
        from src.agentic_crypto_influencer.error_management.validator import validate_tweet_content

        long_content = "a" * 281
        with pytest.raises(ValidationError):
            validate_tweet_content(long_content)

    @pytest.mark.unit
    def test_validate_user_id_valid(self) -> None:
        """Test user ID validation with valid ID."""
        from src.agentic_crypto_influencer.error_management.validator import validate_user_id

        result = validate_user_id("valid_user_123", "twitter")
        assert result == "valid_user_123"

    @pytest.mark.unit
    def test_validate_user_id_invalid_chars(self) -> None:
        """Test user ID validation fails for invalid characters."""
        from src.agentic_crypto_influencer.error_management.validator import validate_user_id

        with pytest.raises(ValidationError):
            validate_user_id("invalid@user", "twitter")
