"""
retry_utils.py

Purpose:
    Provides utilities and decorators to manage retry logic and backoff strategies for task execution.
    Handles error detection, retry counting, delay/backoff between attempts, and recoverable failures.
    Ensures robust automatic error handling for unreliable or flaky workflow tasks.

Key Responsibilities:
    - Implement retry decorators/functions to wrap task logic with automatic retry on exception.
    - Support configurable retry limits, backoff intervals (fixed, exponential), and exception filters.
    - Integrate with task state (FAILED/PENDING), error reporting, and metrics.
    - Enable hooks for retry events in the observer system.
    - Simplify error handling in workflow/task code for cleaner, DRY implementation.

Usage:
    Decorate task functions with retry utilities or invoke retry logic in Scheduler/Task classes.
    Customize retry parameters per task for nuanced fault tolerance and recovery.
"""


import time
from core.task import Task, TaskState
from core.event import EventManager

def retry_task(task: Task, event_manager: EventManager = None, delay: float = 0):
    """
    Executes a task with retry logic based on task.max_retries.
    
    Args:
        task (Task): Task instance to execute.
        event_manager (EventManager): Optional EventManager to notify about retries.
        delay (float): Optional delay (in seconds) between retries.
    """
    while task.retry_count <= task.max_retries:
        try:
            task.run()
            # If task succeeded, break out
            if task.state == TaskState.SUCCESS:
                return True
        except Exception:
            pass

        # Task failed, check if retry is possible
        if task.retry_count <= task.max_retries:
            if event_manager:
                event_manager.notify("task_retried", task=task)
            task.state = TaskState.PENDING
            task.retry_count += 1
            if delay > 0:
                time.sleep(delay)
        else:
            task.state = TaskState.FAILED
            if event_manager:
                event_manager.notify("task_failed", task=task, exception=task.exception)
            return False