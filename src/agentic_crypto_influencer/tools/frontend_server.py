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
import threading
from threading import Lock
import time
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests
from werkzeug.wrappers import Response

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

# Enable CORS for Safari and cross-origin requests
CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000"], supports_credentials=True)

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
    # Check for OAuth status messages from URL parameters
    oauth_success = request.args.get("oauth_success")
    oauth_error = request.args.get("oauth_error")

    # Broadcast status messages to all connected clients
    if oauth_success:
        broadcast_activity("OAuth", "✅ OAuth autorisatie succesvol voltooid!", "success")
    elif oauth_error:
        error_messages = {
            "no_code": "❌ Geen autorisatiecode ontvangen",
            "token_exchange_failed": "❌ Token uitwisseling mislukt",
            "callback_exception": "❌ Fout tijdens callback verwerking",
        }
        message = error_messages.get(oauth_error, f"❌ OAuth fout: {oauth_error}")
        broadcast_activity("OAuth", message, "error")

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


@app.route("/oauth/authorize")  # type: ignore[misc]
def oauth_authorize_redirect() -> Response:
    """Redirect to OAuth authorization URL - Safari friendly without popup."""
    try:
        from src.agentic_crypto_influencer.tools.oauth_handler import OAuthHandler

        oauth_handler = OAuthHandler()

        # Generate authorization URL with PKCE
        auth_url = oauth_handler.get_authorization_url()  # type: ignore

        logger.info("Redirecting to OAuth URL for authorization")
        broadcast_activity("OAuth", "🔄 Doorverwijzen naar X/Twitter autorisatie", "info")

        # Redirect directly to OAuth URL
        return redirect(auth_url)

    except Exception as e:
        logger.error(f"Error in OAuth redirect: {e}")
        broadcast_activity("OAuth", f"❌ Fout bij autorisatie redirect: {e!s}", "error")
        return redirect(url_for("dashboard"))


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
def callback() -> Response:
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
            broadcast_activity("OAuth", f"❌ OAuth Error: {error}", "error")
            return redirect(url_for("dashboard", oauth_error=error))

        if not code:
            logger.error("No authorization code received in callback")
            broadcast_activity("OAuth", "❌ Geen autorisatiecode ontvangen", "error")
            return redirect(url_for("dashboard", oauth_error="no_code"))

        # Exchange code for tokens
        broadcast_activity("OAuth", "🔄 Token uitwisseling wordt uitgevoerd...", "info")
        success = get_and_save_tokens(code)

        if success:
            # Broadcast success to connected clients
            broadcast_activity(ACTIVITY_TYPE_OAUTH, OAUTH_SUCCESS_MESSAGE, ACTIVITY_STATUS_SUCCESS)
            # Redirect back to homepage with success indicator
            return redirect(url_for("dashboard", oauth_success="true"))
        else:
            broadcast_activity("OAuth", "❌ Token exchange mislukt", "error")
            return redirect(url_for("dashboard", oauth_error="token_exchange_failed"))

    except Exception as e:
        logger.error(f"Callback error: {e}")
        broadcast_activity("OAuth", f"❌ Callback error: {e!s}", "error")
        return redirect(url_for("dashboard", oauth_error="callback_exception"))


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
    """Broadcast agent activity to connected clients with enhanced logging."""
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

    # Enhanced logging
    log_message = f"[{agent}] {message} ({activity_type})"
    if activity_type == "error":
        logger.error(log_message)
    elif activity_type == "warning":
        logger.warning(log_message)
    elif activity_type == "success":
        logger.info(f"✅ {log_message}")
    elif activity_type == "chat":
        logger.info(f"💬 {log_message}")
    else:
        logger.info(log_message)

    # Broadcast to WebSocket clients if available
    if socketio_available:
        try:
            socketio.emit("agent_activity", activity, namespace="/stream")
            logger.debug(f"WebSocket broadcast sent: {agent} - {message}")
        except Exception as e:
            logger.warning(f"WebSocket broadcast failed: {e}")
    else:
        logger.debug("WebSocket not available, activity stored for polling")


