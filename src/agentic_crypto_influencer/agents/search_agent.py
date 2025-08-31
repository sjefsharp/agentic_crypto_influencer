from agentic_crypto_influencer.config.search_agent_constants import (
    SEARCH_AGENT_NAME,
    SEARCH_AGENT_SYSTEM_MESSAGE,
)
from agentic_crypto_influencer.tools.google_grounding_tool import GoogleGroundingTool
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


class SearchAgent(AssistantAgent):  # type: ignore[misc]
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name=SEARCH_AGENT_NAME,
            model_client=model_client,
            system_message=SEARCH_AGENT_SYSTEM_MESSAGE,
            tools=[GoogleGroundingTool().run_crypto_search],
        )
