# Workflow Orchestration Engine

## 🚀 Overview

This Workflow Engine is a Python framework for building, running, and monitoring complex workflows. It lets you define tasks and their dependencies, manage execution (sequential or parallel), track metrics, log events, and persist state for recovery—all with minimal code.

---

## 🗂️ Project Structure

```
FlowForge/
│
├── core/        # Core engine: tasks, DAG, scheduler, executor, events, context
├── dsl/         # Domain-specific language for easy workflow definition
├── utils/       # Logging, metrics, retry utilities
├── state/       # Persistence (autosave, resume)
├── examples/    # Example workflows (classic & DSL)
├── tests/       # Unit tests
├── README.md    # This file
└── requirements.txt
```

---

## ⚡ Quick Start

### 1. **Clone the Repository**
```sh
git clone <your-repo-url>
cd FlowForge
```

### 2. **Install Dependencies**
```sh
pip install -r requirements.txt
```

### 3. **Run an Example Workflow**

#### **Classic (Manual) Example**
```sh
python -m examples.sample_workflow
```

#### **DSL (Recommended) Example**
```sh
python -m examples.etl_workflow
```

---

## 🛠️ Defining Your Own Workflow

### **A. Using the DSL (Recommended)**

Create a new file in `examples/` (e.g., `my_workflow.py`):

```python
from dsl.workflow_dsl import workflow, task

with workflow("My Workflow") as wf:

    @task
    def step1():
        print("Step 1 running")
        return "result1"

    @task
    def step2():
        print("Step 2 running")
        return "result2"

    # Set dependencies
    wf.dag.get_task("step2").add_dependency(wf.dag.get_task("step1"))

    # Run the workflow
    wf.run()
```

Run it:
```sh
python -m examples.my_workflow
```

### **B. Using the Classic API**

See `examples/sample_workflow.py` for a full example using manual task, DAG, and scheduler setup.

---

## 📋 Features

- **Task Abstraction:** Define tasks as Python functions or classes.
- **DAG Management:** Express dependencies between tasks.
- **Flexible Execution:** Run tasks sequentially, with threads, or with processes.
- **Event System:** Hook into task/workflow events for logging, metrics, or custom actions.
- **Logging:** All events are logged to `logs/workflow.log`.
- **Metrics:** Track task durations, retries, and workflow stats.
- **Persistence:** Autosave and resume workflow state (see `state/`).
- **Retry Logic:** Automatic retries for failed tasks.
- **Context Management:** Safely manage resources (files, pools, etc.) in tasks.

---

## 📦 State Persistence & Recovery

- **Autosave:** Workflow state is saved automatically on task success and workflow completion.
- **Resume:** Workflows can be resumed from the last checkpoint using the persistence manager.

---

## 📝 Customizing & Extending

- **Add new tasks:** Just define more `@task` functions in your workflow script.
- **Change execution mode:** Use `executor_type="thread"` or `"process"` in the DSL or scheduler.
- **Add logging/metrics:** Register your own event listeners in the workflow script or extend `utils/`.
- **Integrate with other systems:** Use context managers for DB/API connections in your tasks.

---

## 🧪 Running Tests

```sh
python -m unittest discover tests
```

---

## ❓ FAQ

**Q: Where do I see logs?**  
A: All logs are in `logs/workflow.log` and printed to the console.

**Q: How do I add dependencies?**  
A: Use `wf.dag.get_task("task2").add_dependency(wf.dag.get_task("task1"))` in the DSL context.

**Q: How do I resume a workflow?**  
A: The engine autosaves state. Use the same workflow script and it will resume from the last checkpoint.

**Q: Can I run tasks in parallel?**  
A: Yes! Use `executor_type="thread"` or `"process"` in the DSL or scheduler.

---

## 🤝 Contributing

Contributions are welcome!  
- Fork the repo, create a branch, and submit a pull request.
- For bugs or feature requests, open an issue.

---

## 📄 License

MIT License. See `LICENSE` for details.

---

**Happy orchestrating! 🚦**