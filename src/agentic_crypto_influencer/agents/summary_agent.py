from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.agentic_crypto_influencer.config.summary_agent_constants import (
    SUMMARY_AGENT_NAME,
    SUMMARY_AGENT_SYSTEM_MESSAGE,
)
from src.agentic_crypto_influencer.tools.bitvavo_handler import BitvavoHandler
from src.agentic_crypto_influencer.tools.validator import Validator


class SummaryAgent(AssistantAgent):  # type: ignore[misc]
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name=SUMMARY_AGENT_NAME,
            model_client=model_client,
            system_message=SUMMARY_AGENT_SYSTEM_MESSAGE,
            tools=[Validator.validate_length, BitvavoHandler().get_market_data],
        )