def check_graphflow_activity() -> None:
    """Check Redis for GraphFlow activities and broadcast them."""
    try:
        graphflow_activity_data = redis_handler.get("graphflow_activity")
        if graphflow_activity_data:
            activity = json.loads(graphflow_activity_data)

            # Broadcast the activity to connected clients
            if socketio_available:
                try:
                    socketio.emit("agent_activity", activity, namespace="/stream")
                    logger.debug(f"GraphFlow activity forwarded: {activity['message']}")

                    # Add to recent activities
                    with stream_lock:
                        recent_activities.append(activity)
                        if len(recent_activities) > MAX_RECENT_ACTIVITIES:
                            recent_activities.pop(0)

                    # Clear the activity from Redis to prevent duplication
                    redis_handler.delete("graphflow_activity")

                except Exception as e:
                    logger.warning(f"Failed to forward GraphFlow activity: {e}")

    except Exception as e:
        logger.debug(f"No GraphFlow activity to forward: {e}")


# Start a background task to check for GraphFlow activities
def graphflow_activity_checker() -> None:
    """Background thread to check for GraphFlow activities."""
    while True:
        try:
            check_graphflow_activity()
            time.sleep(2)  # Check every 2 seconds
        except Exception as e:
            logger.warning(f"GraphFlow activity checker error: {e}")
            time.sleep(5)  # Wait longer on error


# Start the background checker thread
if socketio_available:
    graphflow_thread = threading.Thread(target=graphflow_activity_checker, daemon=True)
    graphflow_thread.start()
    logger.info("GraphFlow activity checker started")


if socketio_available:

    @socketio.on("connect", namespace="/stream")  # type: ignore[misc]
    def handle_connect() -> None:
        """Handle new WebSocket connection."""
        logger.info(f"Client connected: {request.sid}")  # type: ignore[attr-defined]
        connected_clients.add(request.sid)  # type: ignore[attr-defined]

        # Send recent activities to new client
        with stream_lock:
            for activity in recent_activities[-10:]:  # Send last 10 activities
                emit("agent_activity", activity)

    @socketio.on("disconnect", namespace="/stream")  # type: ignore[misc]
    def handle_disconnect() -> None:
        """Handle WebSocket disconnection."""
        logger.info(f"Client disconnected: {request.sid}")  # type: ignore[attr-defined]
        connected_clients.discard(request.sid)  # type: ignore[attr-defined]


@app.route("/api/jobs/create", methods=["POST"])  # type: ignore[misc]
def create_scheduled_job() -> dict[str, Any] | tuple[Any, int]:
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
            return jsonify(
                {"error": "Missing required fields: schedule_value or schedule_config"}
            ), 400  # type: ignore[no-any-return]

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
            return jsonify(  # type: ignore[no-any-return]
                {
                    "message": "Job created successfully",
                    "job_id": result.get("job_id", "unknown"),
                }
            )
        else:
            return jsonify({"error": result.get("error", "Failed to create job")}), 400  # type: ignore[no-any-return]

    except Exception as e:
        logger.error(f"Error creating scheduled job: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/jobs/list", methods=["GET"])  # type: ignore[misc]
def list_scheduled_jobs() -> dict[str, Any] | tuple[Any, int]:
    """List all scheduled jobs."""
    try:
        jobs = scheduler_manager.get_scheduled_jobs()
        return jsonify({"jobs": jobs})  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error listing scheduled jobs: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/jobs/cancel/<job_id>", methods=["DELETE"])  # type: ignore[misc]
