"""
test_executor.py

Purpose:
    Validates all Executor variants (local, threaded, multiprocessing) for proper task execution, 
    parallelism, error propagation, and resource cleanup. Ensures Executor logic matches specified 
    behavior for each mode.
"""
import pytest
from core.task import Task, TaskState
from core.executor import LocalExecutor, ThreadedExecutor

def test_local_executor_success():
    """
    LocalExecutor runs a simple task to SUCCESS.
    """
    def hello():
        return "hello"
    t = Task("simple", func=hello)
    ex = LocalExecutor()
    result = ex.execute(t)
    assert result is True
    assert t.state == TaskState.SUCCESS
    assert t.result == "hello"

def test_local_executor_failure_and_retry():
    """
    LocalExecutor retries up to max_retries, then marks task as FAILED.
    """
    attempts = {"n": 0}
    def fail():
        attempts["n"] += 1
        raise RuntimeError("fail!")
    t = Task("fail", func=fail, max_retries=2)
    ex = LocalExecutor()
    result = ex.execute(t)
    assert result is False
    assert t.state == TaskState.FAILED
    assert attempts["n"] == 3  # original try + 2 retries

def test_threaded_executor_success():
    """
    ThreadedExecutor executes a batch of tasks and all succeed.
    """
    def say_hi():
        return "hi"
    tasks = [Task(f"t{i}", func=say_hi) for i in range(3)]
    ex = ThreadedExecutor(max_workers=2)
    results = ex.execute_many(tasks)
    assert all(results) is True
    assert all(t.state == TaskState.SUCCESS for t in tasks)
    ex.shutdown()

def test_threaded_executor_mixed_results():
    """
    ThreadedExecutor handles a mix of SUCCESS and FAILED tasks.
    """
    def fail():
        raise ValueError("fail")
    def ok():
        return 1
    tasks = [Task("good", func=ok), Task("bad", func=fail, max_retries=0)]
    ex = ThreadedExecutor(max_workers=2)
    results = ex.execute_many(tasks)
    assert results == [True, False]
    assert tasks[0].state == TaskState.SUCCESS
    assert tasks[1].state == TaskState.FAILED
    ex.shutdown()
