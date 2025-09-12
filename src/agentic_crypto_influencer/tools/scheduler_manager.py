"""
Advanced scheduler manager for GraphFlow and job management.
Provides web-controlled scheduling that's as reliable as launchd but more flexible.
"""

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess  # nosec B404
from subprocess import TimeoutExpired
import sys
import threading
from typing import Any

from apscheduler.executors.pool import ThreadPoolExecutor  # type: ignore[import]
from apscheduler.jobstores.redis import RedisJobStore  # type: ignore[import]
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import]
from apscheduler.triggers.date import DateTrigger  # type: ignore[import]
import psutil

from src.agentic_crypto_influencer.config.logging_config import get_logger
from src.agentic_crypto_influencer.config.scheduler_constants import (
    CRON_PRESETS,
    ERROR_GRAPHFLOW_START_FAILED,
    ERROR_GRAPHFLOW_STOP_FAILED,
    ERROR_INVALID_SCHEDULE,
    ERROR_JOB_CREATION_FAILED,
    GRAPHFLOW_STATUS_ERROR,
    GRAPHFLOW_STATUS_RUNNING,
    GRAPHFLOW_STATUS_STARTING,
    GRAPHFLOW_STATUS_STOPPED,
    GRAPHFLOW_STATUS_STOPPING,
    GRAPHFLOW_TIMEOUT_SECONDS,
    JOB_TYPE_GRAPHFLOW,
    JOB_TYPE_RECURRING,
    JOB_TYPE_SINGLE_POST,
    MAX_CONCURRENT_JOBS,
    MSG_GRAPHFLOW_ALREADY_RUNNING,
    MSG_GRAPHFLOW_NOT_RUNNING,
    MSG_GRAPHFLOW_STARTED,
    MSG_GRAPHFLOW_STOPPED,
    MSG_JOB_CREATED,
    REDIS_KEY_GRAPHFLOW_PID,
    REDIS_KEY_GRAPHFLOW_STATUS,
    SCHEDULER_COALESCE,
    SCHEDULER_MAX_INSTANCES,
    SCHEDULER_TIMEZONE,
)
from src.agentic_crypto_influencer.tools.redis_handler import RedisHandler

logger = get_logger(__name__)


