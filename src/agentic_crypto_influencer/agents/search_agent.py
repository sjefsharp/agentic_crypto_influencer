from autogen_agentchat.agents import AssistantAgent  # type: ignore[import]
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.agentic_crypto_influencer.config.search_agent_constants import (
    SEARCH_AGENT_NAME,
    SEARCH_AGENT_SYSTEM_MESSAGE,
)
from src.agentic_crypto_influencer.tools.google_grounding_tool import GoogleGroundingTool


class SearchAgent(AssistantAgent):  # type: ignore[misc]
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name=SEARCH_AGENT_NAME,
            model_client=model_client,
            system_message=SEARCH_AGENT_SYSTEM_MESSAGE,
            tools=[GoogleGroundingTool().run_crypto_search],
        )
