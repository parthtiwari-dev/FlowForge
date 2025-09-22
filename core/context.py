"""
context.py

Purpose:
    Provides context and resource management utilities for the workflow engine.
    Ensures that necessary resources (files, database connections, network handles, thread/process pools, etc.)
    are allocated before task execution and properly released/cleaned up afterward.
    Supports integration with Python context managers for robust, exception-safe operations.

Key Responsibilities:
    - Define reusable context manager classes/functions for resource handling.
    - Enable automatic setup and teardown for resources needed by tasks or executors.
    - Ensure exception safety, preventing resource leaks on task or workflow failure.
    - Allow custom contexts (e.g., with open files, temp dirs, external API sessions).
    - Integrate context management into Task, Executor, or Scheduler workflows seamlessly.
    - Support extensibility for new resource types and context schemes.

Design & Methods to Implement:
    1. Base context classes/functions using Python's `contextlib` module.
    2. Example context managers for files, database connections, thread/process pools, temp resources.
    3. Utility decorators for wrapping task functions in contexts.
    4. Methods/hooks for setup/teardown tied to task lifecycles or workflow boundaries.

Usage:
    Use context managers to manage resources within task execution code or the engine.
    Wrap task functions or Scheduler routines to ensure safe allocation and release of all resources.
    Plug in custom context managers for specific use cases as needed.

Implementing robust context management ensures stability, safety, and clarity for workflow execution environments.
"""
# utils/context.py
import contextlib
import tempfile
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor


# -------------------------
# Base Context Manager (generic)
# -------------------------
@contextlib.contextmanager
def resource_context(setup, teardown):
    """
    Generic context manager for any resource.
    Example:
        with resource_context(open_file, close_file) as res:
            ...
    """
    resource = setup()
    try:
        yield resource
    finally:
        teardown(resource)


# -------------------------
# Example: File Context
# -------------------------
@contextlib.contextmanager
def file_context(path, mode="r", encoding="utf-8"):
    """
    Safely open and close a file.
    """
    f = open(path, mode, encoding=encoding)
    try:
        yield f
    finally:
        f.close()


# -------------------------
# Example: Temporary Directory
# -------------------------
@contextlib.contextmanager
def temp_dir_context():
    """
    Creates and cleans up a temporary directory.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        # Cleanup directory and files
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(temp_dir)


# -------------------------
# Example: Database Context
# -------------------------
@contextlib.contextmanager
def sqlite_context(db_path=":memory:"):
    """
    Creates and closes a SQLite DB connection.
    """
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


# -------------------------
# Example: Thread Pool Context
# -------------------------
@contextlib.contextmanager
def thread_pool_context(max_workers=4):
    """
    Creates and shuts down a ThreadPoolExecutor.
    """
    executor = ThreadPoolExecutor(max_workers=max_workers)
    try:
        yield executor
    finally:
        executor.shutdown(wait=True)


# -------------------------
# Utility Decorator for Tasks
# -------------------------
def with_context(ctx_manager):
    """
    Decorator to wrap a task function with a context manager.
    Example:
        @with_context(lambda: file_context("data.txt", "r"))
        def process_file(f):
            return f.read()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ctx_manager() as resource:
                return func(resource, *args, **kwargs)
        return wrapper
    return decorator
