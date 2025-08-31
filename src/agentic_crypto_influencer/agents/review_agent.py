from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.agentic_crypto_influencer.config.review_agent_constants import (
    REVIEW_AGENT_NAME,
    REVIEW_AGENT_SYSTEM_MESSAGE,
)
from src.agentic_crypto_influencer.tools.validator import Validator


class ReviewAgent(AssistantAgent):  # type: ignore[misc]
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name=REVIEW_AGENT_NAME,
            model_client=model_client,
            system_message=REVIEW_AGENT_SYSTEM_MESSAGE,
            tools=[Validator.validate_length],
        )
