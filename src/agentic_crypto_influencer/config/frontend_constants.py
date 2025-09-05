"""
Frontend server constants for Flask application configuration.
Contains all hardcoded strings used in the frontend server.
"""

# Flask Configuration
FLASK_SECRET_KEY_DEFAULT = "your-secret-key-here"
FLASK_TEMPLATE_FOLDER = "templates"
FLASK_STATIC_FOLDER = "static"

# SocketIO Configuration
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
SOCKETIO_ASYNC_MODE = "threading"

# Host Configuration
HOST_PRODUCTION = "0.0.0.0"
HOST_LOCAL = "127.0.0.1"
PORT_ENV_VAR = "PORT"

# Activity Settings
MAX_RECENT_ACTIVITIES = 50

# Route Paths
ROUTE_DASHBOARD = "/"
ROUTE_STATIC = "/static/<path:filename>"
ROUTE_OAUTH_STATUS = "/api/oauth/status"
ROUTE_OAUTH_START = "/api/oauth/start"
ROUTE_SYSTEM_REDIS = "/api/system/redis"
ROUTE_CALLBACK = "/callback"

# Template Files
TEMPLATE_DASHBOARD = "dashboard.html"

# Log Messages
LOG_SOCKETIO_INITIALIZED = "SocketIO initialized successfully for real-time features"
LOG_SOCKETIO_FALLBACK = "flask-socketio not available - falling back to polling"

# OAuth Messages (Dutch)
OAUTH_SUCCESS_MESSAGE = "✅ Autorisatie succesvol voltooid"
OAUTH_FAILED_MESSAGE = "❌ Token exchange mislukt"
OAUTH_NO_CODE_MESSAGE = "❌ Geen autorisatiecode ontvangen"
OAUTH_CALLBACK_ERROR_PREFIX = "❌ Callback error: "

# OAuth Success HTML Response
OAUTH_SUCCESS_HTML = """
<html><body style="font-family: -apple-system, BlinkMacSystemFont,
'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px;">
<h2 style="color: #1da1f2;">✅ Autorisatie Voltooid!</h2>
<p>Je kunt dit tabblad nu sluiten.</p>
<script>
    setTimeout(() => {
        if (window.opener) {
            window.opener.postMessage('oauth_success', '*');
            window.close();
        }
    }, 1000);
</script>
</body></html>
"""

# Activity Broadcasting
ACTIVITY_TYPE_OAUTH = "OAuth"
ACTIVITY_STATUS_SUCCESS = "success"
ACTIVITY_STATUS_ERROR = "error"
