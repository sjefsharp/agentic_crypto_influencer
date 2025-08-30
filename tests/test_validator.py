"""
Tests for Validator using pytest best practices.
"""

import pytest

from tools.validator import Validator


@pytest.mark.unit
def test_validate_length_within_bounds() -> None:
    """Test validation with length within bounds."""
    result = Validator.validate_length("Hello World", min_length=5, max_length=20)
    assert result is True


@pytest.mark.unit
def test_validate_length_at_min_boundary() -> None:
    """Test validation at minimum length boundary."""
    result = Validator.validate_length("Hi", min_length=2, max_length=10)
    assert result is True


@pytest.mark.unit
def test_validate_length_at_max_boundary() -> None:
    """Test validation at maximum length boundary."""
    result = Validator.validate_length("Hello", min_length=1, max_length=5)
    assert result is True


@pytest.mark.unit
def test_validate_length_below_min() -> None:
    """Test validation with length below minimum."""
    result = Validator.validate_length("Hi", min_length=5, max_length=10)
    assert result is False


@pytest.mark.unit
def test_validate_length_above_max() -> None:
    """Test validation with length above maximum."""
    result = Validator.validate_length(
        "This is a very long string that exceeds the maximum length",
        min_length=1,
        max_length=20,
    )
    assert result is False


@pytest.mark.unit
def test_validate_length_empty_string() -> None:
    """Test validation with empty string."""
    result = Validator.validate_length("", min_length=1, max_length=10)
    assert result is False


@pytest.mark.unit
def test_validate_length_default_bounds() -> None:
    """Test validation with default bounds (1-280)."""
    result = Validator.validate_length("Valid string")
    assert result is True


@pytest.mark.unit
def test_validate_length_empty_string_default_min() -> None:
    """Test validation with empty string and default minimum."""
    result = Validator.validate_length("")
    assert result is False
