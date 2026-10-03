"""
shared_workflows/pipeline.py

Pipeline orchestration for multi-step workflows.

Provides workflow execution with dependency management and error handling.
"""

from typing import Callable, List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Step execution status."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'


@dataclass
class PipelineStep:
    """
    A single step in a pipeline.
    
    Attributes:
        step_id: Unique identifier
        name: Step name
        func: Function to execute
        depends_on: List of step IDs this depends on
        retry_count: Number of retries on failure
        timeout: Timeout in seconds
    """
    step_id: str
    name: str
    func: Callable
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 0
    timeout: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'step_id': self.step_id,
            'name': self.name,
            'func_name': self.func.__name__,
            'depends_on': self.depends_on,
            'retry_count': self.retry_count,
            'timeout': self.timeout,
        }


@dataclass
class StepResult:
    """
    Result of step execution.
    
    Attributes:
        step_id: Step identifier
        status: Execution status
        result: Return value
        error: Error message if failed
        started_at: Start time
        completed_at: Completion time
    """
    step_id: str
    status: StepStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'step_id': self.step_id,
            'status': self.status.value,
            'result': str(self.result) if self.result is not None else None,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class Pipeline:
    """
    Multi-step workflow pipeline.
    
    Executes steps in order respecting dependencies.
    
    Usage:
        pipeline = Pipeline(pipeline_id='scrape_pipeline')
        
        # Add steps
        pipeline.add_step(
            step_id='scrape',
            name='Scrape Sources',
            func=scrape_all_sources,
        )
        
        pipeline.add_step(
            step_id='validate',
            name='Validate Articles',
            func=validate_articles,
            depends_on=['scrape'],
        )
        
        pipeline.add_step(
            step_id='analyze',
            name='Run Analytics',
            func=run_analytics,
            depends_on=['validate'],
        )
        
        # Execute
        results = pipeline.execute()
        
        # Check results
        for result in results:
            print(f"{result.step_id}: {result.status.value}")
    """
    
    def __init__(self, pipeline_id: str, name: Optional[str] = None):
        """
        Initialize pipeline.
        
        Args:
            pipeline_id: Unique identifier
            name: Pipeline name
        """
        self.pipeline_id = pipeline_id
        self.name = name or pipeline_id
        self.steps: Dict[str, PipelineStep] = {}
        self.results: Dict[str, StepResult] = {}
    
    def add_step(
        self,
        step_id: str,
        name: str,
        func: Callable,
        depends_on: Optional[List[str]] = None,
        retry_count: int = 0,
        timeout: Optional[int] = None,
    ) -> PipelineStep:
        """
        Add step to pipeline.
        
        Args:
            step_id: Unique step identifier
            name: Step name
            func: Function to execute
            depends_on: List of step IDs this depends on
            retry_count: Number of retries on failure
            timeout: Timeout in seconds
            
        Returns:
            PipelineStep instance
        """
        step = PipelineStep(
            step_id=step_id,
            name=name,
            func=func,
            depends_on=depends_on or [],
            retry_count=retry_count,
            timeout=timeout,
        )
        
        self.steps[step_id] = step
        
        logger.info(f"Added step {step_id} to pipeline {self.pipeline_id}")
        
        return step
    
    def execute(self) -> List[StepResult]:
        """
        Execute pipeline.
        
        Returns:
            List of StepResult
        """
        logger.info(f"Starting pipeline {self.pipeline_id}")
        
        # Clear previous results
        self.results.clear()
        
        # Get execution order
        execution_order = self._get_execution_order()
        
        # Execute steps
        for step_id in execution_order:
            step = self.steps[step_id]
            
            # Check dependencies
            if not self._dependencies_met(step):
                logger.warning(f"Skipping {step_id}: dependencies not met")
                self.results[step_id] = StepResult(
                    step_id=step_id,
                    status=StepStatus.SKIPPED,
                    error="Dependencies not met",
                )
                continue
            
            # Execute step
            result = self._execute_step(step)
            self.results[step_id] = result
            
            # Stop if step failed
            if result.status == StepStatus.FAILED:
                logger.error(f"Pipeline {self.pipeline_id} failed at step {step_id}")
                break
        
        logger.info(f"Pipeline {self.pipeline_id} completed")
        
        return list(self.results.values())
    
    def _execute_step(self, step: PipelineStep) -> StepResult:
        """Execute a single step."""
        logger.info(f"Executing step {step.step_id}: {step.name}")
        
        result = StepResult(
            step_id=step.step_id,
            status=StepStatus.RUNNING,
            started_at=datetime.now(),
        )
        
        attempts = 0
        max_attempts = step.retry_count + 1
        
        while attempts < max_attempts:
            try:
                # Execute function
                output = step.func()
                
                # Success
                result.status = StepStatus.COMPLETED
                result.result = output
                result.completed_at = datetime.now()
                
                logger.info(f"Step {step.step_id} completed successfully")
                
                break
            
            except Exception as e:
                attempts += 1
                
                if attempts >= max_attempts:
                    # Failed after all retries
                    result.status = StepStatus.FAILED
                    result.error = str(e)
                    result.completed_at = datetime.now()
                    
                    logger.error(f"Step {step.step_id} failed: {e}")
                else:
                    logger.warning(f"Step {step.step_id} failed, retrying ({attempts}/{max_attempts})")
        
        return result
    
    def _get_execution_order(self) -> List[str]:
        """Get step execution order respecting dependencies."""
        order = []
        visited = set()
        
        def visit(step_id: str):
            if step_id in visited:
                return
            
            step = self.steps[step_id]
            
            # Visit dependencies first
            for dep_id in step.depends_on:
                if dep_id in self.steps:
                    visit(dep_id)
            
            visited.add(step_id)
            order.append(step_id)
        
        # Visit all steps
        for step_id in self.steps:
            visit(step_id)
        
        return order
    
    def _dependencies_met(self, step: PipelineStep) -> bool:
        """Check if step dependencies are met."""
        for dep_id in step.depends_on:
            if dep_id not in self.results:
                return False
            
            if self.results[dep_id].status != StepStatus.COMPLETED:
                return False
        
        return True
    
    def get_results(self) -> List[StepResult]:
        """Get execution results."""
        return list(self.results.values())
    
    def get_result(self, step_id: str) -> Optional[StepResult]:
        """Get result for specific step."""
        return self.results.get(step_id)


# Export
__all__ = [
    'Pipeline',
    'PipelineStep',
    'StepResult',
    'StepStatus',
]
