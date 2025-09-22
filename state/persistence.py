from __future__ import annotations

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
"""
persistence.py

Simple persistence / checkpointing utilities for the workflow engine.

Features:
- save_state(dag, filepath): serialize DAG + tasks to JSON (atomic write)
- load_state(filepath): load JSON checkpoint into dict
- resume_from_state(dag, state_dict): apply saved state to an existing DAG (set task states, retry counts, results)
- PersistenceManager: helper to attach to EventManager for autosave on events

Notes:
- Uses JSON for simplicity. Task 'result' is stored using json if possible, otherwise repr().
- Atomic writes: write to a temp file then move/replace the target.
- This is a minimal, robust starting point for persistence. You can extend to SQLite / more structured stores later.
"""


import json
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, Optional
from core.dag import DAG
from core.task import Task, TaskState
from core.event import WorkflowEvent


def _safe_serialize(obj: Any) -> Any:
    """
    Try to make an object JSON-serializable.
    If not serializable by json, fallback to repr(obj).
    """
    try:
        # Fast check: try encoding then decoding to ensure JSON compatibility
        json.dumps(obj)
        return obj
    except Exception:
        try:
            # If it's a simple object with __dict__, try to serialize its dict
            if hasattr(obj, "__dict__"):
                json.dumps(obj.__dict__)  # may still fail
                return obj.__dict__
        except Exception:
            pass
    # Fallback
    return repr(obj)


def _atomic_write_text(path: Path, data: str, encoding: str = "utf-8"):
    """
    Atomically write text to a file path by writing to a temp file and replacing the target.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(data)
        # Replace atomically (works on Windows and POSIX for simple cases)
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temp file on error
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


def save_state(dag: DAG, filepath: str) -> None:
    """
    Save the current DAG + tasks state to a JSON file at filepath (atomic write).

    Structure:
    {
      "tasks": {
          "<task_name>": {
              "state": "PENDING"|"RUNNING"|"SUCCESS"|"FAILED",
              "retry_count": int,
              "result": <json-friendly or repr>,
              "exception": "<exception str or None>",
              "dependencies": ["dep_name1", "dep_name2", ...]
          },
          ...
      },
      "metadata": {
          "saved_at": "<iso timestamp>"
      }
    }
    """
    out: Dict[str, Any] = {"tasks": {}, "metadata": {}}
    for t in dag.tasks.values():
        out["tasks"][t.name] = {
            "state": t.state.value if isinstance(t.state, TaskState) else str(t.state),
            "retry_count": getattr(t, "retry_count", 0),
            "result": _safe_serialize(getattr(t, "result", None)),
            "exception": None if getattr(t, "exception", None) is None else str(t.exception),
            "dependencies": [d.name for d in getattr(t, "dependencies", [])],
        }
    out["metadata"]["saved_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"

    json_text = json.dumps(out, indent=2)
    _atomic_write_text(Path(filepath), json_text)


def load_state(filepath: str) -> Dict[str, Any]:
    """
    Load state JSON from filepath and return it as a dict.
    Raises FileNotFoundError if filepath doesn't exist.
    """
    p = Path(filepath)
    if not p.is_file():
        raise FileNotFoundError(f"Checkpoint file not found: {filepath}")
    text = p.read_text(encoding="utf-8")
    return json.loads(text)


def resume_from_state(dag: DAG, state: Dict[str, Any]) -> None:
    """
    Apply a previously saved state dict onto an existing DAG instance.

    Behavior:
    - For each task in state["tasks"], if a task with same name exists in dag:
        - Set its state (TaskState enum)
        - Set retry_count
        - Set result (string or object as deserialized)
        - Set exception (string)
    - Does NOT create tasks missing from the DAG; it will warn/ignore them.
    """
    tasks_state = state.get("tasks", {})
    for name, info in tasks_state.items():
        task = dag.get_task(name)
        if task is None:
            # Skip tasks not present in current DAG
            # Optionally, you could create placeholder Task objects — we keep it simple.
            # print(f"[persistence] Saved task '{name}' not found in current DAG. Skipping.")
            continue

        # Restore state
        state_str = info.get("state")
        try:
            task.state = TaskState(state_str)
        except Exception:
            # If unknown state, leave as PENDING
            try:
                task.state = TaskState.PENDING
            except Exception:
                pass

        # Restore retry_count
        task.retry_count = int(info.get("retry_count", 0))

        # Restore result (best-effort)
        task.result = info.get("result", None)

        # Restore exception string
        exc = info.get("exception", None)
        task.exception = exc

    # No return; DAG tasks updated in place.


class PersistenceManager:
    """
    Convenience manager to coordinate saving/loading and to hook into events for autosave.

    Usage:
        mgr = PersistenceManager("checkpoints/run1.json")
        mgr.save(dag)
        state = mgr.load()
        mgr.resume(dag, state)
        mgr.attach_to_events(event_manager)  # will auto-save on TASK_SUCCEEDED, WORKFLOW_COMPLETED

    By default this manager saves on:
      - WorkflowEvent.TASK_SUCCEEDED
      - WorkflowEvent.WORKFLOW_COMPLETED

    You can override `events_to_watch` or call `save()` manually from Scheduler.
    """
    def __init__(self, filepath: str, events_to_watch: Optional[list] = None):
        self.filepath = filepath
        self.events_to_watch = events_to_watch or [
            WorkflowEvent.TASK_SUCCEEDED,
            WorkflowEvent.WORKFLOW_COMPLETED,
        ]
        self._attached = False
        self._event_manager = None

    def save(self, dag: DAG) -> None:
        """Save DAG state to filepath."""
        try:
            save_state(dag, self.filepath)
        except Exception as e:
            # don't raise inside autosave hooks; the engine should continue running
            print(f"[persistence] Error saving state: {e}")

    def load(self) -> Dict[str, Any]:
        """Load and return state dict (raises if file not found)."""
        return load_state(self.filepath)

    def resume(self, dag: DAG) -> None:
        """Load state from file and apply to DAG (no-op if file missing)."""
        try:
            state = self.load()
            resume_from_state(dag, state)
        except FileNotFoundError:
            # nothing to resume
            return
        except Exception as e:
            print(f"[persistence] Error resuming from state: {e}")

    def attach_to_events(self, event_manager) -> None:
        """
        Attach autosave callbacks to an EventManager instance.
        Event handlers will call save(dag) when those events fire.
        """
        if self._attached:
            return
        self._event_manager = event_manager

        def _handler(**kwargs):
            # Expect kwargs to include 'task' or 'dag' or nothing; we require caller to provide dag via closure
            dag = kwargs.get("dag") or kwargs.get("workflow_dag") or getattr(self, "_dag", None)
            if dag is None:
                # Can't save without DAG object; user should either call save(dag) manually
                return
            self.save(dag)

        # Keep handlers small and non-blocking
        for ev in self.events_to_watch:
            event_manager.register(ev, _handler)
        self._attached = True

    def detach_from_events(self, event_manager) -> None:
        """Remove attached autosave handlers (best-effort)."""
        if not self._attached:
            return
        # We cannot easily remove the exact handler closure without storing it, so detach is best-effort.
        # For simplicity, we will just mark detached; if you need full unregister functionality,
        # store the handler references when attaching and remove them here.
        self._attached = False
