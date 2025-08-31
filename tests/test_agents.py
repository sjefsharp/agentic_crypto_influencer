"""
Tests for agent classes using pytest best practices.
"""

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from src.agentic_crypto_influencer.agents.publish_agent import PublishAgent
from src.agentic_crypto_influencer.agents.review_agent import ReviewAgent
from src.agentic_crypto_influencer.agents.search_agent import SearchAgent
from src.agentic_crypto_influencer.agents.summary_agent import SummaryAgent

if TYPE_CHECKING:
    from autogen_ext.models.openai import OpenAIChatCompletionClient


@pytest.fixture  # type: ignore[misc]
def mock_client() -> "OpenAIChatCompletionClient":
    """Mock client for testing agents."""
    mock = Mock()
    # Mock the model_info attribute that autogen expects
    mock.model_info = {"function_calling": True}
    return mock


@pytest.fixture  # type: ignore[misc]
def review_agent(mock_client: "OpenAIChatCompletionClient") -> ReviewAgent:
    """ReviewAgent instance for testing."""
    return ReviewAgent(mock_client)


@pytest.fixture  # type: ignore[misc]
def publish_agent(mock_client: "OpenAIChatCompletionClient") -> PublishAgent:
    """PublishAgent instance for testing."""

    # Create a simple stub function with proper type hints
    def mock_post(post: str) -> dict[str, str]:
        return {"status": "success", "id": "123"}

    with patch("src.agentic_crypto_influencer.agents.publish_agent.X") as mock_x:
        mock_x.return_value.post = mock_post
        return PublishAgent(mock_client)


@pytest.fixture  # type: ignore[misc]
def summary_agent(mock_client: "OpenAIChatCompletionClient") -> SummaryAgent:
    """SummaryAgent instance for testing."""
    return SummaryAgent(mock_client)


@pytest.fixture  # type: ignore[misc]
def search_agent(
    mock_client: "OpenAIChatCompletionClient",
) -> SearchAgent:
    """SearchAgent instance for testing."""

    # Create a simple stub function with proper type hints
    def mock_run_crypto_search(query: str) -> str:
        return f"Search results for: {query}"

    with patch(
        "src.agentic_crypto_influencer.agents.search_agent.GoogleGroundingTool"
    ) as mock_ggt:
        mock_ggt.return_value.run_crypto_search = mock_run_crypto_search
        return SearchAgent(mock_client)


@pytest.mark.unit  # type: ignore[misc]
def test_review_agent_init(review_agent: ReviewAgent) -> None:
    """Test ReviewAgent initialization."""
    assert review_agent is not None


@pytest.mark.unit  # type: ignore[misc]
def test_publish_agent_init(publish_agent: PublishAgent) -> None:
    """Test PublishAgent initialization."""
    assert publish_agent is not None


@pytest.mark.unit  # type: ignore[misc]
def test_summary_agent_init(summary_agent: SummaryAgent) -> None:
    """Test SummaryAgent initialization."""
    assert summary_agent is not None


@pytest.mark.unit  # type: ignore[misc]
def test_search_agent_init(search_agent: SearchAgent) -> None:
    """Test SearchAgent initialization."""
    assert search_agent is not None
