"""
persistence.py

Purpose:
    Provides utilities for saving, loading, and managing workflow state and progress across engine sessions.
    Enables checkpointing and recovery of workflows and tasks, supporting robustness for long-running jobs,
    restarts on failure, and real-time monitoring.

Key Responsibilities:
    - Serialize current state of DAG, Tasks, and Scheduler (including task statuses, results, retries, and metrics).
    - Persist workflow state to disk (e.g., JSON, YAML, SQLite), allowing later restoration and continuation.
    - Load saved state and resume execution from checkpoints.
    - Integrate persistence hooks into Scheduler, Task, or workflow routines for easy saving/loading.
    - Support incremental updates (e.g., periodic autosave, state on events).
    - Provide reporting and inspection utilities for persisted runs.

Design & Methods to Implement:
    1. Functions/classes for:
        - save_state(obj, filepath): Serialize and store workflow/task state to file.
        - load_state(filepath): Deserialize and restore state from file.
        - autosave hooks: Optional periodic or on-event saving.
    2. Support for JSON/YAML (simple start) and extensibility to databases (SQLite) or other formats.
    3. Ensure atomic writes and exception safety to prevent corruption or loss.
    4. Methods for inspection and reporting of loaded/saved state.

Usage:
    Use persistence.save_state() to checkpoint workflow at key intervals, and load_state() to recover.
    Integrate with Scheduler or EventManager for regular or event-triggered saves.
    This enhances reliability, recovery, and auditability in your workflow engine.
"""
