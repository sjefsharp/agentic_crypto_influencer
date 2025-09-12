import asyncio
from collections.abc import Mapping
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any

# Add project root to Python path for compatibility
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from autogen_agentchat.conditions import TextMentionTermination  # noqa: E402
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow  # noqa: E402
from autogen_ext.models.openai import OpenAIChatCompletionClient  # noqa: E402

from src.agentic_crypto_influencer.agents.publish_agent import PublishAgent  # noqa: E402
from src.agentic_crypto_influencer.agents.search_agent import SearchAgent  # noqa: E402
from src.agentic_crypto_influencer.agents.summary_agent import SummaryAgent  # noqa: E402
from src.agentic_crypto_influencer.config.key_constants import GOOGLE_GENAI_API_KEY  # noqa: E402
from src.agentic_crypto_influencer.config.logging_config import (  # noqa: E402
    get_logger,
    setup_logging,
)
from src.agentic_crypto_influencer.config.model_constants import MODEL_ID  # noqa: E402
from src.agentic_crypto_influencer.error_management.error_manager import ErrorManager  # noqa: E402
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler  # noqa: E402

# Initialize logging
setup_logging()
logger = get_logger("graphflow.main")
error_manager = ErrorManager()


def broadcast_to_frontend(agent: str, message: str, activity_type: str = "info") -> None:
    """Broadcast activity to frontend via Redis for live monitoring."""
    try:
        from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler

        redis_handler = RedisHandler(lazy_connect=True)
        activity = {
            "agent": agent,
            "message": message,
            "type": activity_type,
            "timestamp": datetime.now().isoformat(),
        }

        # Store in Redis with expiry for frontend to pick up
        redis_handler.set("graphflow_activity", json.dumps(activity))
        logger.debug(f"Broadcasted to frontend: [{agent}] {message}")

    except Exception as e:
        logger.warning(f"Failed to broadcast to frontend: {e}")


async def main() -> None:
    """Main function to run the crypto influencer agent workflow."""
    if not GOOGLE_GENAI_API_KEY:
        error_msg = "GOOGLE_GENAI_API_KEY environment variable is required"
        logger.error(error_msg)
        broadcast_to_frontend("GraphFlow", f"❌ {error_msg}", "error")
        raise ValueError(error_msg)

    logger.info("Starting crypto influencer workflow", extra={"model_id": MODEL_ID})
    broadcast_to_frontend("GraphFlow", "🚀 Crypto influencer workflow wordt gestart...", "info")

    try:
        # Initialize model client
        logger.debug("Initializing OpenAI model client")
        broadcast_to_frontend(
            "GraphFlow", "🔧 OpenAI model client wordt geïnitialiseerd...", "info"
        )
        model_client = OpenAIChatCompletionClient(model=MODEL_ID, api_key=GOOGLE_GENAI_API_KEY)

        # Initialize agents
        logger.debug("Initializing agents")
        broadcast_to_frontend("GraphFlow", "🤖 Agents worden geïnitialiseerd...", "info")
        search_agent = SearchAgent(model_client=model_client)
        summary_agent = SummaryAgent(model_client=model_client)
        publish_agent = PublishAgent(model_client=model_client)

        # Build graph
        logger.debug("Building agent graph")
        broadcast_to_frontend("GraphFlow", "📊 Agent workflow graph wordt gebouwd...", "info")
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
        broadcast_to_frontend("GraphFlow", "💾 Redis verbinding wordt geïnitialiseerd...", "info")
        redis_handler = RedisHandler(lazy_connect=True)

        # Load team_state from Redis if available
        logger.debug("Loading team state from Redis")
        broadcast_to_frontend("GraphFlow", "📥 Team state wordt geladen vanuit Redis...", "info")
        redis_team_state_bytes = redis_handler.get("team_state")
        redis_team_state: str = (
            redis_team_state_bytes.decode("utf-8") if redis_team_state_bytes else "{}"
        )
        team_state: Mapping[str, Any] = json.loads(redis_team_state)
        await flow.load_state(team_state)

        if team_state:
            logger.info(
                "Loaded existing team state from Redis",
                extra={"state_keys": list(team_state.keys())},
            )
        else:
            logger.info("No existing team state found, starting fresh")

        # Run the workflow
        logger.info("Starting workflow execution")
        broadcast_to_frontend("GraphFlow", "🎯 Workflow uitvoering wordt gestart...", "success")
        stream = flow.run_stream(
            task="Process the latest crypto news and publish a compliant, high-quality tweet to X."
        )

        event_count = 0
        async for event in stream:
            event_count += 1

            # Log detailed event information
            event_type = type(event).__name__
            logger.info(f"Workflow event {event_count} - Type: {event_type}")

            # Broadcast event progress to frontend
            if event_count % 5 == 0 or event_count < 10:  # Every 5th event or first 10
                broadcast_to_frontend("GraphFlow", f"📝 Event {event_count}: {event_type}", "info")

            # Check for specific event attributes
            if hasattr(event, "source"):
                logger.info(f"  Source: {event.source}")
            if hasattr(event, "target"):
                logger.info(f"  Target: {event.target}")
            if hasattr(event, "data"):
                logger.info(f"  Data: {event.data}")
            if hasattr(event, "messages") and event.messages:
                logger.info(f"  Messages ({len(event.messages)}):")
                for i, msg in enumerate(event.messages[-3:]):  # Last 3 messages
                    logger.info(f"    {i}: {str(msg)[:200]}")
            if hasattr(event, "content"):
                logger.info(f"  Content: {event.content}")

            # Log full event for debugging (truncated)
            full_event_str = str(event)
            if (
                "post" in full_event_str.lower()
                or "twitter" in full_event_str.lower()
                or "x.com" in full_event_str.lower()
            ):
                logger.info("  *** POTENTIAL TWITTER POST EVENT ***")
                logger.info(f"  Full event: {full_event_str[:500]}")
                broadcast_to_frontend(
                    "GraphFlow", "🐦 Twitter post event gedetecteerd!", "warning"
                )

            logger.debug(f"  Full event preview: {full_event_str[:300]}")

        # Save state back to Redis
        logger.debug("Saving team state to Redis")
        broadcast_to_frontend("GraphFlow", "💾 Team state wordt opgeslagen in Redis...", "info")
        team_state = await flow.save_state()
        redis_handler.set("team_state", json.dumps(team_state))

        logger.info(
            "Workflow completed successfully",
            extra={
                "total_events": event_count,
                "state_saved": True,
            },
        )
        broadcast_to_frontend(
            "GraphFlow",
            f"✅ Workflow succesvol voltooid! ({event_count} events verwerkt)",
            "success",
        )

    except Exception as e:
        error_message = error_manager.handle_error(
            e,
            context={
                "workflow": "crypto_influencer",
                "model_id": MODEL_ID,
            },
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
