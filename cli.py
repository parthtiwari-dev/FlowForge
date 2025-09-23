#!/usr/bin/env python3
"""
cli.py

Purpose:
    Command-line entry point for the workflow orchestration engine.
    Allows users to define, manage, and execute workflows and tasks directly from the terminal.

Key Responsibilities:
    - Parse command-line arguments for running, listing, validating, or inspecting workflows.
    - Provide commands to execute a workflow definition file (Python, YAML, or DSL-based).
    - Allow users to set executor type (local, thread, process) and control concurrency.
    - Offer options for viewing execution logs, metrics, results, and workflow status.
    - Support commands for dry-run, debugging, or exporting workflow structure.
    - Integrate with engine modules (Scheduler, DAG, Task, etc.) to perform requested operations.

Usage:
    Run this script from the command line with various options to:
        - Execute a workflow file: python cli.py run path/to/workflow.py --executor thread --workers 4
        - Validate a workflow file: python cli.py validate path/to/workflow.py
        - List available tasks: python cli.py list-tasks path/to/workflow.py
        - Show workflow status/logs/results
    Users can customize run behavior with additional flags and arguments.
"""

import argparse
import importlib.util
import sys
import os
from pathlib import Path
import json
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dag import DAG
from core.task import Task, TaskState
from core.scheduler import Scheduler
from core.executor import LocalExecutor, ThreadedExecutor, MultiprocessExecutor
from core.event import EventManager, WorkflowEvent
from utils.logging_utils import set_log_level, log_task_started, log_task_succeeded, log_task_failed, log_workflow_started, log_workflow_completed
from utils.metrics_utils import MetricsManager
from state.persistence import PersistenceManager
from dsl.workflow_dsl import Workflow


def load_workflow_module(filepath: str):
    """Load a Python workflow module from filepath."""
    spec = importlib.util.spec_from_file_location("workflow", filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load workflow from {filepath}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_dag_from_module(module) -> DAG:
    """Extract DAG object from a loaded workflow module."""
    # Look for common DAG variable names
    for attr_name in ['dag', 'workflow', 'main_dag', 'DAG']:
        if hasattr(module, attr_name):
            dag_obj = getattr(module, attr_name)
            if isinstance(dag_obj, DAG):
                return dag_obj
    
    # If no DAG found, try to build one from tasks
    dag = DAG()
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, Task):
            dag.add_task(attr)
    
    if not dag.tasks:
        raise ValueError("No DAG or Task objects found in workflow module")
    
    return dag


