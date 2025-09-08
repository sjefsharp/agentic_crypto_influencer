from autogen_agentchat.agents import AssistantAgent  # type: ignore[import]
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.agentic_crypto_influencer.config.publish_agent_constants import (
    PUBLISH_AGENT_NAME,
    PUBLISH_AGENT_SYSTEM_MESSAGE,
)
from src.agentic_crypto_influencer.tools.x import X


class PublishAgent(AssistantAgent):  # type: ignore[misc]
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name=PUBLISH_AGENT_NAME,
            model_client=model_client,
            system_message=PUBLISH_AGENT_SYSTEM_MESSAGE,
            tools=[X().post],
        )
