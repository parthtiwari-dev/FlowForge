# FlowForge - Workflow Orchestration Engine

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/your-username/flowforge)

**FlowForge** is a powerful, lightweight Python workflow orchestration engine that allows you to build, manage, and execute complex data pipelines and task workflows with ease. It provides a robust foundation for creating directed acyclic graphs (DAGs) of tasks with dependency management, retry logic, multiple execution modes, and comprehensive monitoring capabilities.

## 🎯 What Does FlowForge Do?

FlowForge helps you:
- **Define workflows** as a series of interconnected tasks with dependencies
- **Execute tasks** in the correct order based on their dependencies
- **Handle failures** with configurable retry logic and error handling
- **Monitor execution** with comprehensive logging and metrics
- **Scale execution** with multiple executor types (local, threaded, multiprocess)
- **Persist state** for checkpoint recovery and workflow resumption
- **Manage resources** with context managers and cleanup utilities

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Tasks       │    │      DAG        │    │   Scheduler     │
│                 │───▶│                 │───▶│                 │
│ • Extract       │    │ • Dependencies  │    │ • Execution     │
│ • Transform     │    │ • Validation    │    │ • Concurrency   │
│ • Load          │    │ • Traversal     │    │ • Retry Logic   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Executors    │    │     Events      │    │   Persistence   │
│                 │    │                 │    │                 │
│ • Local         │◀───┤ • Logging       │    │ • Checkpoints   │
│ • Threaded      │    │ • Metrics       │    │ • State Mgmt    │
│ • Process-based │    │ • Notifications │    │ • Recovery      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
FlowForge/
├── core/                    # Core engine components
│   ├── task.py             # Task abstraction and execution
│   ├── dag.py              # Directed Acyclic Graph management
│   ├── scheduler.py        # Task scheduling and coordination
│   ├── executor.py         # Multiple execution backends
│   ├── event.py            # Event system for monitoring
│   ├── context.py          # Resource management
│   └── exceptions.py       # Custom exception classes
├── dsl/                     # Domain-Specific Language
│   └── workflow_dsl.py     # Declarative workflow definition
├── utils/                   # Utility modules
│   ├── logging_utils.py    # Logging and output management
│   ├── retry_utils.py      # Retry and backoff strategies
│   └── metrics_utils.py    # Performance monitoring
├── state/                   # State management
│   └── persistence.py      # Checkpoint and recovery
├── examples/               # Sample workflows
│   ├── sample_workflow.py  # Comprehensive demo
│   ├── etl_workflow.py     # Data pipeline example
│   └── ml_workflow.py      # ML pipeline example
├── tests/                  # Unit tests
│   ├── test_task.py
│   ├── test_dag.py
│   ├── test_scheduler.py
│   └── test_executor.py
├── cli.py                  # Command-line interface
├── requirements.txt        # Dependencies
├── setup.py               # Package configuration
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Environment Setup

First, create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Your First Workflow

```bash
# Run the sample workflow
python cli.py run examples/sample_workflow.py

# Or run with threading
python cli.py run examples/sample_workflow.py --executor thread --workers 4
```

## 💻 CLI Usage

FlowForge provides a comprehensive command-line interface for managing workflows:

### Basic Commands

```bash
# List all tasks and dependencies
python cli.py list-tasks examples/sample_workflow.py

# Validate workflow structure
python cli.py validate examples/sample_workflow.py

# Run workflow (default: local executor)
python cli.py run examples/sample_workflow.py

# Run with specific executor and workers
python cli.py run examples/sample_workflow.py --executor thread --workers 4

# Dry run (show structure without execution)
python cli.py run examples/sample_workflow.py --dry-run

# Run with verbose logging
python cli.py run examples/sample_workflow.py --verbose

# Run with minimal output
python cli.py run examples/sample_workflow.py --quiet
```

### Checkpoint and Recovery

```bash
# Run with checkpointing
python cli.py run examples/sample_workflow.py --checkpoint my_state.json

# Check workflow status from checkpoint
python cli.py status --checkpoint my_state.json
```

### Available Executors

| Executor | Description | Use Case |
|----------|-------------|----------|
| `local` | Sequential execution | Simple workflows, debugging |
| `thread` | Multi-threaded execution | I/O bound tasks |
| `process` | Multi-process execution | CPU intensive tasks |

## 🔧 Creating Your Own Workflows

### Method 1: Direct Python API

```python
from core.task import Task
from core.dag import DAG
from core.scheduler import Scheduler

# Define task functions
def extract():
    print("Extracting data...")
    return "raw_data"

def transform():
    print("Transforming data...")
    return "clean_data"

def load():
    print("Loading data...")
    return "loaded"

# Create tasks
t1 = Task("extract", func=extract)
t2 = Task("transform", func=transform, max_retries=2)
t3 = Task("load", func=load)

# Set dependencies
t2.add_dependency(t1)  # transform depends on extract
t3.add_dependency(t2)  # load depends on transform

# Create DAG and add tasks
dag = DAG()
for task in [t1, t2, t3]:
    dag.add_task(task)

# Run workflow
scheduler = Scheduler(dag, executor_type="local")
scheduler.run()
```

### Method 2: Using DSL (Domain-Specific Language)

```python
from dsl.workflow_dsl import workflow, task

with workflow("My_ETL_Pipeline") as wf:
    @task
    def extract():
        print("Extracting data...")
        return "raw_data"

    @task(max_retries=2)
    def transform():
        print("Transforming data...")
        return "clean_data"

    @task
    def load():
        print("Loading data...")
        return "loaded"

    # Set dependencies
    wf.dag.get_task("transform").add_dependency(wf.dag.get_task("extract"))
    wf.dag.get_task("load").add_dependency(wf.dag.get_task("transform"))

    # Run the workflow
    wf.run()
```