def cancel_scheduled_job(job_id: str) -> dict[str, Any] | tuple[Any, int]:
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
def get_job_history() -> dict[str, Any] | tuple[Any, int]:
    """Get job execution history."""
    try:
        history = scheduler_manager.get_job_history()
        return jsonify({"history": history})  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error getting job history: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/graphflow/start", methods=["POST"])  # type: ignore[misc]
def start_graphflow() -> dict[str, Any] | tuple[Any, int]:
    """Start GraphFlow process with enhanced logging and error handling."""
    try:
        logger.info("GraphFlow start requested")
        broadcast_activity("GraphFlow", "🚀 GraphFlow wordt opgestart...", "info")

        if scheduler_manager is None:  # type: ignore[comparison-overlap]
            error_msg = "Scheduler not available"
            logger.error(error_msg)
            broadcast_activity("GraphFlow", f"❌ {error_msg}", "error")
            return jsonify({"error": error_msg}), 500  # type: ignore[no-any-return]

        result = scheduler_manager.start_graphflow()

        if result.get("success", False):
            message = result.get("message", "GraphFlow started successfully")
            pid = result.get("pid")

            logger.info(f"✅ GraphFlow started successfully - PID: {pid}")
            broadcast_activity(
                "GraphFlow", f"✅ {message}" + (f" (PID: {pid})" if pid else ""), "success"
            )

            return jsonify(  # type: ignore[no-any-return]
                {
                    "message": message,
                    "pid": pid,
                }
            )
        else:
            error = result.get("error", "Failed to start GraphFlow")
            logger.error(f"Failed to start GraphFlow: {error}")
            broadcast_activity("GraphFlow", f"❌ {error}", "error")
            return jsonify({"error": error}), 400  # type: ignore[no-any-return]

    except Exception as e:
        error_msg = f"Error starting GraphFlow: {e}"
        logger.error(error_msg)
        broadcast_activity("GraphFlow", f"❌ {error_msg}", "error")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/graphflow/stop", methods=["POST"])  # type: ignore[misc]
def stop_graphflow() -> dict[str, Any] | tuple[Any, int]:
    """Stop GraphFlow process with enhanced logging and error handling."""
    try:
        logger.info("GraphFlow stop requested")
        broadcast_activity("GraphFlow", "⏹️ GraphFlow wordt gestopt...", "info")

        result = scheduler_manager.stop_graphflow()

        if result.get("success", False):
            message = result.get("message", "GraphFlow stopped successfully")
            logger.info("✅ GraphFlow stopped successfully")
            broadcast_activity("GraphFlow", f"✅ {message}", "success")

            return jsonify({"message": message})  # type: ignore[no-any-return]
        else:
            error = result.get("error", "Failed to stop GraphFlow")
            logger.error(f"Failed to stop GraphFlow: {error}")
            broadcast_activity("GraphFlow", f"❌ {error}", "error")
            return jsonify({"error": error}), 400  # type: ignore[no-any-return]

    except Exception as e:
        error_msg = f"Error stopping GraphFlow: {e}"
        logger.error(error_msg)
        broadcast_activity("GraphFlow", f"❌ {error_msg}", "error")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/graphflow/status", methods=["GET"])  # type: ignore[misc]
def get_graphflow_status() -> dict[str, Any] | tuple[Any, int]:
    """Get GraphFlow status."""
    try:
        status = scheduler_manager.get_graphflow_status()
        # Map the response to match test expectations and handle both real and mock responses
        response_data = {
            "running": status.get("is_running", status.get("running", False)),
            "pid": status.get("pid"),
            "status": status.get("status", "unknown"),
        }

        # Add start_time if available (for compatibility with tests)
        if "start_time" in status:
            response_data["start_time"] = status["start_time"]

        return jsonify(response_data)  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error getting GraphFlow status: {e}")
        return jsonify({"error": str(e)}), 500  # type: ignore[no-any-return]


@app.route("/api/stream/activities")  # type: ignore[misc]
def get_recent_activities() -> dict[str, Any] | tuple[Any, int]:
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