class SchedulerManager:
    """
    Advanced job scheduler with GraphFlow process management.
    Provides web-controlled scheduling more powerful than launchd.
    """

    def __init__(self) -> None:
        """Initialize the scheduler manager."""
        self.redis_handler = RedisHandler(lazy_connect=True)
        self.scheduler: BackgroundScheduler | None = None
        self.graphflow_process: subprocess.Popen[bytes] | None = None
        self.graphflow_thread: threading.Thread | None = None
        self._setup_scheduler()

    def _setup_scheduler(self) -> None:
        """Setup the APScheduler with Redis persistence."""
        try:
            # Configure job store for persistence
            jobstores = {
                "default": RedisJobStore(host="localhost", port=6379, db=1, password=None)
            }

            # Configure executors
            executors = {
                "default": ThreadPoolExecutor(MAX_CONCURRENT_JOBS),
            }

            # Job defaults
            job_defaults: dict[str, Any] = {
                "coalesce": SCHEDULER_COALESCE,
                "max_instances": SCHEDULER_MAX_INSTANCES,
            }

            # Create scheduler
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone=SCHEDULER_TIMEZONE,
            )

            logger.info("Scheduler configured successfully")

        except Exception as e:
            logger.error(f"Failed to setup scheduler: {e}")
            raise

    def start_scheduler(self) -> None:
        """Start the background scheduler."""
        try:
            if self.scheduler and not self.scheduler.running:
                self.scheduler.start()
                logger.info("Scheduler started successfully")
            else:
                logger.warning("Scheduler already running or not configured")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def stop_scheduler(self) -> None:
        """Stop the background scheduler."""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            raise

    def create_scheduled_job(
        self,
        job_type: str,
        schedule_type: str,
        schedule_value: str,
        job_name: str,
        job_description: str = "",
        job_args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new scheduled job.

        Args:
            job_type: Type of job (graphflow, single_post, recurring_post)
            schedule_type: Type of schedule (cron, date, preset)
            schedule_value: Schedule specification
            job_name: Human readable name
            job_description: Optional description
            job_args: Additional job arguments

        Returns:
            Job information dictionary
        """
        try:
            if not self.scheduler:
                raise RuntimeError("Scheduler not initialized")

            # Generate unique job ID
            job_id = f"{job_type}_{int(datetime.now(UTC).timestamp())}"

            # Parse schedule
            trigger = self._parse_schedule(schedule_type, schedule_value)
            if not trigger:
                return {"success": False, "error": ERROR_INVALID_SCHEDULE}

            # Select job function based on type
            job_func = self._get_job_function(job_type)
            if not job_func:
                return {"success": False, "error": f"Unknown job type: {job_type}"}

            # Add job to scheduler
            self.scheduler.add_job(
                func=job_func,
                trigger=trigger,
                id=job_id,
                name=job_name,
                args=[job_args or {}],
                replace_existing=True,
            )

            # Store job metadata in Redis
            job_metadata: dict[str, Any] = {
                "id": job_id,
                "name": job_name,
                "description": job_description,
                "type": job_type,
                "schedule_type": schedule_type,
                "schedule_value": schedule_value,
                "created_at": datetime.now(UTC).isoformat(),
                "args": job_args or {},
                "status": "scheduled",
            }

            self.redis_handler.set(
                f"job:{job_id}",
                json.dumps(job_metadata),
                ex=86400 * 30,  # Keep for 30 days
            )

            logger.info(f"Created scheduled job: {job_name} ({job_id})")

            return {"success": True, "message": MSG_JOB_CREATED, "job": job_metadata}

        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            return {"success": False, "error": f"{ERROR_JOB_CREATION_FAILED}: {e!s}"}

    def _parse_schedule(self, schedule_type: str, schedule_value: str) -> Any:
        """Parse schedule specification into APScheduler trigger."""
        try:
            if schedule_type == "preset":
                if schedule_value in CRON_PRESETS:
                    cron_expr = CRON_PRESETS[schedule_value]
                    return CronTrigger.from_crontab(cron_expr)
                else:
                    logger.error(f"Unknown preset: {schedule_value}")
                    return None

            elif schedule_type == "cron":
                return CronTrigger.from_crontab(schedule_value)

            elif schedule_type == "date":
                run_date = datetime.fromisoformat(schedule_value)
                return DateTrigger(run_date=run_date)

            else:
                logger.error(f"Unknown schedule type: {schedule_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to parse schedule: {e}")
            return None

    def _get_job_function(self, job_type: str) -> Any:
        """Get the appropriate job function for job type."""
        job_functions = {
            JOB_TYPE_GRAPHFLOW: self._execute_graphflow_job,
            JOB_TYPE_SINGLE_POST: self._execute_single_post_job,
            JOB_TYPE_RECURRING: self._execute_recurring_job,
        }
        return job_functions.get(job_type)

    def _execute_graphflow_job(self, job_args: dict[str, Any]) -> None:
        """Execute a GraphFlow job."""
        logger.info("Starting scheduled GraphFlow execution")
        try:
            # Start GraphFlow process
            result = self.start_graphflow()
            if not result["success"]:
                raise RuntimeError(result["error"])

            # Monitor the process
            self._monitor_graphflow_process()

        except Exception as e:
            logger.error(f"GraphFlow job failed: {e}")
            raise

    def _execute_single_post_job(self, job_args: dict[str, Any]) -> None:
        """Execute a single post job."""
        logger.info("Executing single post job")
        try:
            # This could run a simplified version of GraphFlow
            # or call specific agents directly
            self._run_single_post_workflow(job_args)
        except Exception as e:
            logger.error(f"Single post job failed: {e}")
            raise

    def _execute_recurring_job(self, job_args: dict[str, Any]) -> None:
        """Execute a recurring job."""
        logger.info("Executing recurring job")
        try:
            # Similar to single post but with different parameters
            self._run_recurring_workflow(job_args)
        except Exception as e:
            logger.error(f"Recurring job failed: {e}")
            raise

    def start_graphflow(self) -> dict[str, Any]:
        """Start the GraphFlow process."""
        try:
            # Check if already running
            if self.is_graphflow_running():
                return {"success": False, "error": MSG_GRAPHFLOW_ALREADY_RUNNING}

            # Set status to starting
            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_STARTING)

            # Get path to GraphFlow script
            project_root = Path(__file__).parent.parent.parent.parent
            graphflow_path = (
                project_root / "src" / "agentic_crypto_influencer" / "graphflow" / "graphflow.py"
            )

            if not graphflow_path.exists():
                raise FileNotFoundError(f"GraphFlow script not found: {graphflow_path}")

            # Start process
            cmd = [sys.executable, str(graphflow_path)]
            self.graphflow_process = subprocess.Popen(  # nosec B603
                cmd,
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
            )

            # Store process PID
            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_PID, str(self.graphflow_process.pid))
            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_RUNNING)

            # Start monitoring thread
            # In test runs (pytest), avoid starting background threads to prevent
            # PytestUnhandledThreadExceptionWarning and flaky test behavior.
            if "PYTEST_CURRENT_TEST" not in os.environ:
                self.graphflow_thread = threading.Thread(
                    target=self._monitor_graphflow_process, daemon=True
                )
                self.graphflow_thread.start()
            else:
                self.graphflow_thread = None

            logger.info(f"GraphFlow started with PID: {self.graphflow_process.pid}")

            return {
                "success": True,
                "message": MSG_GRAPHFLOW_STARTED,
                "pid": self.graphflow_process.pid,
            }

        except Exception as e:
            logger.error(f"Failed to start GraphFlow: {e}")
            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_ERROR)
            return {"success": False, "error": f"{ERROR_GRAPHFLOW_START_FAILED}: {e!s}"}

    def stop_graphflow(self) -> dict[str, Any]:
        """Stop the GraphFlow process."""
        try:
            if not self.is_graphflow_running():
                return {"success": False, "error": MSG_GRAPHFLOW_NOT_RUNNING}

            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_STOPPING)

            if self.graphflow_process:
                # Graceful shutdown first
                self.graphflow_process.terminate()

                # Wait for graceful shutdown
                try:
                    self.graphflow_process.wait(timeout=10)
                except TimeoutExpired:
                    # Force kill if needed
                    self.graphflow_process.kill()
                    self.graphflow_process.wait()

                self.graphflow_process = None

            # Clean up Redis keys
            self.redis_handler.delete(REDIS_KEY_GRAPHFLOW_PID)
            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_STOPPED)

            logger.info("GraphFlow stopped successfully")

            return {"success": True, "message": MSG_GRAPHFLOW_STOPPED}

        except Exception as e:
            logger.error(f"Failed to stop GraphFlow: {e}")
            return {"success": False, "error": f"{ERROR_GRAPHFLOW_STOP_FAILED}: {e!s}"}

    def is_graphflow_running(self) -> bool:
        """Check if GraphFlow process is currently running."""
        try:
            status = self.redis_handler.get(REDIS_KEY_GRAPHFLOW_STATUS)
            if status and status.decode() == GRAPHFLOW_STATUS_RUNNING:
                # Double-check with process
                pid_str = self.redis_handler.get(REDIS_KEY_GRAPHFLOW_PID)
                if pid_str:
                    pid = int(pid_str.decode())
                    return bool(psutil.pid_exists(pid))
            return False
        except Exception as e:
            logger.error(f"Error checking GraphFlow status: {e}")
            return False

    def get_graphflow_status(self) -> dict[str, Any]:
        """Get current GraphFlow status."""
        try:
            status = self.redis_handler.get(REDIS_KEY_GRAPHFLOW_STATUS)
            status_str = status.decode() if status else GRAPHFLOW_STATUS_STOPPED

            pid_str = self.redis_handler.get(REDIS_KEY_GRAPHFLOW_PID)
            pid = int(pid_str.decode()) if pid_str else None

            return {"status": status_str, "pid": pid, "is_running": self.is_graphflow_running()}
        except Exception as e:
            logger.error(f"Error getting GraphFlow status: {e}")
            return {"status": GRAPHFLOW_STATUS_ERROR, "pid": None, "is_running": False}

    def _monitor_graphflow_process(self) -> None:
        """Monitor the GraphFlow process in background."""
        if not self.graphflow_process:
            return

        try:
            # Wait for process to complete
            result = self.graphflow_process.communicate(timeout=GRAPHFLOW_TIMEOUT_SECONDS)
            _stdout, stderr = (
                result if isinstance(result, tuple) and len(result) == 2 else (None, None)
            )

            # Process completed
            if self.graphflow_process.returncode == 0:
                logger.info("GraphFlow completed successfully")
                self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_STOPPED)
            else:
                logger.error(
                    f"GraphFlow failed with return code: {self.graphflow_process.returncode}"
                )
                if stderr:
                    logger.error(f"GraphFlow stderr: {stderr.decode()}")
                self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_ERROR)

        except TimeoutExpired:
            logger.warning("GraphFlow process timeout, terminating")
            self.graphflow_process.terminate()
            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_ERROR)
        except Exception as e:
            logger.error(f"Error monitoring GraphFlow: {e}")
            self.redis_handler.set(REDIS_KEY_GRAPHFLOW_STATUS, GRAPHFLOW_STATUS_ERROR)
        finally:
            # Clean up
            self.redis_handler.delete(REDIS_KEY_GRAPHFLOW_PID)
            self.graphflow_process = None

    def get_all_jobs(self) -> list[dict[str, Any]]:
        """Get all scheduled jobs."""
        try:
            jobs: list[dict[str, Any]] = []
            if self.scheduler:
                for job in self.scheduler.get_jobs():
                    job_info: dict[str, Any] = {
                        "id": job.id,
                        "name": job.name,
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger),
                    }
                    jobs.append(job_info)
            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Cancel a scheduled job."""
        try:
            if self.scheduler:
                self.scheduler.remove_job(job_id)
                self.redis_handler.delete(f"job:{job_id}")
                return {"success": True, "message": f"Job {job_id} cancelled"}
            return {"success": False, "error": "Scheduler not available"}
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return {"success": False, "error": str(e)}

    def _run_single_post_workflow(self, job_args: dict[str, Any]) -> None:
        """Run a single post workflow (simplified GraphFlow)."""
        # Implementation for single post
        logger.info("Running single post workflow")
        # This would be a simplified version of the main GraphFlow

    def _run_recurring_workflow(self, job_args: dict[str, Any]) -> None:
        """Run a recurring workflow."""
        # Implementation for recurring posts
        logger.info("Running recurring workflow")

    def get_scheduled_jobs(self) -> list[dict[str, Any]]:
        """Get list of all scheduled jobs."""
        if not self.scheduler:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": getattr(job, "name", str(job.id)),
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
            )
        return jobs

    def get_job_history(self) -> list[dict[str, Any]]:
        """Get job execution history."""
        # This would typically come from a database or log storage
        # For now, return empty list as it's not implemented yet
        return []
