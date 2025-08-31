import asyncio
from json import JSONDecodeError

from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_ext.models.openai import OpenAIChatCompletionClient
from flask import json
from src.agentic_crypto_influencer.agents.publish_agent import PublishAgent
from src.agentic_crypto_influencer.agents.search_agent import SearchAgent
from src.agentic_crypto_influencer.agents.summary_agent import SummaryAgent
from src.agentic_crypto_influencer.config.key_constants import GOOGLE_GENAI_API_KEY
from src.agentic_crypto_influencer.config.model_constants import MODEL_ID
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler

error_manager = ErrorManager()


async def main() -> None:
    if not GOOGLE_GENAI_API_KEY:
        raise ValueError("GOOGLE_GENAI_API_KEY environment variable is required")
    try:
        model_client = OpenAIChatCompletionClient(model=MODEL_ID, api_key=GOOGLE_GENAI_API_KEY)

        search_agent = SearchAgent(model_client=model_client)
        summary_agent = SummaryAgent(model_client=model_client)
        publish_agent = PublishAgent(model_client=model_client)

        builder = DiGraphBuilder()
        builder.add_node(search_agent)
        builder.add_node(summary_agent)
        builder.add_node(publish_agent)
        builder.add_edge(search_agent, summary_agent)
        builder.add_edge(summary_agent, publish_agent)

        builder.set_entry_point(search_agent)

        graph = builder.build()

        termination_condition = TextMentionTermination("!PUBLISHED!")

        flow = GraphFlow(
            participants=builder.get_participants(),
            graph=graph,
            termination_condition=termination_condition,
        )
        redis_handler = RedisHandler()

        team_state = None

        # Load team_state from Redis if available
        redis_team_state = redis_handler.get("team_state")
        if redis_team_state:
            try:
                team_state = json.loads(redis_team_state)
                await flow.load_state(team_state)
            except JSONDecodeError:
                team_state = None

        stream = flow.run_stream(
            task="Process the latest crypto news and publish a compliant, high-quality tweet to X."
        )

        async for event in stream:
            print(event)

        team_state = await flow.save_state()
        if team_state:
            # Save team_state to Redis
            redis_handler.set("team_state", json.dumps(team_state))
    except Exception as e:
        error_message = error_manager.handle_error(e)
        print(error_message)


if __name__ == "__main__":
    asyncio.run(main())
