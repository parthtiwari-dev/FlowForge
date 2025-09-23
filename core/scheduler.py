"""
scheduler.py

Purpose:
    Defines the Scheduler for the workflow orchestration engine. The Scheduler is responsible for
    coordinating the execution of tasks within a DAG, ensuring that each task runs only after its
    dependencies are satisfied. It manages task states, triggers execution, handles retries,
    and optionally supports concurrency (threads/processes).

Key Responsibilities:
    - Accept a DAG of registered Task instances for scheduling.
    - Identify and dispatch tasks that are ready to run (all dependencies successful).
    - Monitor state transitions for each task (e.g., RUNNING, SUCCESS, FAILED).
    - Implement retry logic for failed tasks respecting their max_retries setting.
    - Optionally enable concurrent execution of eligible tasks.
    - Track overall workflow progress, providing status updates and completion detection.
    - Integrate with logging, event, and metric systems for observability.

Design & Methods to Implement:
    1. Scheduler class with:
        - __init__ accepting a DAG instance and optional concurrency settings.
        - run(): Main orchestration loop/scheduler logic.
        - _execute_task(task): Runs a task, updates state, handles errors/retries.
        - Optionally: concurrency helpers (threading/multiprocessing).
        - Progress reporting/logging integration.
    2. Internal attributes for:
        - DAG reference.
        - List or set of completed/failed tasks.
        - Task execution queue or pool.
        - Optional hooks/callbacks for events or metrics.

Usage:
    The Scheduler is the central engine module for executing workflows.
    It is invoked after a DAG is constructed, and manages the end-to-end execution flow,
    error/retry handling, and reporting until all tasks are completed or workflow fails.

Follow this design to implement robust scheduling and execution coordination for your workflow engine.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.task import TaskState
from core.dag import DAG
from core.executor import LocalExecutor, ThreadedExecutor, MultiprocessExecutor
from core.event import WorkflowEvent

class Scheduler:
    def __init__(self, dag: DAG, executor_type: str = "local",
                 max_workers: int = 1, events=None):
        """
        Initializes the Scheduler.

        Args:
            dag (DAG): The workflow DAG to execute.
            executor_type (str): "local", "thread", or "process".
            max_workers (int): Number of workers for concurrency.
            events (EventManager): Optional event manager for hooks.
        """
        self.dag = dag
        self.events = events
        self.completed_tasks = set()
        self.failed_tasks = set()
        self.running_tasks = set()
        self._status_lock = threading.Lock()

        if executor_type == "thread":
            self.executor = ThreadedExecutor(max_workers=max_workers)
        elif executor_type == "process":
            self.executor = MultiprocessExecutor(max_workers=max_workers)
        else:
            self.executor = LocalExecutor()

        self.executor_type = executor_type
        self.max_workers = max_workers

    def run(self):
        """
        Main scheduling and execution loop.
        Executes tasks in dependency-aware order until the workflow completes.
        """
        self.dag.validate()

        # Fire workflow started event
        if self.events:
            self.events.notify(WorkflowEvent.WORKFLOW_STARTED)

        print("=== Starting Workflow Execution ===\n")

        while True:
            # Find tasks ready to run
            ready_tasks = [
                t for t in self.dag.tasks.values()
                if t.name not in self.completed_tasks
                and t.name not in self.failed_tasks
                and t.name not in self.running_tasks
                and t.is_ready()
            ]

            # Deadlock prevention: mark unreachable tasks as FAILED
            for task in self.dag.tasks.values():
                if (
                    task.state == TaskState.PENDING
                    and task.name not in self.completed_tasks
                    and task.name not in self.failed_tasks
                    and hasattr(task, "is_unreachable")
                    and task.is_unreachable()
                ):
                    print(f"Task {task.name} is unreachable due to failed dependencies. Marking as FAILED.")
                    task.state = TaskState.FAILED
                    self.failed_tasks.add(task.name)

            if not ready_tasks:
                if self._all_finished():
                    break
                time.sleep(0.1)
                continue

            if self.executor_type == "local":
                for task in ready_tasks:
                    # Fire task started event
                    if self.events:
                        self.events.notify(WorkflowEvent.TASK_STARTED, task=task)

                    print(f"Scheduling task: {task.name}")
                    success = self.executor.execute(task)

                    with self._status_lock:
                        if success:
                            self.completed_tasks.add(task.name)
                            if self.events:
                                self.events.notify(WorkflowEvent.TASK_SUCCEEDED, task=task)
                        elif task.state == TaskState.FAILED:
                            self.failed_tasks.add(task.name)
                            if self.events:
                                self.events.notify(WorkflowEvent.TASK_FAILED, task=task, exception=task.exception)
                        elif task.retry_count > 0:
                            if self.events:
                                self.events.notify(WorkflowEvent.TASK_RETRIED, task=task)

            else:
                print(f"Scheduling tasks: {[task.name for task in ready_tasks]}")
                # Fire TASK_STARTED for each
                if self.events:
                    for task in ready_tasks:
                        self.events.notify(WorkflowEvent.TASK_STARTED, task=task)

                results = self.executor.execute_many(ready_tasks)
                for i, task in enumerate(ready_tasks):
                    with self._status_lock:
                        if results[i]:
                            self.completed_tasks.add(task.name)
                            if self.events:
                                self.events.notify(WorkflowEvent.TASK_SUCCEEDED, task=task)
                        elif task.state == TaskState.FAILED:
                            self.failed_tasks.add(task.name)
                            if self.events:
                                self.events.notify(WorkflowEvent.TASK_FAILED, task=task, exception=task.exception)
                        elif task.retry_count > 0:
                            if self.events:
                                self.events.notify(WorkflowEvent.TASK_RETRIED, task=task)

            self.report_status()
            time.sleep(0.1)

        print("\n=== Workflow Execution Complete ===")
        print(f"Successful tasks: {sorted(self.completed_tasks)}")
        print(f"Failed tasks: {sorted(self.failed_tasks)}")

        # Fire workflow completed event
        if self.events:
            self.events.notify(WorkflowEvent.WORKFLOW_COMPLETED)

        if self.executor_type in ("thread", "process"):
            self.executor.shutdown()

    def report_status(self):
        """
        Prints current status of all tasks in the workflow.
        """
        print("---- Current Workflow Status ----")
        for task in self.dag.tasks.values():
            print(f"Task {task.name}: {task.state.value} | Retries: {task.retry_count}")
        print("---------------------------------\n")

    def _all_finished(self):
        """
        Returns True if all tasks have completed (success or failed).
        """
        total = len(self.dag.tasks)
        finished = len(self.completed_tasks) + len(self.failed_tasks)
        return finished >= total