## 🎛️ Advanced Features

### Event Management and Logging

```python
from core.event import EventManager, WorkflowEvent
from utils.logging_utils import log_task_started, log_task_succeeded

# Set up event management
events = EventManager()
events.register(WorkflowEvent.TASK_STARTED, log_task_started)
events.register(WorkflowEvent.TASK_SUCCEEDED, log_task_succeeded)

# Use with scheduler
scheduler = Scheduler(dag, events=events)
```

### Metrics and Monitoring

```python
from utils.metrics_utils import MetricsManager

metrics = MetricsManager()
# Register with events for automatic collection
events.register(WorkflowEvent.TASK_STARTED, metrics.task_started)
events.register(WorkflowEvent.TASK_SUCCEEDED, metrics.task_succeeded)

# Print metrics after execution
metrics.print_task_metrics()
metrics.print_workflow_metrics()
```

### Context Management

```python
from core.context import with_context, file_context

@with_context(lambda: file_context("output.txt", "w"))
def write_results(file_handle):
    file_handle.write("Results here")
    return "written"

task = Task("write_task", func=write_results)
```

### State Persistence

```python
from state.persistence import PersistenceManager

# Set up persistence
pm = PersistenceManager("workflow_state.json")

# Resume from checkpoint if available
pm.resume(dag)

# Attach autosave to events
pm.attach_to_events(events)
```

## 📊 Task Configuration Options

### Task Parameters

```python
task = Task(
    name="my_task",           # Unique task identifier
    func=my_function,         # Function to execute
    max_retries=3,           # Number of retry attempts
    timeout=60,              # Task timeout in seconds
    depends_on=[]            # List of dependency tasks
)
```

### Task States

| State | Description |
|-------|-------------|
| `PENDING` | Task is waiting to be executed |
| `RUNNING` | Task is currently executing |
| `SUCCESS` | Task completed successfully |
| `FAILED` | Task failed after all retries |

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_task.py -v

# Run with coverage
python -m pytest tests/ --cov=core --cov-report=html
```

### Test Structure

- `test_task.py` - Task creation, execution, and state management
- `test_dag.py` - DAG construction, validation, and traversal
- `test_scheduler.py` - Workflow coordination and execution order
- `test_executor.py` - Different execution backends

## 📖 Example Workflows

### 1. Data Pipeline (ETL)

```python
# examples/etl_workflow.py - Simple ETL pipeline
python cli.py run examples/etl_workflow.py
```

### 2. Machine Learning Pipeline

```python
# examples/ml_workflow.py - ML training pipeline
python cli.py run examples/ml_workflow.py --executor process --workers 2
```

### 3. Complex Sample Workflow

```python
# examples/sample_workflow.py - Comprehensive demo with all features
python cli.py run examples/sample_workflow.py --verbose
```

## 🔍 Debugging and Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're in the project root and virtual environment is activated
2. **File Not Found**: Use correct relative paths (e.g., `examples/sample_workflow.py`)
3. **Circular Dependencies**: Use `python cli.py validate` to check for cycles
4. **Task Failures**: Check logs and increase retry counts if needed

### Debug Mode

```bash
# Enable verbose logging
python cli.py run examples/sample_workflow.py --verbose

# Dry run to check structure
python cli.py run examples/sample_workflow.py --dry-run

# Validate before running
python cli.py validate examples/sample_workflow.py
```

## 🎨 Customization

### Custom Executors

Create your own executor by extending `BaseExecutor`:

```python
from core.executor import BaseExecutor

class CustomExecutor(BaseExecutor):
    def execute(self, task):
        # Your custom execution logic
        return task.run()
```

### Custom Event Handlers

```python
def my_custom_handler(task=None, **kwargs):
    print(f"Custom handling for task: {task.name}")

events.register(WorkflowEvent.TASK_STARTED, my_custom_handler)
```

### Custom Retry Strategies

```python
from utils.retry_utils import retry_task

@retry_task(max_retries=3, backoff_factor=2.0)
def unreliable_function():
    # Function that might fail
    pass
```

## 📈 Performance Tips

1. **Choose the Right Executor**:
   - Use `local` for simple debugging
   - Use `thread` for I/O-bound tasks
   - Use `process` for CPU-intensive tasks

2. **Optimize Task Dependencies**:
   - Minimize unnecessary dependencies
   - Parallelize independent tasks
   - Use `--dry-run` to visualize execution graph

3. **Configure Retries Appropriately**:
   - Set `max_retries` based on task reliability
   - Use exponential backoff for network operations

4. **Use Checkpointing for Long Workflows**:
   - Enable persistence for workflows > 30 minutes
   - Resume failed workflows from last checkpoint

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `python -m pytest tests/`
5. Submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/flowforge.git
cd flowforge

# Create development environment
python -m venv dev-env
source dev-env/bin/activate  # or dev-env\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
python -m pytest tests/ -v
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: This README contains comprehensive usage information
- **Issues**: Report bugs or request features via GitHub Issues
- **Examples**: Check the `examples/` directory for sample workflows
- **Tests**: Review `tests/` directory for usage patterns

## 🎯 Roadmap

- [ ] Web-based dashboard for workflow monitoring
- [ ] Additional executor types (Docker, Kubernetes)
- [ ] Workflow templates and marketplace
- [ ] Integration with external services (AWS, GCP)
- [ ] Advanced scheduling (cron-like, triggers)
- [ ] Workflow versioning and rollback capabilities

---

**Happy Orchestrating! 🎼**

For more information, examples, or support, please refer to the comprehensive examples in the `examples/` directory or run:

```bash
python cli.py --help
```