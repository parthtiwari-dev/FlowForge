"""
executor.py

Purpose:
    Provides executor classes for running workflow tasks. Executors are responsible for 
    abstracting how tasks are executed—either sequentially, concurrently (with threads or processes), 
    or, in advanced versions, on remote/external systems.

Key Responsibilities:
    - Define a standard interface (BaseExecutor) for executing tasks.
    - Implement various executor types:
        - LocalExecutor: Runs tasks in the main process, sequentially.
        - ThreadedExecutor: Executes multiple tasks in parallel using threads.
        - MultiprocessExecutor: Runs tasks concurrently in separate processes for isolation/scalability.
        - (Optional/stretch) RemoteExecutor: Simulate or implement remote/distributed execution.
    - Manage task execution, result capture, and error propagation.
    - Integrate with the Scheduler to coordinate task dispatch using selected executor type.
    - Optionally handle resource allocation and cleanup for each execution context.

Design & Methods to Implement:
    1. BaseExecutor class with an abstract execute(task) method.
    2. LocalExecutor subclass for simple in-process execution.
    3. ThreadedExecutor/MultiprocessExecutor subclasses for parallelism, using Python's concurrent.futures.
    4. Optionally: methods for initialization/shutdown, status monitoring, and resource management.

Usage:
    The Scheduler will instantiate the appropriate Executor and delegate all task runs to it.
    Executors can be swapped to change execution mode (sequential or concurrent), 
    supporting scalability, extensibility, and testing.

Follow this design to implement a flexible, robust task execution layer for your workflow engine.
"""
from core.task import Task
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

class BaseExecutor:
    """
    Base class for all executors. Subclasses must implement the execute(task) method.
    """
    def execute(self, task: Task):
        raise NotImplementedError("Executors must implement the execute(task) method.")


class LocalExecutor(BaseExecutor):
    """
    Executes tasks sequentially in the current process.
    """
    def execute(self, task: Task):
        return task.run()


class ThreadedExecutor(BaseExecutor):
    """
    Executes multiple tasks in parallel using threading.
    """
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.pool = ThreadPoolExecutor(max_workers=self.max_workers)

    def execute_many(self, tasks):
        """
        Accepts a list of tasks and runs them in parallel threads.
        Returns a list of results.
        """
        futures = [self.pool.submit(task.run) for task in tasks]
        results = []
        for future in as_completed(futures):
            results.append(future.result())
        return results

    def shutdown(self):
        self.pool.shutdown()


class MultiprocessExecutor(BaseExecutor):
    """
    Executes multiple tasks in parallel using processes.
    """
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.pool = ProcessPoolExecutor(max_workers=self.max_workers)

    def execute_many(self, tasks):
        """
        Accepts a list of tasks and runs them in parallel processes.
        Returns a list of results.
        """
        futures = [self.pool.submit(task.run) for task in tasks]
        results = []
        for future in as_completed(futures):
            results.append(future.result())
        return results

    def shutdown(self):
        self.pool.shutdown()


# Example usage (usually called by Scheduler):
# 
# local_executor = LocalExecutor()
# threaded_executor = ThreadedExecutor(max_workers=4)
# multiprocess_executor = MultiprocessExecutor(max_workers=4)
#
# For parallel execution:
# threaded_executor.execute_many([task1, task2])
# multiprocess_executor.execute_many([task3, task4])
# threaded_executor.shutdown()
# multiprocess_executor.shutdown()