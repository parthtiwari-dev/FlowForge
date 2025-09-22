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
from core.task import Task, TaskState
from core.dag import DAG
from core.executor import LocalExecutor, ThreadedExecutor, MultiprocessExecutor

class Scheduler:
    def __init__(self, dag: DAG, executor_type: str = "local", max_workers: int = 1):
        """
        Initializes the Scheduler.

        Args:
            dag (DAG): The workflow DAG to execute.
            executor_type (str): Type of executor ("local", "thread", "process").
            max_workers (int): Maximum number of workers for concurrency.
        """
        self.dag = dag
        self.completed_tasks = set()
        self.failed_tasks = set()
        self.running_tasks = set()
        self._status_lock = threading.Lock()

        # Set up executor according to type
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
        print("=== Starting Workflow Execution ===\n")
        if self.executor_type == "thread":
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = {}
                while True:
                    # Find all ready tasks not yet scheduled
                    ready_tasks = [
                        t for t in self.dag.tasks.values()
                        if t.name not in self.completed_tasks
                        and t.name not in self.failed_tasks
                        and t.name not in self.running_tasks
                        and t.is_ready()
                    ]
                    for task in ready_tasks:
                        print(f"Scheduling task: {task.name}")
                        future = pool.submit(task.run)
                        futures[future] = task
                        self.running_tasks.add(task.name)

                    if not futures:
                        if self._all_finished():
                            break
                        time.sleep(0.1)
                        continue

                    done_future = next(as_completed(futures), None)
                    if done_future is not None:
                        task = futures.pop(done_future)
                        self.running_tasks.remove(task.name)
                        result = done_future.result()
                        with self._status_lock:
                            if result:
                                self.completed_tasks.add(task.name)
                            elif task.state == TaskState.FAILED:
                                self.failed_tasks.add(task.name)
                        self.report_status()
        else:
            # Original local/process logic
            while True:
                ready_tasks = self.dag.get_ready_tasks()
                if not ready_tasks:
                    if self._all_finished():
                        break
                    time.sleep(0.2)
                    continue

                if self.executor_type == "local":
                    for task in ready_tasks:
                        print(f"Scheduling task: {task.name}")
                        success = self.executor.execute(task)
                        if success:
                            self.completed_tasks.add(task.name)
                        elif task.state == TaskState.FAILED:
                            self.failed_tasks.add(task.name)
                else:
                    print(f"Scheduling tasks: {[task.name for task in ready_tasks]}")
                    results = self.executor.execute_many(ready_tasks)
                    for i, task in enumerate(ready_tasks):
                        with self._status_lock:
                            if results[i]:
                                self.completed_tasks.add(task.name)
                            elif task.state == TaskState.FAILED:
                                self.failed_tasks.add(task.name)
                self.report_status()
                time.sleep(0.1)

        print("\n=== Workflow Execution Complete ===")
        print(f"Successful tasks: {sorted(self.completed_tasks)}")
        print(f"Failed tasks: {sorted(self.failed_tasks)}")

        # Shutdown the executor pool if used
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
    # If you want to add concurrency (threading/multiprocessing), 
    # you would update run() to submit ready tasks to a ThreadPoolExecutor here.


# You can now instantiate Scheduler with your DAG and call scheduler.run()
