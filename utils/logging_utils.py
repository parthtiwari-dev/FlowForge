"""
logging_utils.py

Purpose:
    Provides utilities for logging workflow execution, task events, errors, and system status.
    Enables flexible configuration of log formatting, destinations (console, file), and log levels.
    Can be used directly or registered as listeners in the event/observer system.

Key Responsibilities:
    - Define log functions for task lifecycle events (start, success, failure, retry).
    - Enable logging of workflow status, progress, and errors with clear format.
    - Allow toggling verbose/debug modes for detailed workflow analysis.
    - Support integration with Python's standard logging module for advanced use-cases.
    - Facilitate reproducible, readable output for monitoring and debugging.

Usage:
    Import and use log functions directly, or register them as event listeners via EventManager.
    Configure log level/output as needed for development or production scenarios.
"""
import logging
import os

# -------------------------
# Ensure logs directory exists
# -------------------------
os.makedirs("logs", exist_ok=True)

# -------------------------
# Logger Configuration
# -------------------------
logger = logging.getLogger("workflow_engine")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler("logs/workflow.log")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# -------------------------
# Task Event Logging
# -------------------------
def log_task_started(task, **kwargs):
    msg = f"Task STARTED: {task.name}"
    if hasattr(task, "result") and task.result is not None:
        msg += f" | Previous Result: {task.result}"
    logger.info(msg)

def log_task_succeeded(task, **kwargs):
    msg = f"Task SUCCEEDED: {task.name}"
    if hasattr(task, "result") and task.result is not None:
        msg += f" | Result: {task.result}"
    logger.info(msg)

def log_task_failed(task, exception=None, **kwargs):
    exc_msg = exception or getattr(task, "exception", None)
    logger.error(f"Task FAILED: {task.name} | Exception: {exc_msg}")

def log_task_retried(task, **kwargs):
    logger.warning(f"Task RETRIED: {task.name} | Retry count: {task.retry_count}")

# -------------------------
# Workflow Event Logging
# -------------------------
def log_workflow_started(**kwargs):
    logger.info("Workflow execution STARTED.")

def log_workflow_completed(**kwargs):
    logger.info("Workflow execution COMPLETED.")

# -------------------------
# Custom ad-hoc log helper
# -------------------------
def log_custom(message, level="info"):
    level = level.lower()
    if level == "debug":
        logger.debug(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.info(message)

def set_log_level(level="INFO"):
    """
    Set the log level for the workflow logger.
    Usage: set_log_level("DEBUG"), set_log_level("INFO"), etc.
    """
    logger.setLevel(level.upper())
    for handler in logger.handlers:
        handler.setLevel(level.upper())
