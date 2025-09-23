"""
test_scheduler.py

Purpose:
    Tests the Scheduler’s ability to coordinate workflow execution, including respecting
    dependencies, triggering retries, and reporting task and workflow status. Ensures correct
    sequencing, error handling, and completion detection in orchestrated runs.
"""

import pytest
from core.scheduler import Scheduler
from core.task import Task, TaskState
from core.dag import DAG
from core.executor import LocalExecutor
from core.event import EventManager, WorkflowEvent


# Helper to create a simple DAG
def create_sample_dag():
    t1 = Task("task1", func=lambda: "result1")
    t2 = Task("task2", func=lambda: "result2")
    t3 = Task("task3", func=lambda: "result3")

    t2.add_dependency(t1)
    t3.add_dependency(t2)

    dag = DAG()
    for t in [t1, t2, t3]:
        dag.add_task(t)
    return dag, [t1, t2, t3]


def test_scheduler_runs_tasks_in_order():
    dag, tasks = create_sample_dag()
    scheduler = Scheduler(dag, executor_type="local")

    executed = []

    # Wrap original task functions to track execution
    for t in tasks:
        orig_func = t.func
        t.func = lambda orig=orig_func, name=t.name: executed.append(name) or orig()

    scheduler.run()

    # Execution order must respect dependencies: task1 -> task2 -> task3
    assert executed == ["task1", "task2", "task3"]

    # All tasks should be marked SUCCESS
    for t in tasks:
        assert t.state == TaskState.SUCCESS


def test_scheduler_handles_retry():
    t1 = Task("task1", func=lambda: 1)
    # This task fails first 2 times, succeeds on 3rd
    retry_counter = {"count": 0}

    def fail_then_succeed():
        if retry_counter["count"] < 2:
            retry_counter["count"] += 1
            raise ValueError("fail")
        return "ok"

    t2 = Task("task2", func=fail_then_succeed, max_retries=2)

    t2.add_dependency(t1)

    dag = DAG()
    for t in [t1, t2]:
        dag.add_task(t)

    scheduler = Scheduler(dag, executor_type="local")
    scheduler.run()

    assert t1.state == TaskState.SUCCESS
    assert t2.state == TaskState.SUCCESS
    assert retry_counter["count"] == 2  # retried exactly twice


def test_scheduler_triggers_events():
    dag, tasks = create_sample_dag()
    events = EventManager()
    scheduler = Scheduler(dag, executor_type="local", events=events)


    EVENTS = [
        WorkflowEvent.TASK_STARTED,
        WorkflowEvent.TASK_SUCCEEDED,
        WorkflowEvent.TASK_FAILED,
        WorkflowEvent.TASK_RETRIED,
        WorkflowEvent.WORKFLOW_STARTED,
        WorkflowEvent.WORKFLOW_COMPLETED,
    ]

    fired = {ev: [] for ev in EVENTS}

    def make_recorder(ev):
        return lambda **kwargs: fired[ev].append(
            kwargs.get("task").name if "task" in kwargs else None
        )

    for ev in EVENTS:
        events.register(ev, make_recorder(ev))

    # Attach recorders to all events

    scheduler.run()

    # Workflow started and completed events
    assert fired[WorkflowEvent.WORKFLOW_STARTED] == [None]
    assert fired[WorkflowEvent.WORKFLOW_COMPLETED] == [None]

    # Task started and succeeded events for each task
    started_tasks = [name for name in fired[WorkflowEvent.TASK_STARTED] if name]
    succeeded_tasks = [name for name in fired[WorkflowEvent.TASK_SUCCEEDED] if name]

    assert set(started_tasks) == set(["task1", "task2", "task3"])
    assert set(succeeded_tasks) == set(["task1", "task2", "task3"])


def test_scheduler_handles_failed_task_no_retry():
    t1 = Task("task1", func=lambda: 1)
    t2 = Task("task2", func=lambda: 1 / 0)  # fails
    t2.add_dependency(t1)

    dag = DAG()
    dag.add_task(t1)
    dag.add_task(t2)

    scheduler = Scheduler(dag, executor_type="local")
    scheduler.run()

    assert t1.state == TaskState.SUCCESS
    assert t2.state == TaskState.FAILED


def test_scheduler_with_no_tasks():
    dag = DAG()
    scheduler = Scheduler(dag, executor_type="local")
    # Should run without errors
    scheduler.run()
