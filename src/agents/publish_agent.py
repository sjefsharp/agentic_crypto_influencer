from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from tools.x import X

from config.publish_agent_constants import (
    PUBLISH_AGENT_NAME,
    PUBLISH_AGENT_SYSTEM_MESSAGE,
)


class PublishAgent(AssistantAgent):
    def __init__(self, model_client: OpenAIChatCompletionClient):
        super().__init__(
            name=PUBLISH_AGENT_NAME,
            model_client=model_client,
            system_message=PUBLISH_AGENT_SYSTEM_MESSAGE,
            tools=[X().post],
        )
