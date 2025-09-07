"""
Unit tests for scheduler constants module.
Tests constant definitions and configuration values.
"""

from src.agentic_crypto_influencer.config.scheduler_constants import (
    CRON_PRESETS,
    GRAPHFLOW_STATUS_RUNNING,
    GRAPHFLOW_STATUS_STOPPED,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
    JOB_TYPE_GRAPHFLOW,
    JOB_TYPE_SINGLE_POST,
    REDIS_KEY_GRAPHFLOW_PID,
    REDIS_KEY_GRAPHFLOW_STATUS,
    REDIS_KEY_JOBS,
    SCHEDULER_TIMEZONE,
    TIMEZONE_OPTIONS,
)


class TestSchedulerConstants:
    """Test cases for scheduler constants."""

    def test_job_types_are_strings(self) -> None:
        """Test that job types are defined as strings."""
        assert isinstance(JOB_TYPE_GRAPHFLOW, str)
        assert isinstance(JOB_TYPE_SINGLE_POST, str)
        assert JOB_TYPE_GRAPHFLOW != ""
        assert JOB_TYPE_SINGLE_POST != ""

    def test_job_status_constants_are_strings(self) -> None:
        """Test that job status constants are defined as strings."""
        statuses = [
            JOB_STATUS_PENDING,
            JOB_STATUS_RUNNING,
            JOB_STATUS_COMPLETED,
            JOB_STATUS_FAILED,
        ]

        for status in statuses:
            assert isinstance(status, str)
            assert status != ""

        # Verify unique values
        assert len(statuses) == len(set(statuses))

    def test_graphflow_status_constants(self) -> None:
        """Test that GraphFlow status constants are defined."""
        assert isinstance(GRAPHFLOW_STATUS_RUNNING, str)
        assert isinstance(GRAPHFLOW_STATUS_STOPPED, str)
        assert GRAPHFLOW_STATUS_RUNNING != ""
        assert GRAPHFLOW_STATUS_STOPPED != ""

    def test_redis_keys_are_strings(self) -> None:
        """Test that Redis keys are defined as strings."""
        redis_keys = [
            REDIS_KEY_GRAPHFLOW_PID,
            REDIS_KEY_GRAPHFLOW_STATUS,
            REDIS_KEY_JOBS,
        ]

        for key in redis_keys:
            assert isinstance(key, str)
            assert key != ""

        # Verify unique values
        assert len(redis_keys) == len(set(redis_keys))

    def test_cron_presets_structure(self) -> None:
        """Test that cron presets have correct structure."""
        assert isinstance(CRON_PRESETS, dict)
        assert len(CRON_PRESETS) > 0

        for name, expression in CRON_PRESETS.items():
            assert isinstance(name, str)
            assert isinstance(expression, str)
            assert expression != ""

    def test_timezone_options_structure(self) -> None:
        """Test that timezone options have correct structure."""
        assert isinstance(TIMEZONE_OPTIONS, list)
        assert len(TIMEZONE_OPTIONS) > 0

        for timezone_tuple in TIMEZONE_OPTIONS:
            assert isinstance(timezone_tuple, tuple)
            assert len(timezone_tuple) == 2
            assert isinstance(timezone_tuple[0], str)
            assert isinstance(timezone_tuple[1], str)

    def test_default_timezone_is_valid(self) -> None:
        """Test that default timezone is valid."""
        assert isinstance(SCHEDULER_TIMEZONE, str)
        assert SCHEDULER_TIMEZONE != ""

    def test_cron_presets_have_valid_expressions(self) -> None:
        """Test that cron preset expressions follow expected format."""
        for name, expression in CRON_PRESETS.items():
            parts = expression.split()

            # Cron expressions should have 5 parts for this simple format
            assert len(parts) == 5, f"Invalid cron expression for {name}: {expression}"

    def test_constant_values_uniqueness(self) -> None:
        """Test that important constants have unique values."""
        # Job types should be unique
        job_types = [JOB_TYPE_GRAPHFLOW, JOB_TYPE_SINGLE_POST]
        assert len(job_types) == len(set(job_types))

    def test_redis_key_prefixes(self) -> None:
        """Test that Redis keys follow consistent naming pattern."""
        redis_keys = [
            REDIS_KEY_GRAPHFLOW_PID,
            REDIS_KEY_GRAPHFLOW_STATUS,
            REDIS_KEY_JOBS,
        ]

        # Check that keys don't accidentally conflict
        assert len(redis_keys) == len(set(redis_keys))

        # Keys should not be empty or just whitespace
        for key in redis_keys:
            assert key.strip() != ""

    def test_cron_presets_completeness(self) -> None:
        """Test that cron presets include common scheduling patterns."""
        preset_names = set(CRON_PRESETS.keys())

        # Should include some hourly patterns
        hourly_patterns = ["every_hour", "every_2_hours", "every_4_hours"]
        found_hourly = any(pattern in preset_names for pattern in hourly_patterns)
        assert found_hourly, "Should include some hourly patterns"

    def test_constants_are_not_none(self) -> None:
        """Test that all important constants are not None."""
        constants_to_check = [
            JOB_TYPE_GRAPHFLOW,
            JOB_TYPE_SINGLE_POST,
            JOB_STATUS_PENDING,
            JOB_STATUS_RUNNING,
            JOB_STATUS_COMPLETED,
            JOB_STATUS_FAILED,
            REDIS_KEY_GRAPHFLOW_PID,
            REDIS_KEY_GRAPHFLOW_STATUS,
            REDIS_KEY_JOBS,
            SCHEDULER_TIMEZONE,
            CRON_PRESETS,
            TIMEZONE_OPTIONS,
            GRAPHFLOW_STATUS_RUNNING,
            GRAPHFLOW_STATUS_STOPPED,
        ]

        for constant in constants_to_check:
            assert constant is not None
