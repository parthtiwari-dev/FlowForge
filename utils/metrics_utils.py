"""
metrics_utils.py

Purpose:
    Provides utilities to collect, aggregate, and report runtime metrics from workflow execution.
    Tracks task success, failure, retry counts, execution durations, and overall workflow stats.
    Ideal for monitoring, optimization, and reporting within the orchestration engine.

Key Responsibilities:
    - Record key performance indicators (KPIs) for each task (start/end time, duration, outcome).
    - Maintain counters for total successes, failures, retries, and completed workflows.
    - Provide methods for real-time metric reporting and end-of-run summaries.
    - Enable metric hooks as event listeners for automated data collection.
    - Support extensible design for custom/user-defined metric tracking.

Usage:
    Import and call metrics functions directly, or register metric collectors as listeners in the event system.
    Use summaries for post-mortem reporting, dashboarding, or runtime alerts.
"""

import time
from collections import defaultdict


class MetricsManager:
    """
    Collects and reports metrics for workflow tasks and overall execution.
    Can be used as an EventManager listener.
    """

    def __init__(self):
        # Track task-level metrics
        self.task_metrics = defaultdict(
            lambda: {
                "start_time": None,
                "end_time": None,
                "duration": None,
                "status": None,
                "retries": 0,
            }
        )
        # Track workflow-level counters
        self.workflow_metrics = {
            "tasks_success": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "workflow_start_time": None,
            "workflow_end_time": None,
            "workflow_duration": None,
        }

    # -------------------------
    # Task Event Handlers
    # -------------------------
    def task_started(self, task, **kwargs):
        self.task_metrics[task.name]["start_time"] = time.time()
        self.task_metrics[task.name]["status"] = "RUNNING"

    def task_succeeded(self, task, **kwargs):
        end = time.time()
        start = self.task_metrics[task.name]["start_time"] or end
        self.task_metrics[task.name].update(
            {
                "end_time": end,
                "duration": end - start,
                "status": "SUCCESS",
                "retries": task.retry_count,
            }
        )
        self.workflow_metrics["tasks_success"] += 1
        if task.retry_count > 0:
            self.workflow_metrics["tasks_retried"] += task.retry_count

    def task_failed(self, task, exception=None, **kwargs):
        end = time.time()
        start = self.task_metrics[task.name]["start_time"] or end
        self.task_metrics[task.name].update(
            {
                "end_time": end,
                "duration": end - start,
                "status": "FAILED",
                "retries": task.retry_count,
            }
        )
        self.workflow_metrics["tasks_failed"] += 1
        if task.retry_count > 0:
            self.workflow_metrics["tasks_retried"] += task.retry_count

    def task_retried(self, task, **kwargs):
        self.task_metrics[task.name]["retries"] = task.retry_count
        self.workflow_metrics["tasks_retried"] += 1

    # -------------------------
    # Workflow Event Handlers
    # -------------------------
    def workflow_started(self, **kwargs):
        self.workflow_metrics["workflow_start_time"] = time.time()

    def workflow_completed(self, **kwargs):
        end = time.time()
        start = self.workflow_metrics.get("workflow_start_time") or end
        self.workflow_metrics.update(
            {"workflow_end_time": end, "workflow_duration": end - start}
        )

    # -------------------------
    # Reporting
    # -------------------------
    def print_task_metrics(self):
        print("\n=== Task Metrics ===")
        for task_name, metrics in self.task_metrics.items():
            duration = metrics["duration"]
            duration_str = f"{duration:.3f}s" if duration is not None else "N/A"
            print(
                f"{task_name}: Status={metrics['status']}, "
                f"Duration={duration_str}, "
                f"Retries={metrics['retries']}"
            )
        print("====================\n")

    def print_workflow_metrics(self):
        print("\n=== Workflow Metrics ===")
        duration = self.workflow_metrics["workflow_duration"]
        duration_str = f"{duration:.3f}s" if duration is not None else "N/A"
        print(f"Workflow Duration: {duration_str}")
        print(f"Tasks Success: {self.workflow_metrics['tasks_success']}")
        print(f"Tasks Failed: {self.workflow_metrics['tasks_failed']}")
        print(f"Tasks Retried: {self.workflow_metrics['tasks_retried']}")
        print("========================\n")
