import asyncio
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from flask import json
from json import JSONDecodeError

from agents.publish_agent import PublishAgent
from agents.search_agent import SearchAgent
from agents.summary_agent import SummaryAgent
from config.key_constants import GOOGLE_GENAI_API_KEY
from config.model_constants import MODEL_ID
from error_management.error_manager import ErrorManager
import os

error_manager = ErrorManager()


async def main():
    try:
        if not GOOGLE_GENAI_API_KEY:
            raise ValueError("GOOGLE_GENAI_API_KEY environment variable is required")
        model_client = OpenAIChatCompletionClient(
            model=MODEL_ID, api_key=GOOGLE_GENAI_API_KEY
        )

        search_agent = SearchAgent(model_client=model_client)
        summary_agent = SummaryAgent(model_client=model_client)
        publish_agent = PublishAgent(model_client=model_client)

        builder = DiGraphBuilder()
        builder.add_node(search_agent)
        builder.add_node(summary_agent)
        builder.add_node(publish_agent)
        builder.add_edge(search_agent, summary_agent)
        builder.add_edge(
            summary_agent,
            publish_agent,
            condition=lambda msg: "Post must be between 1 and 280 characters"
            not in msg.to_model_text(),
        )

        builder.set_entry_point(search_agent)

        graph = builder.build()

        termination_condition = TextMentionTermination("APPROVE")

        flow = GraphFlow(
            participants=builder.get_participants(),
            graph=graph,
            termination_condition=termination_condition,
        )
        team_state_path = "src/graphflow/team_state.json"
        team_state = None

        if os.path.exists(team_state_path):
            try:
                with open(team_state_path, "r") as f:
                    team_state = json.load(f)
            except (JSONDecodeError, IOError):
                team_state = None

        if team_state:
            await flow.load_state(team_state)

        stream = flow.run_stream(
            task="""
            Find the latest breaking cryptocurrency news. 
            Filter out any content that has already been published. 
            Summarize the most relevant news into a concise post of no more than 280 characters. 
            The final post must be published to the X platform.
            """
        )

        async for event in stream:
            print(event)

        team_state = await flow.save_state()
        team_state_path = "src/graphflow/team_state.json"
        if team_state:
            os.makedirs(os.path.dirname(team_state_path), exist_ok=True)
            with open(team_state_path, "w") as f:
                json.dump(team_state, f)
    except Exception as e:
        error_message = error_manager.handle_error(e)
        print(error_message)


if __name__ == "__main__":
    asyncio.run(main())
