"""
task.py

Purpose:
    Defines the core Task abstraction for the workflow orchestration engine.
    Each Task represents a single unit of work in a workflow (node in a DAG),
    encapsulating its execution logic, dependencies, state management, and retry/error handling.

Key Responsibilities:
    - Represent a workflow task as a Python object with a unique name/ID.
    - Allow specification and management of dependencies between tasks.
    - Track and manage task state throughout its lifecycle (e.g., PENDING, RUNNING, SUCCESS, FAILED).
    - Provide a method for executing the task's logic (to be implemented in subclasses or at instantiation).
    - Implement error handling and configurable retry logic for robustness.
    - Offer helper methods for dependency management, state transitions, and reset functionality.
    - Serve as the foundation for DAG construction, scheduling, execution, and monitoring across the engine.

Design & Methods to Implement:
    1. Task states as constants or an Enum for easy state tracking.
    2. Task class with:
        - __init__ constructor accepting name/ID, optional dependencies, and retry settings.
        - add_dependency(task): Add another Task as a dependency.
        - run(): (Abstract/placeholder) Method for actual execution logic, to be overridden.
        - reset(): Reset state and retry count for reruns.
        - mark_success(), mark_failed(): Change state and increment retries as appropriate.
        - Properties or methods for checking if ready/runnable (all dependencies succeeded).
    3. Internal attributes for:
        - Name/ID
        - Dependencies (set or list of Task objects)
        - State
        - Max-retries and retry counter

Usage:
    Other engine modules (dag.py, scheduler.py, executor.py) will use this Task abstraction
    for building workflows, managing execution order, handling concurrency, and logging outcomes.

By completing this file as specified above, you will have a robust Task foundation
on which to build the workflow orchestration engine.
"""

from enum import Enum


class TaskState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Task:
    def __init__(self, name, func=None, max_retries=0):
        self.name = name
        self.func = func
        self.dependencies = []
        self.state = TaskState.PENDING
        self.max_retries = max_retries
        self.retry_count = 0
        self.result = None         # <-- add this
        self.exception = None      # <-- add this

    # ... rest of the code same as optimized version


    def add_dependency(self, task):
        self.dependencies.append(task)

    def is_ready(self):
        """Check if all dependencies are successful"""
        return all(dep.state == TaskState.SUCCESS for dep in self.dependencies)

    def run(self):
        """Execute the task respecting dependencies and retries"""
        if not self.is_ready():
            print(f"Task {self.name} cannot run yet. Dependencies not met.")
            return False

        self.state = TaskState.RUNNING
        try:
            if self.func:
                self.result = self.func()  # <-- store result here
            self.state = TaskState.SUCCESS
            print(f"Task {self.name} executed successfully.")
            return True
        except Exception as e:
            self.retry_count += 1
            self.exception = e
            print(f"Task {self.name} failed with error: {e}")
            if self.retry_count <= self.max_retries:
                self.state = TaskState.PENDING
                print(f"Retrying Task {self.name} (attempt {self.retry_count})...")
            else:
                self.state = TaskState.FAILED
            return False

    def reset(self):
        """Reset the task state and retry count for reruns"""
        self.state = TaskState.PENDING
        self.retry_count = 0
