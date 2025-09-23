"""
test_task.py

Purpose:
    Verifies all essential behaviors, state transitions, dependencies, result handling, and 
    retry logic of the Task class through unit tests. Ensures Tasks execute correctly under 
    both normal and failure conditions.
"""

import pytest
from core.task import Task, TaskState
from core.exceptions import InvalidTaskError

def test_task_creation():
    t = Task("task1")
    assert t.name == "task1"
    assert t.state == TaskState.PENDING
    assert t.dependencies == []
    assert t.max_retries == 0
    assert t.retry_count == 0

def test_task_add_dependency():
    t1 = Task("task1")
    t2 = Task("task2")
    t2.add_dependency(t1)
    assert t1 in t2.dependencies
    assert t2.dependencies[0].name == "task1"

def test_task_run_success():
    def sample_func():
        return 42

    t = Task("task_success", func=sample_func)
    result = t.run()
    assert result is True
    assert t.state == TaskState.SUCCESS
    assert t.result == 42

def test_task_run_failure_no_retry():
    def fail_func():
        raise ValueError("fail")

    t = Task("task_fail", func=fail_func)
    result = t.run()
    assert result is False
    assert t.state == TaskState.FAILED
    assert isinstance(t.exception, ValueError)

def test_task_run_failure_with_retry():
    retry_counter = {"count": 0}
    def fail_then_succeed():
        if retry_counter["count"] < 2:
            retry_counter["count"] += 1
            raise RuntimeError("fail")
        return "done"

    t = Task("task_retry", func=fail_then_succeed, max_retries=2)
    
    # First run
    result = t.run()
    assert result is True
    assert t.state == TaskState.SUCCESS
    assert t.result == "done"
    assert retry_counter["count"] == 2
    assert t.retry_count == 2

def test_task_run_max_retry_exceeded():
    def always_fail():
        raise RuntimeError("fail")

    t = Task("task_fail_retry", func=always_fail, max_retries=1)
    result = t.run()
    assert result is False
    assert t.state == TaskState.FAILED
    assert isinstance(t.exception, RuntimeError)
    assert t.retry_count == 1

def test_task_with_custom_exception():
    def raise_custom():
        raise InvalidTaskError("custom error")

    t = Task("task_custom_exception", func=raise_custom)
    result = t.run()
    assert result is False
    assert t.state == TaskState.FAILED
    assert isinstance(t.exception, InvalidTaskError)

def test_task_result_persistence_between_runs():
    run_count = {"count": 0}
    def counter_func():
        run_count["count"] += 1
        return run_count["count"]

    t = Task("task_counter", func=counter_func)
    result1 = t.run()
    assert result1 is True
    assert t.result == 1
    result2 = t.run()
    assert result2 is True
    assert t.result == 2  # Result updates on every run

def test_task_pending_state_with_retry():
    retry_counter = {"count": 0}
    def fail_once_then_succeed():
        if retry_counter["count"] == 0:
            retry_counter["count"] += 1
            raise RuntimeError("fail once")
        return "ok"

    t = Task("task_pending_retry", func=fail_once_then_succeed, max_retries=1)
    assert t.state == TaskState.PENDING
    t.run()
    assert t.state == TaskState.SUCCESS
    assert t.retry_count == 1