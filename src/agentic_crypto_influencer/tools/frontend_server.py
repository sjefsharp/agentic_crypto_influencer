"""
Moderne OAuth2 callback server met real-time dashboard voor X/Twitter API.
Features: WebSocket live streaming, WCAG 2.1 AA compliance, Progressive Web App.
Volledig gebaseerd op OAuth2Session library en X API v2 PKCE specificaties.
Optimized for Render.com deployment with accessibility support.
"""

import base64
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from threading import Lock
import time
from typing import Any

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import requests
import json

from src.agentic_crypto_influencer.tools.scheduler_manager import SchedulerManager

# Global scheduler manager instance
scheduler_manager = SchedulerManager()

# Add project root to Python path for Render.com compatibility
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agentic_crypto_influencer.config.frontend_constants import (  # noqa: E402
    ACTIVITY_STATUS_SUCCESS,
    ACTIVITY_TYPE_OAUTH,
    FLASK_SECRET_KEY_DEFAULT,
    FLASK_STATIC_FOLDER,
    FLASK_TEMPLATE_FOLDER,
    HOST_LOCAL,
    HOST_PRODUCTION,
    LOG_SOCKETIO_FALLBACK,
    LOG_SOCKETIO_INITIALIZED,
    MAX_RECENT_ACTIVITIES,
    OAUTH_NO_CODE_MESSAGE,
    OAUTH_SUCCESS_HTML,
    OAUTH_SUCCESS_MESSAGE,
    PORT_ENV_VAR,
    ROUTE_OAUTH_STATUS,
    SOCKETIO_ASYNC_MODE,
    SOCKETIO_CORS_ALLOWED_ORIGINS,
    TEMPLATE_DASHBOARD,
)
from src.agentic_crypto_influencer.config.key_constants import (  # noqa: E402
    CALLBACK_SERVER_PORT,
    X_CLIENT_ID,
    X_CLIENT_SECRET,
    X_REDIRECT_URI,
)
from src.agentic_crypto_influencer.config.logging_config import get_logger  # noqa: E402
from src.agentic_crypto_influencer.config.oauth_constants import (  # noqa: E402
    CONTENT_TYPE_FORM_URLENCODED,
    HEADER_AUTHORIZATION,
    HEADER_BASIC_PREFIX,
    HEADER_CONTENT_TYPE,
    TOKEN_KEY_ACCESS_TOKEN,
    TOKEN_KEY_EXPIRES_AT,
    TOKEN_KEY_TOKEN_TYPE,
    TOKEN_TYPE_BEARER,
    X_TOKEN_URL_FALLBACK,
)
from src.agentic_crypto_influencer.config.redis_constants import (  # noqa: E402
    REDIS_KEY_ACCESS_TOKEN,
    REDIS_KEY_OAUTH_CODE_VERIFIER,
)
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler  # noqa: E402

logger = get_logger(__name__)

# Initialize Flask app with SocketIO for real-time features
app = Flask(__name__, template_folder=FLASK_TEMPLATE_FOLDER, static_folder=FLASK_STATIC_FOLDER)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", FLASK_SECRET_KEY_DEFAULT)

# Initialize SocketIO with threading for production compatibility
socketio_available = True
try:
    socketio = SocketIO(
        app, cors_allowed_origins=SOCKETIO_CORS_ALLOWED_ORIGINS, async_mode=SOCKETIO_ASYNC_MODE
    )
    logger.info(LOG_SOCKETIO_INITIALIZED)
except ImportError:
    logger.warning(LOG_SOCKETIO_FALLBACK)
    socketio_available = False

# Smart host/port configuration for Render.com vs local
PORT = int(os.environ.get(PORT_ENV_VAR, CALLBACK_SERVER_PORT))  # Render.com provides PORT env var
HOST = (
    HOST_PRODUCTION if PORT_ENV_VAR in os.environ else HOST_LOCAL
)  # Render.com vs local  # nosec B104

# Store recent agent activities for new connections
recent_activities: list[dict[str, Any]] = []
MAX_RECENT_ACTIVITIES_LIMIT = MAX_RECENT_ACTIVITIES

# Global variables for real-time streaming
connected_clients: set[str] = set()
stream_lock = Lock()
redis_handler = RedisHandler(lazy_connect=True)


@app.route("/")  # type: ignore
def dashboard() -> str:
    """Main dashboard with OAuth status and live agent stream."""
    return render_template(TEMPLATE_DASHBOARD)  # type: ignore


@app.route("/static/<path:filename>")  # type: ignore
def static_files(filename: str) -> Response:
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)


