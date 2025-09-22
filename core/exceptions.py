"""
Custom exception classes for the workflow engine.
These help differentiate engine-specific errors from generic Python errors.
"""

class WorkflowError(Exception):
    """Base class for all workflow-related errors."""
    pass


class TaskFailedError(WorkflowError):
    """Raised when a task fails and retries are exhausted."""
    def __init__(self, task_id, original_exception):
        self.task_id = task_id
        self.original_exception = original_exception
        super().__init__(f"Task '{task_id}' failed: {original_exception}")


class CircularDependencyError(WorkflowError):
    """Raised when the DAG contains a cycle (invalid workflow)."""
    def __init__(self, cycle):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {cycle}")


class InvalidTaskError(WorkflowError):
    """Raised when a task is misconfigured or invalid."""
    pass
