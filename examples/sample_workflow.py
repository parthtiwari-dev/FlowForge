# sample_workflow.py

from core.task import Task, TaskState
from core.dag import DAG
from core.scheduler import Scheduler
from core.executor import LocalExecutor, ThreadedExecutor
from core.event import EventManager, WorkflowEvent
from utils.logging_utils import log_task_started, log_task_succeeded, log_task_failed, log_task_retried, log_workflow_started, log_workflow_completed
from utils.metrics_utils import MetricsManager

# ----------------------------
# 1. Set up EventManager
# ----------------------------
events = EventManager()

# Register logging functions
events.register(WorkflowEvent.TASK_STARTED, log_task_started)
events.register(WorkflowEvent.TASK_SUCCEEDED, log_task_succeeded)
events.register(WorkflowEvent.TASK_FAILED, log_task_failed)
events.register(WorkflowEvent.TASK_RETRIED, log_task_retried)
events.register(WorkflowEvent.WORKFLOW_STARTED, log_workflow_started)
events.register(WorkflowEvent.WORKFLOW_COMPLETED, log_workflow_completed)

# Register metrics manager
metrics = MetricsManager()
events.register(WorkflowEvent.TASK_STARTED, metrics.task_started)
events.register(WorkflowEvent.TASK_SUCCEEDED, metrics.task_succeeded)
events.register(WorkflowEvent.TASK_FAILED, metrics.task_failed)
events.register(WorkflowEvent.TASK_RETRIED, metrics.task_retried)
events.register(WorkflowEvent.WORKFLOW_STARTED, metrics.workflow_started)
events.register(WorkflowEvent.WORKFLOW_COMPLETED, metrics.workflow_completed)

# ----------------------------
# 2. Define Task Logic
# ----------------------------
def extract():
    print("Extracting data...")
    return "raw_data"

def transform():
    print("Transforming data...")
    if transform.retry_count == 0:
        transform.retry_count += 1
        raise ValueError("Transform failed first time!")
    return "clean_data"
transform.retry_count = 0

def load():
    print("Loading data...")
    return "loaded"

def fail_task():
    print("This task always fails!")
    raise RuntimeError("Intentional failure")

# ----------------------------
# 3. Create Tasks & DAG
# ----------------------------
t1 = Task("extract", func=extract)
t2 = Task("transform", func=transform, max_retries=1)
t3 = Task("load", func=load)
t4 = Task("fail_task", func=fail_task, max_retries=2)

# Set dependencies
t2.add_dependency(t1)
t3.add_dependency(t2)
t4.add_dependency(t1)

# Build DAG
dag = DAG()
dag.add_task(t1)
dag.add_task(t2)
dag.add_task(t3)
dag.add_task(t4)

print("DAG Structure:")
dag.print_structure()

# ----------------------------
# 4. Fire Workflow Started Event
# ----------------------------
events.notify(WorkflowEvent.WORKFLOW_STARTED)

# ----------------------------
# 5. Create Scheduler
# ----------------------------
scheduler = Scheduler(dag, executor_type="thread", max_workers=2)

# ----------------------------
# 6. Wrap Executor to Fire Events
# ----------------------------
def wrap_task_execution(task):
    events.notify(WorkflowEvent.TASK_STARTED, task=task)
    success = task.run()
    if success:
        events.notify(WorkflowEvent.TASK_SUCCEEDED, task=task)
    elif task.state == TaskState.FAILED:
        events.notify(WorkflowEvent.TASK_FAILED, task=task, exception=task.exception)
    elif task.state == TaskState.PENDING and task.retry_count > 0:
        events.notify(WorkflowEvent.TASK_RETRIED, task=task)
    return success

# Wrap LocalExecutor
if isinstance(scheduler.executor, LocalExecutor):
    scheduler.executor.execute = wrap_task_execution

# Wrap ThreadedExecutor
elif isinstance(scheduler.executor, ThreadedExecutor):
    original_execute_many = scheduler.executor.execute_many
    def wrapped_execute_many(tasks):
        results = []
        for task in tasks:
            events.notify(WorkflowEvent.TASK_STARTED, task=task)
        results = original_execute_many(tasks)
        for i, task in enumerate(tasks):
            if results[i]:
                events.notify(WorkflowEvent.TASK_SUCCEEDED, task=task)
            elif task.state == TaskState.FAILED:
                events.notify(WorkflowEvent.TASK_FAILED, task=task, exception=task.exception)
            elif task.state == TaskState.PENDING and task.retry_count > 0:
                events.notify(WorkflowEvent.TASK_RETRIED, task=task)
        return results
    scheduler.executor.execute_many = wrapped_execute_many

# ----------------------------
# 7. Run Workflow
# ----------------------------
scheduler.run()

# ----------------------------
# 8. Fire Workflow Completed Event
# ----------------------------
events.notify(WorkflowEvent.WORKFLOW_COMPLETED)

# ----------------------------
# 9. Print Metrics
# ----------------------------
metrics.print_task_metrics()
metrics.print_workflow_metrics()