@app.route(ROUTE_OAUTH_STATUS)  # type: ignore
def oauth_status() -> tuple[dict[str, Any], int] | dict[str, Any]:
    """Check current OAuth authorization status."""
    try:
        token_data = redis_handler.get(REDIS_KEY_ACCESS_TOKEN)
        if token_data:
            # Try to parse token data
            try:
                token_info = json.loads(token_data) if isinstance(token_data, str) else token_data
                # Check if token exists and has required fields
                if isinstance(token_info, dict) and TOKEN_KEY_ACCESS_TOKEN in token_info:
                    return jsonify(  # type: ignore
                        {
                            "authorized": True,
                            TOKEN_KEY_TOKEN_TYPE: token_info.get(
                                TOKEN_KEY_TOKEN_TYPE, TOKEN_TYPE_BEARER
                            ),
                            TOKEN_KEY_EXPIRES_AT: token_info.get(TOKEN_KEY_EXPIRES_AT),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except (json.JSONDecodeError, TypeError):
                logger.warning("Token data found but not parseable")

        return jsonify(  # type: ignore
            {
                "authorized": False,
                "message": "Autorisatie vereist",
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        return jsonify(
            {
                "authorized": False,
                "error": "Status check failed",
                "timestamp": datetime.now().isoformat(),
            }
        ), 500


@app.route("/api/oauth/url")  # type: ignore[misc]
def get_oauth_url() -> tuple[dict[str, Any], int] | dict[str, Any]:
    """Generate OAuth authorization URL with PKCE."""
    try:
        from src.agentic_crypto_influencer.tools.oauth_handler import OAuthHandler

        oauth_handler = OAuthHandler()

        # Generate authorization URL with PKCE
        auth_url = oauth_handler.get_authorization_url()  # type: ignore

        return jsonify({"url": auth_url, "timestamp": datetime.now().isoformat()})  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        return jsonify(
            {
                "error": "Failed to generate authorization URL",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ), 500


@app.route("/api/system/redis")  # type: ignore[misc]
def redis_status() -> tuple[dict[str, Any], int] | dict[str, Any]:
    """Check Redis connection status."""
    try:
        # Simple ping test
        result = redis_handler.ping()  # type: ignore
        if result:
            return jsonify(  # type: ignore[no-any-return]
                {
                    "status": "ok",
                    "message": "Redis verbinding actief",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            raise Exception("Redis ping failed")
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return jsonify(  # type: ignore
            {
                "status": "error",
                "message": f"Redis verbinding mislukt: {e!s}",
                "timestamp": datetime.now().isoformat(),
            }
        ), 500


@app.route("/callback")  # type: ignore[misc]
def callback() -> tuple[str, int] | str:
    """
    OAuth2 callback handler met improved error handling en logging.
    Gebruikt OAuth2Session voor proper token exchange met PKCE support.
    """
    try:
        # Get authorization code from callback
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")

        # Log callback details
        logger.info(f"OAuth callback received - Code: {'Present' if code else 'Missing'}")
        logger.info(f"State: {state[:20] + '...' if state and len(state) > 20 else state}")

        if error:
            logger.error(f"OAuth error in callback: {error}")
            return f"❌ OAuth Error: {error}", 400

        if not code:
            logger.error("No authorization code received in callback")
            return OAUTH_NO_CODE_MESSAGE, 400

        # Exchange code for tokens
        success = get_and_save_tokens(code)

        if success:
            # Broadcast success to connected clients
            broadcast_activity(ACTIVITY_TYPE_OAUTH, OAUTH_SUCCESS_MESSAGE, ACTIVITY_STATUS_SUCCESS)
            return OAUTH_SUCCESS_HTML
        else:
            broadcast_activity("OAuth", "❌ Token exchange mislukt", "error")
            return "❌ Token uitwisseling mislukt", 500

    except Exception as e:
        logger.error(f"Callback error: {e}")
        broadcast_activity("OAuth", f"❌ Callback error: {e!s}", "error")
        return f"❌ Callback fout: {e}", 500


def get_and_save_tokens(code: str) -> bool:
    """
    Exchange authorization code for tokens using direct HTTP request.
    Bypasses OAuth2Session token exchange issues with X API v2.
    """
    try:
        # Get stored OAuth parameters
        stored_code_verifier = redis_handler.get(REDIS_KEY_OAUTH_CODE_VERIFIER)
        if not stored_code_verifier:
            logger.error("No code_verifier found in Redis")
            return False

        # Prepare token exchange request
        token_url = X_TOKEN_URL_FALLBACK  # nosec B105

        # Create Basic auth header for confidential clients
        credentials = f"{X_CLIENT_ID}:{X_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            HEADER_AUTHORIZATION: f"{HEADER_BASIC_PREFIX} {encoded_credentials}",
            HEADER_CONTENT_TYPE: CONTENT_TYPE_FORM_URLENCODED,
        }

        token_data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": X_CLIENT_ID,
            "redirect_uri": X_REDIRECT_URI,
            "code_verifier": stored_code_verifier,
        }

        logger.info("Making direct token exchange request to X API v2")

        # Make token request
        response = requests.post(token_url, headers=headers, data=token_data, timeout=30)

        logger.info(f"Token response status: {response.status_code}")

        if response.status_code == 200:
            tokens = response.json()
            logger.info("✅ Token exchange successful!")

            # Add timestamp for token management
            tokens["retrieved_at"] = time.time()

            # Save tokens to Redis
            redis_handler.set("access_token", json.dumps(tokens))

            # Cleanup temporary OAuth data
            redis_handler.delete("oauth_code_verifier")
            redis_handler.delete("oauth_state")

            logger.info("✅ Tokens saved to Redis successfully")
            return True
        else:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error in token exchange: {e}")
        return False


def broadcast_activity(agent: str, message: str, activity_type: str = "info") -> None:
    """Broadcast agent activity to connected clients."""
    activity = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "message": message,
        "type": activity_type,
    }

    # Store in recent activities
    with stream_lock:
        recent_activities.append(activity)
        if len(recent_activities) > MAX_RECENT_ACTIVITIES:
            recent_activities.pop(0)

    # Broadcast to WebSocket clients if available
    if socketio_available:
        try:
            socketio.emit("agent_activity", activity, namespace="/stream")
        except Exception as e:
            logger.warning(f"WebSocket broadcast failed: {e}")


if socketio_available:

    @socketio.on("connect", namespace="/stream")  # type: ignore[misc]
    def handle_connect() -> None:
        """Handle new WebSocket connection."""
        logger.info(f"Client connected: {request.sid}")
        connected_clients.add(request.sid)

        # Send recent activities to new client
        with stream_lock:
            for activity in recent_activities[-10:]:  # Send last 10 activities
                emit("agent_activity", activity)

    @socketio.on("disconnect", namespace="/stream")  # type: ignore[misc]
    def handle_disconnect() -> None:
        """Handle WebSocket disconnection."""
        logger.info(f"Client disconnected: {request.sid}")
        connected_clients.discard(request.sid)


@app.route("/api/jobs/create", methods=["POST"])  # type: ignore[misc]
def create_scheduled_job() -> dict[str, Any]:
    """Create a scheduled job."""
    try:
        # Get JSON data from request
        try:
            data = request.get_json()
        except Exception:
            # Handle cases where request doesn't have valid JSON (wrong content-type, etc.)
            return jsonify({"error": "No data provided"}), 400  # type: ignore[no-any-return]

        if not data:
            return jsonify({"error": "No data provided"}), 400  # type: ignore[no-any-return]
        if "schedule_config" in data and "schedule_value" not in data:
            # Convert schedule_config to schedule_value for backward compatibility
            data["schedule_value"] = json.dumps(data["schedule_config"])
        elif "schedule_value" not in data and "schedule_config" not in data:
            return jsonify({"error": "Missing required fields: schedule_value or schedule_config"}), 400  # type: ignore[no-any-return]

        required_fields = ["job_type", "schedule_type", "schedule_value"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400  # type: ignore[no-any-return]

        # Extract parameters - job_name is optional, use default if not provided
        job_type = data["job_type"]
        schedule_type = data["schedule_type"]
        schedule_value = data["schedule_value"]
        job_name = data.get("job_name", f"Job-{datetime.now().isoformat()}")
        job_description = data.get("job_description", "")
        job_args = data.get("job_args")

        # Create the job
        result = scheduler_manager.create_scheduled_job(
            job_type=job_type,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            job_name=job_name,
            job_description=job_description,
            job_args=job_args,
        )

        if result.get("success", False):
            return jsonify({  # type: ignore[no-any-return]
                "message": "Job created successfully",
                "job_id": result.get("job_id", "unknown")
            })
        else:
            return jsonify({"error": result.get("error", "Failed to create job")}), 400  # type: ignore[no-any-return]

    except Exception as e:
        logger.error(f"Error creating scheduled job: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/jobs/list", methods=["GET"])  # type: ignore[misc]
def list_scheduled_jobs() -> dict[str, Any]:
    """List all scheduled jobs."""
    try:
        jobs = scheduler_manager.get_scheduled_jobs()
        return jsonify({"jobs": jobs})  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error listing scheduled jobs: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/jobs/cancel/<job_id>", methods=["DELETE"])  # type: ignore[misc]
def cancel_scheduled_job(job_id: str) -> dict[str, Any]:
    """Cancel a scheduled job."""
    try:
        result = scheduler_manager.cancel_job(job_id)
        if result["success"]:
            return jsonify({"message": "Job cancelled successfully"})  # type: ignore[no-any-return]
        else:
            return jsonify({"error": result.get("error", "Failed to cancel job")}), 400  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error cancelling scheduled job: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/jobs/history", methods=["GET"])  # type: ignore[misc]
def get_job_history() -> dict[str, Any]:
    """Get job execution history."""
    try:
        history = scheduler_manager.get_job_history()
        return jsonify({"history": history})  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error getting job history: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/graphflow/start", methods=["POST"])  # type: ignore[misc]
def start_graphflow() -> dict[str, Any]:
    """Start GraphFlow process."""
    try:
        if scheduler_manager is None:  # type: ignore[comparison-overlap]
            return jsonify({"error": "Scheduler not available"}), 500  # type: ignore[no-any-return]

        result = scheduler_manager.start_graphflow()
        if result.get("success", False):
            return jsonify({
                "message": result.get("message", "GraphFlow started successfully"),
                "pid": result.get("pid")
            })  # type: ignore[no-any-return]
        else:
            return jsonify({"error": result.get("error", "Failed to start GraphFlow")}), 400  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error starting GraphFlow: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/graphflow/stop", methods=["POST"])  # type: ignore[misc]
def stop_graphflow() -> dict[str, Any]:
    """Stop GraphFlow process."""
    try:
        result = scheduler_manager.stop_graphflow()
        if result.get("success", False):
            return jsonify({"message": "GraphFlow stopped successfully"})  # type: ignore[no-any-return]
        else:
            return jsonify({"error": result.get("error", "Failed to stop GraphFlow")}), 400  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error stopping GraphFlow: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/graphflow/status", methods=["GET"])  # type: ignore[misc]
def get_graphflow_status() -> dict[str, Any]:
    """Get GraphFlow status."""
    try:
        status = scheduler_manager.get_graphflow_status()
        # Map the response to match test expectations and handle both real and mock responses
        response_data = {
            "running": status.get("is_running", status.get("running", False)),
            "pid": status.get("pid"),
            "status": status.get("status", "unknown")
        }

        # Add start_time if available (for compatibility with tests)
        if "start_time" in status:
            response_data["start_time"] = status["start_time"]

        return jsonify(response_data)  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error getting GraphFlow status: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/stream/activities")  # type: ignore[misc]
def get_recent_activities() -> dict[str, Any]:
    """Fallback API endpoint for recent activities (polling)."""
    with stream_lock:
        return jsonify(  # type: ignore[no-any-return]
            {
                "activities": recent_activities[-20:],  # Last 20 activities
                "timestamp": datetime.now().isoformat(),
            }
        )


@app.errorhandler(404)  # type: ignore[misc]
def not_found(error: Any) -> tuple[dict[str, Any], int]:
    """Custom 404 handler."""
    return jsonify(
        {
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.now().isoformat(),
        }
    ), 404


@app.errorhandler(500)  # type: ignore[misc]
def internal_error(error: Any) -> tuple[dict[str, Any], int]:
    """Custom 500 handler."""
    return jsonify(
        {
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "timestamp": datetime.now().isoformat(),
        }
    ), 500


def run_server() -> None:
    """Run the callback server with proper configuration."""
    try:
        logger.info("🚀 Starting OAuth2 Dashboard Server...")
        logger.info(f"📡 Host: {HOST}, Port: {PORT}")
        logger.info(f"🔗 Dashboard: http://{HOST}:{PORT}")
        logger.info("📱 PWA Support: Enabled")
        logger.info("♿ Accessibility: WCAG 2.1 AA Compliant")
        logger.info(
            f"🔌 WebSocket: {'Enabled' if socketio_available else 'Disabled (polling fallback)'}"
        )

        # Add initial activity
        broadcast_activity("System", "🚀 Dashboard server gestart", "info")

        if socketio_available:
            socketio.run(app, host=HOST, port=PORT, debug=False, allow_unsafe_werkzeug=True)
        else:
            app.run(host=HOST, port=PORT, debug=False)

    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise


if __name__ == "__main__":
    run_server()