def run_workflow(args):
    """Execute a workflow file."""
    print(f"Loading workflow from {args.workflow}")
    
    # Set up logging
    if args.verbose:
        set_log_level("DEBUG")
    elif args.quiet:
        set_log_level("ERROR")
    else:
        set_log_level("INFO")
    
    # Load workflow
    module = load_workflow_module(args.workflow)
    dag = extract_dag_from_module(module)
    
    print(f"Found {len(dag.tasks)} tasks in workflow")
    
    if args.dry_run:
        print("\nDry run - workflow structure:")
        dag.print_structure()
        return
    
    # Set up event management
    events = EventManager()
    metrics = MetricsManager()
    
    # Register logging
    events.register(WorkflowEvent.TASK_STARTED, log_task_started)
    events.register(WorkflowEvent.TASK_SUCCEEDED, log_task_succeeded)
    events.register(WorkflowEvent.TASK_FAILED, log_task_failed)
    events.register(WorkflowEvent.WORKFLOW_STARTED, log_workflow_started)
    events.register(WorkflowEvent.WORKFLOW_COMPLETED, log_workflow_completed)
    
    # Register metrics
    events.register(WorkflowEvent.TASK_STARTED, metrics.task_started)
    events.register(WorkflowEvent.TASK_SUCCEEDED, metrics.task_succeeded)
    events.register(WorkflowEvent.TASK_FAILED, metrics.task_failed)
    events.register(WorkflowEvent.WORKFLOW_STARTED, metrics.workflow_started)
    events.register(WorkflowEvent.WORKFLOW_COMPLETED, metrics.workflow_completed)
    
    # Set up persistence if checkpoint file specified
    persistence = None
    if args.checkpoint:
        persistence = PersistenceManager(args.checkpoint)
        persistence.resume(dag)
        persistence.attach_to_events(events)
    
    # Create and run scheduler
    scheduler = Scheduler(
        dag=dag,
        executor_type=args.executor,
        max_workers=args.workers,
        events=events
    )
    
    try:
        scheduler.run()
        print("\nWorkflow execution completed!")
        
        # Print metrics
        if not args.quiet:
            print("\n" + "="*50)
            metrics.print_task_metrics()
            metrics.print_workflow_metrics()
            
    except Exception as e:
        print(f"Workflow execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def validate_workflow(args):
    """Validate a workflow file."""
    try:
        print(f"Validating workflow: {args.workflow}")
        module = load_workflow_module(args.workflow)
        dag = extract_dag_from_module(module)
        
        # Validate DAG
        dag.validate()
        
        print(f"✓ Workflow is valid")
        print(f"  - {len(dag.tasks)} tasks found")
        
        # Check for potential issues
        ready_tasks = dag.get_ready_tasks()
        if not ready_tasks:
            print("  ⚠ Warning: No tasks are ready to run (check dependencies)")
        
        print("\nTask dependency structure:")
        dag.print_structure()
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        sys.exit(1)


def list_tasks(args):
    """List all tasks in a workflow."""
    try:
        module = load_workflow_module(args.workflow)
        dag = extract_dag_from_module(module)
        
        print(f"Tasks in workflow ({len(dag.tasks)} total):")
        print("-" * 50)
        
        for task_name, task in dag.tasks.items():
            deps = [dep.name for dep in task.dependencies] if task.dependencies else []
            deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
            retries_str = f" [max_retries: {task.max_retries}]" if task.max_retries > 0 else ""
            
            print(f"  {task_name}{deps_str}{retries_str}")
            
    except Exception as e:
        print(f"Error listing tasks: {e}")
        sys.exit(1)


def show_status(args):
    """Show workflow status from checkpoint."""
    if not args.checkpoint or not os.path.exists(args.checkpoint):
        print("No checkpoint file found")
        sys.exit(1)
    
    try:
        persistence = PersistenceManager(args.checkpoint)
        state = persistence.load()
        
        print(f"Checkpoint status from: {args.checkpoint}")
        print(f"Saved at: {state.get('metadata', {}).get('saved_at', 'Unknown')}")
        print("-" * 50)
        
        tasks = state.get('tasks', {})
        for task_name, task_info in tasks.items():
            state_str = task_info.get('state', 'UNKNOWN')
            retry_count = task_info.get('retry_count', 0)
            has_result = task_info.get('result') is not None
            has_exception = task_info.get('exception') is not None
            
            status_parts = [state_str]
            if retry_count > 0:
                status_parts.append(f"retries: {retry_count}")
            if has_result:
                status_parts.append("has result")
            if has_exception:
                status_parts.append("has exception")
            
            print(f"  {task_name}: {' | '.join(status_parts)}")
            
    except Exception as e:
        print(f"Error reading status: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="FlowForge Workflow Orchestration Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run sample_workflow.py                    # Run with default settings
  %(prog)s run workflow.py --executor thread -w 4   # Run with 4 threads
  %(prog)s validate my_workflow.py                   # Validate workflow
  %(prog)s list-tasks workflow.py                    # List all tasks
  %(prog)s run workflow.py --checkpoint state.json  # Run with checkpointing
  %(prog)s status --checkpoint state.json           # Show checkpoint status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Execute a workflow')
    run_parser.add_argument('workflow', help='Path to workflow Python file')
    run_parser.add_argument('--executor', '-e', choices=['local', 'thread', 'process'],
                           default='local', help='Executor type (default: local)')
    run_parser.add_argument('--workers', '-w', type=int, default=2,
                           help='Number of worker threads/processes (default: 2)')
    run_parser.add_argument('--checkpoint', '-c', help='Checkpoint file for persistence')
    run_parser.add_argument('--dry-run', action='store_true',
                           help='Show workflow structure without executing')
    run_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Enable verbose logging')
    run_parser.add_argument('--quiet', '-q', action='store_true',
                           help='Minimal output')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a workflow file')
    validate_parser.add_argument('workflow', help='Path to workflow Python file')
    
    # List tasks command
    list_parser = subparsers.add_parser('list-tasks', help='List all tasks in workflow')
    list_parser.add_argument('workflow', help='Path to workflow Python file')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show workflow status from checkpoint')
    status_parser.add_argument('--checkpoint', '-c', required=True,
                              help='Checkpoint file to read status from')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'run':
        run_workflow(args)
    elif args.command == 'validate':
        validate_workflow(args)
    elif args.command == 'list-tasks':
        list_tasks(args)
    elif args.command == 'status':
        show_status(args)


if __name__ == '__main__':
    main()