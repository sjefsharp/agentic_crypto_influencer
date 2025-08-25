from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from config.summary_agent_constants import (
    SUMMARY_AGENT_NAME,
    SUMMARY_AGENT_SYSTEM_MESSAGE,
)


class SummaryAgent(AssistantAgent):
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name=SUMMARY_AGENT_NAME,
            model_client=model_client,
            system_message=SUMMARY_AGENT_SYSTEM_MESSAGE,
        )
