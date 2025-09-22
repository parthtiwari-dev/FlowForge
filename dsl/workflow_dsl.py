"""
workflow_dsl.py

Purpose:
    Provides a domain-specific language (DSL) for declaratively defining workflows, tasks, and dependencies.
    Enables users to build complex workflows using simple syntax, decorators, or configuration files,
    abstracting away boilerplate Python code for orchestration and execution.

Key Responsibilities:
    - Define a clean, readable API for specifying tasks, dependencies, and workflow parameters.
    - Support decorator-based and/or config-based workflow definitions.
    - Parse workflow specifications and translate them into engine objects (Task, DAG, Scheduler).
    - Validate DSL input for correctness, dependency resolution, and acyclic structure.
    - Enable users to quickly author, modify, or visualize workflows with minimal code.
    - Provide extensibility for custom task operations, resource contexts, and execution options.

Design & Methods to Implement:
    1. Decorators and classes/functions for defining tasks, dependencies, and workflow blocks.
    2. Parsers for DSL syntax and/or config formats (YAML/JSON/Pythonic mini-language).
    3. Methods to translate DSL definitions into engine components (instantiating Tasks, adding to DAG, launching Scheduler).
    4. Validation logic for user input and workflow structure.
    5. Example usage and API documentation for end-users.

Usage:
    Users can author workflows using decorators, config files, or short DSL scripts.
    The engine parses and loads these definitions, builds the internal DAG/Task objects, and executes the workflow.
    This makes workflow authoring user-friendly and supports rapid prototyping and sharing.
"""


# dsl/workflow_dsl.py

from contextlib import contextmanager
from core.task import Task, TaskState
from core.dag import DAG
from core.scheduler import Scheduler
from core.executor import LocalExecutor, ThreadedExecutor
from core.event import EventManager, WorkflowEvent
from core.context import with_context
from core.exceptions import InvalidTaskError
from state.persistence import PersistenceManager
from utils.logging_utils import set_log_level, log_task_started, log_task_succeeded, log_task_failed, log_task_retried, log_workflow_started, log_workflow_completed
from utils.metrics_utils import MetricsManager

set_log_level("INFO")  # Default logging level for DSL

# Global registry to track tasks in a workflow context
_CURRENT_WORKFLOW = None

class Workflow:
    """
    Context manager for a workflow DSL.
    Collects tasks, builds DAG, and runs workflow.
    """
    def __init__(self, name, executor_type="local", max_workers=2, checkpoint_file=None):
        self.name = name
        self.executor_type = executor_type
        self.max_workers = max_workers
        self.dag = DAG()
        self.events = EventManager()
        self.metrics = MetricsManager()
        self.checkpoint_file = checkpoint_file
        self.persistence = PersistenceManager(checkpoint_file) if checkpoint_file else None
        self._tasks = []

        # Hook logs
        self._register_logging()
        # Hook metrics
        self._register_metrics()

    def _register_logging(self):
        self.events.register(WorkflowEvent.TASK_STARTED, log_task_started)
        self.events.register(WorkflowEvent.TASK_SUCCEEDED, log_task_succeeded)
        self.events.register(WorkflowEvent.TASK_FAILED, log_task_failed)
        self.events.register(WorkflowEvent.TASK_RETRIED, log_task_retried)
        self.events.register(WorkflowEvent.WORKFLOW_STARTED, log_workflow_started)
        self.events.register(WorkflowEvent.WORKFLOW_COMPLETED, log_workflow_completed)

    def _register_metrics(self):
        self.events.register(WorkflowEvent.TASK_STARTED, self.metrics.task_started)
        self.events.register(WorkflowEvent.TASK_SUCCEEDED, self.metrics.task_succeeded)
        self.events.register(WorkflowEvent.TASK_FAILED, self.metrics.task_failed)
        self.events.register(WorkflowEvent.TASK_RETRIED, self.metrics.task_retried)
        self.events.register(WorkflowEvent.WORKFLOW_STARTED, self.metrics.workflow_started)
        self.events.register(WorkflowEvent.WORKFLOW_COMPLETED, self.metrics.workflow_completed)

    def add_task(self, task: Task):
        self.dag.add_task(task)
        self._tasks.append(task)
        # Attach persistence autosave
        if self.persistence:
            self.persistence.attach_to_events(self.events)

    def run(self):
        self.events.notify(WorkflowEvent.WORKFLOW_STARTED)

        scheduler = Scheduler(self.dag, executor_type=self.executor_type, max_workers=self.max_workers)

        # Wrap executor to fire events and retries
        def wrap_task_execution(task):
            self.events.notify(WorkflowEvent.TASK_STARTED, task=task)
            success = task.run()
            if success:
                self.events.notify(WorkflowEvent.TASK_SUCCEEDED, task=task)
            elif task.state == TaskState.FAILED:
                self.events.notify(WorkflowEvent.TASK_FAILED, task=task, exception=task.exception)
            elif task.state == TaskState.PENDING and task.retry_count > 0:
                self.events.notify(WorkflowEvent.TASK_RETRIED, task=task)
            return success

        if isinstance(scheduler.executor, LocalExecutor):
            scheduler.executor.execute = wrap_task_execution
        elif isinstance(scheduler.executor, ThreadedExecutor):
            original_execute_many = scheduler.executor.execute_many
            def wrapped_execute_many(tasks):
                results = []
                for task in tasks:
                    self.events.notify(WorkflowEvent.TASK_STARTED, task=task)
                results = original_execute_many(tasks)
                for i, task in enumerate(tasks):
                    if results[i]:
                        self.events.notify(WorkflowEvent.TASK_SUCCEEDED, task=task)
                    elif task.state == TaskState.FAILED:
                        self.events.notify(WorkflowEvent.TASK_FAILED, task=task, exception=task.exception)
                    elif task.state == TaskState.PENDING and task.retry_count > 0:
                        self.events.notify(WorkflowEvent.TASK_RETRIED, task=task)
                return results
            scheduler.executor.execute_many = wrapped_execute_many

        scheduler.run()
        self.events.notify(WorkflowEvent.WORKFLOW_COMPLETED)
        self.metrics.print_task_metrics()
        self.metrics.print_workflow_metrics()

@contextmanager
def workflow(name, executor_type="local", max_workers=2, checkpoint_file=None):
    """
    Context manager version of Workflow DSL
    """
    global _CURRENT_WORKFLOW
    _CURRENT_WORKFLOW = Workflow(name, executor_type, max_workers, checkpoint_file)
    try:
        yield _CURRENT_WORKFLOW
    finally:
        _CURRENT_WORKFLOW = None

def task(func=None, *, with_ctx=None, max_retries=0):
    """
    Decorator to define a task in the current workflow.
    - with_ctx: optional function returning a context manager
    """
    def decorator(fn):
        if _CURRENT_WORKFLOW is None:
            raise RuntimeError("No active workflow. Use @task inside a Workflow context or 'with workflow(...)'")
        wrapped_fn = fn
        if with_ctx:
            wrapped_fn = with_context(with_ctx)(fn)
        t = Task(fn.__name__, func=wrapped_fn, max_retries=max_retries)
        _CURRENT_WORKFLOW.add_task(t)
        return wrapped_fn
    if func:
        return decorator(func)
    return decorator
