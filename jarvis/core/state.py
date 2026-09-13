"""Global state manager for JARVIS runtime."""

import threading
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum


class SystemState(Enum):
    """System operational state."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class GlobalState:
    """Thread-safe global runtime state."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            "system_state": SystemState.INITIALIZING,
            "start_time": datetime.utcnow(),
            "current_mission_id": None,
            "current_mission_intent": None,
            "missions_completed": 0,
            "total_cost_usd": 0.0,
            "internet_available": None,  # Will be probed
            "ollama_available": False,
            "lm_studio_available": False,
            "voice_available": False,
            "browser_available": False,
            "metrics": {
                "actions_executed": 0,
                "errors_occurred": 0,
                "checkpoints_saved": 0,
            },
        }
        self._initialized = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        with self._lock:
            keys = key.split(".")
            value = self._state
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
            return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set a state value."""
        with self._lock:
            keys = key.split(".")
            current = self._state
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value

    def increment(self, key: str, amount: int = 1) -> None:
        """Increment a numeric state value."""
        with self._lock:
            current = self.get(key, 0)
            self.set(key, current + amount)

    def set_system_state(self, state: SystemState) -> None:
        """Set overall system state."""
        self.set("system_state", state)

    def get_system_state(self) -> SystemState:
        """Get overall system state."""
        return self.get("system_state", SystemState.INITIALIZING)

    def start_mission(self, mission_id: str, intent: str) -> None:
        """Mark mission as active."""
        with self._lock:
            self.set("current_mission_id", mission_id)
            self.set("current_mission_intent", intent)
            self.set("system_state", SystemState.BUSY)

    def end_mission(self) -> None:
        """Mark mission as completed."""
        with self._lock:
            self.set("current_mission_id", None)
            self.set("current_mission_intent", None)
            self.increment("missions_completed")
            # Don't set system_state to READY yet; let watchdog decide

    def add_cost(self, amount: float) -> None:
        """Add to cumulative cost tracking."""
        current = self.get("total_cost_usd", 0.0)
        self.set("total_cost_usd", current + amount)

    def dump(self) -> Dict[str, Any]:
        """Export state as dict."""
        with self._lock:
            return dict(self._state)
