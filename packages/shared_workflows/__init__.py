"""
shared_workflows

Workflow scheduling and pipeline orchestration.

Modules:
- scheduler: APScheduler wrapper
- pipeline: Multi-step workflow execution

Provides unified scheduling and pipeline execution for both platforms.
"""

from .scheduler import (
    WorkflowScheduler,
    Job,
    APSCHEDULER_AVAILABLE,
)
from .pipeline import (
    Pipeline,
    PipelineStep,
    StepResult,
    StepStatus,
)

__all__ = [
    # Scheduler
    "WorkflowScheduler",
    "Job",
    "APSCHEDULER_AVAILABLE",
    
    # Pipeline
    "Pipeline",
    "PipelineStep",
    "StepResult",
    "StepStatus",
]
