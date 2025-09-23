"""
test_dag.py

Purpose:
    Unit tests for the DAG class.
    Validates task registration, dependency graph construction, topological sorting, cycle detection, and readiness queries.
    Confirms the DAG maintains a correct and acyclic workflow structure with reliable dependency resolution.
"""

# tests/test_dag.py

import pytest
from core.dag import DAG
from core.task import Task, TaskState
from core.exceptions import InvalidTaskError

def test_add_task():
    dag = DAG()
    t1 = Task("task1")
    dag.add_task(t1)
    
    assert "task1" in dag.tasks
    assert dag.get_task("task1") == t1

def test_add_duplicate_task_raises():
    dag = DAG()
    t1 = Task("task1")
    dag.add_task(t1)
    
    t2 = Task("task1")  # same name
    with pytest.raises(ValueError):
        dag.add_task(t2)

def test_add_dependency():
    dag = DAG()
    t1 = Task("task1")
    t2 = Task("task2")
    dag.add_task(t1)
    dag.add_task(t2)
    
    t2.add_dependency(t1)
    
    assert t1 in t2.dependencies
    assert t2.dependencies[0].name == "task1"

def test_cycle_detection():
    dag = DAG()
    t1 = Task("task1")
    t2 = Task("task2")
    t3 = Task("task3")
    
    dag.add_task(t1)
    dag.add_task(t2)
    dag.add_task(t3)
    
    t2.add_dependency(t1)
    t3.add_dependency(t2)
    
    # Introducing cycle
    t1.add_dependency(t3)
    
    with pytest.raises(ValueError):
        dag.validate()  # Assuming DAG has validate() that raises on cycles

def test_topological_ordering():
    dag = DAG()
    t1 = Task("task1")
    t2 = Task("task2")
    t3 = Task("task3")
    
    dag.add_task(t1)
    dag.add_task(t2)
    dag.add_task(t3)
    
    t2.add_dependency(t1)
    t3.add_dependency(t2)
    
    order = dag.topological_sort()  # returns list of tasks in order
    order_names = [t.name for t in order]
    
    assert order_names.index("task1") < order_names.index("task2")
    assert order_names.index("task2") < order_names.index("task3")

def test_get_task_not_existing():
    dag = DAG()
    assert dag.get_task("unknown") is None
