"""
dag.py

Purpose:
    Defines the Directed Acyclic Graph (DAG) abstraction for modeling workflow structures.
    The DAG manages Task objects, their relationships, and determines valid execution order
    according to dependencies. It is the backbone for constructing, validating, and traversing
    workflow task graphs for scheduling and execution.

Key Responsibilities:
    - Register and store Task instances as nodes in the workflow graph.
    - Track and manage directed edges representing dependencies between tasks.
    - Prevent dependency cycles (guarantee that the graph remains acyclic).
    - Provide methods to retrieve tasks with all dependencies satisfied (ready to run).
    - Support traversal and topological sorting to establish a valid order of execution.
    - Validate the integrity of the workflow (no missing dependencies, no cycles).
    - Enable visualization or introspection of the workflow DAG structure.
"""

from typing import Dict, List, Set, Optional
from core.task import Task, TaskState

class DAG:
    def __init__(self):
        """
        Initializes the DAG with an empty set of tasks.
        """
        self.tasks: Dict[str, Task] = {}

    def add_task(self, task: Task):
        """
        Adds a Task to the DAG.
        """
        if task.name in self.tasks:
            raise ValueError(f"Task with name '{task.name}' already exists in DAG.")
        self.tasks[task.name] = task

    def get_task(self, name: str) -> Optional[Task]:
        """
        Retrieve a task from the DAG by name.
        """
        return self.tasks.get(name)

    def validate(self):
        """
        Validates the DAG for cycles and missing dependencies.
        Raises an exception if invalid.
        """
        # Check for missing dependencies
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep.name not in self.tasks:
                    raise ValueError(f"Task '{task.name}' depends on missing task '{dep.name}'.")

        # Check for cycles
        if self._has_cycle():
            raise ValueError("DAG contains a cycle; dependency graph must be acyclic.")

    def _has_cycle(self) -> bool:
        """
        Internal method to detect cycles in the DAG using DFS.
        Returns True if a cycle is found, else False.
        """
        visited = set()
        visiting = set()

        def dfs(task: Task):
            if task.name in visiting:
                return True  # cycle detected
            if task.name in visited:
                return False
            visiting.add(task.name)
            for dep in task.dependencies:
                if dfs(dep):
                    return True
            visiting.remove(task.name)
            visited.add(task.name)
            return False

        for task in self.tasks.values():
            if dfs(task):
                return True
        return False

    def topological_sort(self) -> List[Task]:
        """
        Returns a list of tasks in a valid topological order.
        Raises ValueError if the DAG contains cycles.
        """
        self.validate()
        visited = set()
        order = []

        def dfs(task: Task):
            if task.name in visited:
                return
            for dep in task.dependencies:
                dfs(dep)
            visited.add(task.name)
            order.append(task)

        for task in self.tasks.values():
            dfs(task)

        # Remove duplicates while preserving order (DFS may append some tasks multiple times)
        seen = set()
        ordered_unique = []
        for t in reversed(order):
            if t.name not in seen:
                ordered_unique.append(t)
                seen.add(t.name)
        return list(reversed(ordered_unique))

    def get_ready_tasks(self) -> List[Task]:
        """
        Returns list of tasks ready to run (PENDING and all dependencies are SUCCESS).
        """
        ready = [
            task
            for task in self.tasks.values()
            if task.state == TaskState.PENDING and task.is_ready()
        ]
        return ready

    def print_structure(self):
        """
        Prints a simple representation of the DAG for debugging/inspection.
        """
        for task in self.tasks.values():
            dep_names = [dep.name for dep in task.dependencies]
            print(f"Task: {task.name}, Depends On: {dep_names}")

    def visualize(self):
        """
        OPTIONAL: If you want to visualize as text or export to Graphviz/etc.
        """
        try:
            import graphviz
        except ImportError:
            print("Graphviz is not installed, cannot visualize.")
            return
        dot = graphviz.Digraph()
        for task in self.tasks.values():
            dot.node(task.name)
            for dep in task.dependencies:
                dot.edge(dep.name, task.name)
        return dot
