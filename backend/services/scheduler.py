"""
APScheduler-based background job scheduler for signal polling.

Runs signal polling every 15 minutes to check all zones for disruption conditions.
In production, consider using Celery Beat or a managed scheduler like AWS CloudWatch Events.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(
    timezone="UTC",
    job_defaults={
        "coalesce": True,  # Combine multiple pending runs into one
        "max_instances": 1,  # Only one instance of each job at a time
        "misfire_grace_time": 300,  # 5 min grace period for missed jobs
    }
)

# Configuration
POLL_INTERVAL_MINUTES = 15


def _job_listener(event):
    """Log job execution results."""
    if event.exception:
        logger.error(
            f"Job {event.job_id} failed with exception: {event.exception}",
            exc_info=True
        )
    else:
        logger.info(f"Job {event.job_id} executed successfully")


def start_scheduler():
    """
    Initialize and start the background job scheduler.
    
    Registers the signal polling job to run every 15 minutes.
    """
    from services.signal_poller import poll_all_zones
    
    # Add job listener for monitoring
    scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    # Register the signal polling job
    scheduler.add_job(
        poll_all_zones,
        trigger=IntervalTrigger(minutes=POLL_INTERVAL_MINUTES),
        id="signal_poll",
        name="Poll all zones for disruption signals",
        replace_existing=True,
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info(
        f"Signal polling scheduler started — polling every {POLL_INTERVAL_MINUTES} minutes"
    )


def stop_scheduler():
    """
    Gracefully shut down the scheduler.
    
    Waits for running jobs to complete before shutting down.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Signal polling scheduler stopped")


def trigger_immediate_poll():
    """
    Manually trigger an immediate poll (useful for testing/admin).
    
    Returns the job ID for tracking.
    """
    from services.signal_poller import poll_all_zones
    
    job = scheduler.add_job(
        poll_all_zones,
        id="signal_poll_manual",
        name="Manual signal poll trigger",
        replace_existing=True,
    )
    logger.info(f"Manual poll triggered — job_id: {job.id}")
    return job.id


def get_scheduler_status() -> dict:
    """Get current scheduler status and job information."""
    jobs = scheduler.get_jobs()
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in jobs
        ],
        "poll_interval_minutes": POLL_INTERVAL_MINUTES,
    }
