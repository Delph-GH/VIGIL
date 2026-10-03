"""
shared_workflows/scheduler.py

APScheduler wrapper for workflow scheduling.

Provides unified scheduling interface for both platforms.
"""

from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
import logging

# Optional dependency
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None
    CronTrigger = None
    IntervalTrigger = None


logger = logging.getLogger(__name__)


class Job:
    """
    Represents a scheduled job.
    
    Attributes:
        job_id: Unique identifier
        func: Function to execute
        trigger: Trigger type
        next_run: Next scheduled run
        status: Job status
    """
    
    def __init__(
        self,
        job_id: str,
        func: Callable,
        trigger: str,
        next_run: Optional[datetime] = None,
        status: str = 'pending',
    ):
        self.job_id = job_id
        self.func = func
        self.trigger = trigger
        self.next_run = next_run
        self.status = status
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'job_id': self.job_id,
            'func_name': self.func.__name__,
            'trigger': self.trigger,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'status': self.status,
        }


class WorkflowScheduler:
    """
    Unified scheduler wrapper for APScheduler.
    
    Provides simple interface for job scheduling with:
    - Cron scheduling
    - Interval scheduling
    - Job management
    - Error handling
    
    Usage:
        scheduler = WorkflowScheduler()
        
        # Schedule with cron
        scheduler.schedule_cron(
            job_id='daily_scrape',
            func=scrape_sources,
            cron='0 8 * * *',  # Daily at 8am
        )
        
        # Schedule with interval
        scheduler.schedule_interval(
            job_id='check_health',
            func=health_check,
            minutes=15,  # Every 15 minutes
        )
        
        # Start scheduler
        scheduler.start()
    """
    
    def __init__(self):
        """Initialize scheduler."""
        if not APSCHEDULER_AVAILABLE:
            raise ImportError(
                "APScheduler is required. Install with: pip install apscheduler"
            )
        
        # Create scheduler with memory job store
        jobstores = {
            'default': MemoryJobStore()
        }
        
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self._jobs: Dict[str, Job] = {}
        self._running = False
    
    def schedule_cron(
        self,
        job_id: str,
        func: Callable,
        cron: str,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict] = None,
    ) -> Job:
        """
        Schedule job with cron expression.
        
        Args:
            job_id: Unique job identifier
            func: Function to execute
            cron: Cron expression (e.g., "0 8 * * *")
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Job instance
        """
        # Parse cron expression
        parts = cron.split()
        
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron}")
        
        minute, hour, day, month, day_of_week = parts
        
        # Create trigger
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )
        
        # Add job
        apscheduler_job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
        )
        
        # Create Job instance
        job = Job(
            job_id=job_id,
            func=func,
            trigger='cron',
            next_run=apscheduler_job.next_run_time,
            status='scheduled',
        )
        
        self._jobs[job_id] = job
        
        logger.info(f"Scheduled job {job_id} with cron: {cron}")
        
        return job
    
    def schedule_interval(
        self,
        job_id: str,
        func: Callable,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict] = None,
    ) -> Job:
        """
        Schedule job with interval.
        
        Args:
            job_id: Unique job identifier
            func: Function to execute
            minutes: Interval in minutes
            hours: Interval in hours
            days: Interval in days
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Job instance
        """
        # Create trigger
        trigger = IntervalTrigger(
            minutes=minutes or 0,
            hours=hours or 0,
            days=days or 0,
        )
        
        # Add job
        apscheduler_job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
        )
        
        # Create Job instance
        interval_str = []
        if days:
            interval_str.append(f"{days}d")
        if hours:
            interval_str.append(f"{hours}h")
        if minutes:
            interval_str.append(f"{minutes}m")
        
        job = Job(
            job_id=job_id,
            func=func,
            trigger=f"interval: {' '.join(interval_str)}",
            next_run=apscheduler_job.next_run_time,
            status='scheduled',
        )
        
        self._jobs[job_id] = job
        
        logger.info(f"Scheduled job {job_id} with interval: {' '.join(interval_str)}")
        
        return job
    
    def remove_job(self, job_id: str):
        """
        Remove scheduled job.
        
        Args:
            job_id: Job identifier
        """
        self.scheduler.remove_job(job_id)
        
        if job_id in self._jobs:
            del self._jobs[job_id]
        
        logger.info(f"Removed job {job_id}")
    
    def start(self):
        """Start scheduler."""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop scheduler."""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("Scheduler stopped")
    
    def list_jobs(self) -> List[Job]:
        """
        List all scheduled jobs.
        
        Returns:
            List of Job instances
        """
        return list(self._jobs.values())
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job or None
        """
        return self._jobs.get(job_id)
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running


# Export
__all__ = [
    'WorkflowScheduler',
    'Job',
    'APSCHEDULER_AVAILABLE',
]
