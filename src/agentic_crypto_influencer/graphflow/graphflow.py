import asyncio
import json
import sys
from collections.abc import Mapping
from typing import Any

from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.agentic_crypto_influencer.agents.publish_agent import PublishAgent
from src.agentic_crypto_influencer.agents.search_agent import SearchAgent
from src.agentic_crypto_influencer.agents.summary_agent import SummaryAgent
from src.agentic_crypto_influencer.config.key_constants import GOOGLE_GENAI_API_KEY
from src.agentic_crypto_influencer.config.logging_config import get_logger, setup_logging
from src.agentic_crypto_influencer.config.model_constants import MODEL_ID
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler

# Initialize logging
setup_logging()
logger = get_logger("graphflow.main")
error_manager = ErrorManager()


async def main() -> None:
    """Main function to run the crypto influencer agent workflow."""
    if not GOOGLE_GENAI_API_KEY:
        error_msg = "GOOGLE_GENAI_API_KEY environment variable is required"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    logger.info("Starting crypto influencer workflow", extra={"model_id": MODEL_ID})
    
    try:
        # Initialize model client
        logger.debug("Initializing OpenAI model client")
        model_client = OpenAIChatCompletionClient(model=MODEL_ID, api_key=GOOGLE_GENAI_API_KEY)

        # Initialize agents
        logger.debug("Initializing agents")
        search_agent = SearchAgent(model_client=model_client)
        summary_agent = SummaryAgent(model_client=model_client)
        publish_agent = PublishAgent(model_client=model_client)

        # Build graph
        logger.debug("Building agent graph")
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
        
        # Initialize Redis handler
        logger.debug("Initializing Redis handler")
        redis_handler = RedisHandler()

        # Load team_state from Redis if available
        logger.debug("Loading team state from Redis")
        redis_team_state_bytes = redis_handler.get("team_state")
        redis_team_state: str = (
            redis_team_state_bytes.decode("utf-8") if redis_team_state_bytes else "{}"
        )
        team_state: Mapping[str, Any] = json.loads(redis_team_state)
        await flow.load_state(team_state)
        
        if team_state:
            logger.info("Loaded existing team state from Redis", extra={"state_keys": list(team_state.keys())})
        else:
            logger.info("No existing team state found, starting fresh")

        # Run the workflow
        logger.info("Starting workflow execution")
        stream = flow.run_stream(
            task="Process the latest crypto news and publish a compliant, high-quality tweet to X."
        )

        event_count = 0
        async for event in stream:
            event_count += 1
            logger.info(
                f"Workflow event {event_count}",
                extra={
                    "event_number": event_count,
                    "event_preview": str(event)[:200],  # First 200 chars for logging
                }
            )

        # Save state back to Redis
        logger.debug("Saving team state to Redis")
        team_state = await flow.save_state()
        redis_handler.set("team_state", json.dumps(team_state))
        
        logger.info(
            "Workflow completed successfully",
            extra={
                "total_events": event_count,
                "state_saved": True,
            }
        )
        
    except Exception as e:
        error_message = error_manager.handle_error(
            e,
            context={
                "workflow": "crypto_influencer",
                "model_id": MODEL_ID,
            }
        )
        logger.critical(f"Workflow failed: {error_message}")


if __name__ == "__main__":
    setup_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        sys.exit(1)
