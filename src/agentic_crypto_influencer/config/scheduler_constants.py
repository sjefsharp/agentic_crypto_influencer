"""
Scheduler constants for job management and GraphFlow control.
Contains all configuration for the web-based scheduling system.
"""

# Job Types
JOB_TYPE_GRAPHFLOW = "graphflow"
JOB_TYPE_SINGLE_POST = "single_post"
JOB_TYPE_RECURRING = "recurring_post"

# Job Status
JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

# Redis Keys for Job Storage
REDIS_KEY_JOBS = "scheduler:jobs"
REDIS_KEY_JOB_PREFIX = "scheduler:job:"
REDIS_KEY_GRAPHFLOW_PID = "scheduler:graphflow_pid"
REDIS_KEY_GRAPHFLOW_STATUS = "scheduler:graphflow_status"

# GraphFlow Process Status
GRAPHFLOW_STATUS_STOPPED = "stopped"
GRAPHFLOW_STATUS_STARTING = "starting"
GRAPHFLOW_STATUS_RUNNING = "running"
GRAPHFLOW_STATUS_STOPPING = "stopping"
GRAPHFLOW_STATUS_ERROR = "error"

# Scheduler Configuration
SCHEDULER_TIMEZONE = "Europe/Amsterdam"
SCHEDULER_JOBSTORE_URL = "redis://localhost:6379/1"
SCHEDULER_COALESCE = True
SCHEDULER_MAX_INSTANCES = 3

# Job Execution Limits
MAX_CONCURRENT_JOBS = 5
JOB_TIMEOUT_SECONDS = 300  # 5 minutes
GRAPHFLOW_TIMEOUT_SECONDS = 3600  # 1 hour

# API Messages
MSG_JOB_CREATED = "Job successfully created"
MSG_JOB_CANCELLED = "Job cancelled"
MSG_JOB_NOT_FOUND = "Job not found"
MSG_GRAPHFLOW_STARTED = "GraphFlow process started"
MSG_GRAPHFLOW_STOPPED = "GraphFlow process stopped"
MSG_GRAPHFLOW_ALREADY_RUNNING = "GraphFlow is already running"
MSG_GRAPHFLOW_NOT_RUNNING = "GraphFlow is not running"

# Error Messages
ERROR_INVALID_SCHEDULE = "Invalid schedule format"
ERROR_JOB_CREATION_FAILED = "Failed to create job"
ERROR_GRAPHFLOW_START_FAILED = "Failed to start GraphFlow"
ERROR_GRAPHFLOW_STOP_FAILED = "Failed to stop GraphFlow"
ERROR_SCHEDULER_NOT_AVAILABLE = "Scheduler service not available"

# Cron Presets for Quick Selection
CRON_PRESETS = {
    "every_hour": "0 * * * *",
    "every_2_hours": "0 */2 * * *",
    "every_4_hours": "0 */4 * * *",
    "every_6_hours": "0 */6 * * *",
    "daily_9am": "0 9 * * *",
    "daily_12pm": "0 12 * * *",
    "daily_6pm": "0 18 * * *",
    "weekdays_9am": "0 9 * * 1-5",
    "weekends_10am": "0 10 * * 6,0",
}

# Time Zone Options for UI
TIMEZONE_OPTIONS = [
    ("Europe/Amsterdam", "Amsterdam (CET/CEST)"),
    ("Europe/London", "London (GMT/BST)"),
    ("America/New_York", "New York (EST/EDT)"),
    ("America/Los_Angeles", "Los Angeles (PST/PDT)"),
    ("Asia/Tokyo", "Tokyo (JST)"),
    ("UTC", "UTC"),
]
