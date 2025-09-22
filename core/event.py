# This file implements the Event + Observer pattern for notifications and logging hooks.
"""
event.py

Purpose:
    Implements an event/observer pattern for the workflow orchestration engine.
    The EventManager enables any part of the system (logging, metrics, notifications, etc.)
    to register as listeners/observers for specific workflow events. 
    This provides fully decoupled, runtime-extensible hooks for lifecycle changes (task start, success, failure, retry, workflow completion, etc.).

Key Responsibilities:
    - Define a flexible mechanism for broadcasting events and notifying registered listeners.
    - Allow listeners to subscribe/unsubscribe to specific event types dynamically.
    - Fire events at critical workflow moments (e.g., task_started, task_succeeded, task_failed, workflow_started, workflow_completed).
    - Pass relevant event data/context to listeners for customized handling (e.g., log messages, send metrics, notifications).
    - Ensure event system is lightweight and never blocks or breaks main engine execution.
    - Support extensibility: enable plugin-like integration for new observers in future.

Design & Methods to Implement:
    1. EventManager class:
        - register(event_type, listener): Add a function/callback for an event type.
        - unregister(event_type, listener): Remove a listener for an event type.
        - notify(event_type, **kwargs): Broadcast event and call all listeners for type, passing event data.
    2. Internal attributes:
        - Mapping from event_type (str) to list of listeners/callbacks.
    3. Define standard event types (constants or Enum), e.g.:
        - "task_started", "task_succeeded", "task_failed", "task_retried"
        - "workflow_started", "workflow_completed"
    4. Usage pattern:
        - Fire events within Task, Scheduler, or DAG at key points.
        - Logging, metrics, and other utils register as listeners for relevant events.

Usage:
    EventManager is instantiated centrally (or as needed).
    Core modules fire events via notify().
    Any internal or external utility attaches listeners for custom behaviors.

This pattern provides robust, scalable observability and integration for your workflow engine, supporting maintainable code and easy feature extension.
"""
from collections import defaultdict
from typing import Callable

class EventManager:
    """
    Manages event listeners and dispatches notifications to them.
    Implements a simple Observer pattern for workflow events.
    """
    def __init__(self):
        # Maps event_type -> list of listeners (functions/callables)
        self._listeners = defaultdict(list)

    def register(self, event_type: str, listener: Callable[..., None]):
        """
        Registers a listener (function/callback) for a given event_type.
        Avoids duplicate registrations.

        Args:
            event_type (str): The type of event to listen for.
            listener (callable): Function to call when event_type fires.
        """
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)

    def unregister(self, event_type: str, listener: Callable[..., None]):
        """
        Unregisters a listener from a given event_type.

        Args:
            event_type (str): The event type.
            listener (callable): Registered listener to remove.
        """
        if listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)

    def notify(self, event_type: str, **event_data):
        """
        Broadcasts an event, calling all registered listeners for that type.

        Args:
            event_type (str): The type of event.
            **event_data: Arbitrary keyword arguments passing event context
                          (e.g., task object, error, status).
        """
        for listener in self._listeners[event_type]:
            try:
                listener(**event_data)
            except Exception as e:
                # Safely catch listener errors to avoid breaking main workflow
                print(f"[EventManager] Error in listener for '{event_type}': {e}")

    def clear_listeners(self, event_type: str = None):
        """
        Clears all listeners for a specific event type or all event types.

        Args:
            event_type (str, optional): If provided, clears only this event type.
        """
        if event_type:
            self._listeners[event_type] = []
        else:
            self._listeners.clear()


# Optional: Define standard event types
class WorkflowEvent:
    TASK_STARTED = "task_started"
    TASK_SUCCEEDED = "task_succeeded"
    TASK_FAILED = "task_failed"
    TASK_RETRIED = "task_retried"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
