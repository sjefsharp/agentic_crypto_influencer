"""
Tests for agent classes using pytest best practices.
"""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from agents.publish_agent import PublishAgent
from agents.review_agent import ReviewAgent
from agents.search_agent import SearchAgent
from agents.summary_agent import SummaryAgent

if TYPE_CHECKING:
    from autogen_ext.models.openai import OpenAIChatCompletionClient


@pytest.fixture
def mock_client() -> "OpenAIChatCompletionClient":
    """Mock client for testing agents."""
    return MagicMock()


@pytest.fixture
def review_agent(mock_client: "OpenAIChatCompletionClient") -> ReviewAgent:
    """ReviewAgent instance for testing."""
    return ReviewAgent(mock_client)


@pytest.fixture
def publish_agent(mock_client: "OpenAIChatCompletionClient") -> PublishAgent:
    """PublishAgent instance for testing."""
    return PublishAgent(mock_client)


@pytest.fixture
def summary_agent(mock_client: "OpenAIChatCompletionClient") -> SummaryAgent:
    """SummaryAgent instance for testing."""
    return SummaryAgent(mock_client)


@pytest.fixture
def search_agent(mock_client: "OpenAIChatCompletionClient") -> SearchAgent:
    """SearchAgent instance for testing."""
    return SearchAgent(mock_client)


@pytest.mark.unit
def test_review_agent_init(review_agent: ReviewAgent) -> None:
    """Test ReviewAgent initialization."""
    assert review_agent is not None


@pytest.mark.unit
def test_publish_agent_init(publish_agent: PublishAgent) -> None:
    """Test PublishAgent initialization."""
    assert publish_agent is not None


@pytest.mark.unit
def test_summary_agent_init(summary_agent: SummaryAgent) -> None:
    """Test SummaryAgent initialization."""
    assert summary_agent is not None


@pytest.mark.unit
def test_search_agent_init(search_agent: SearchAgent) -> None:
    """Test SearchAgent initialization."""
    assert search_agent is not None
