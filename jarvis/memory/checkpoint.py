"""Checkpoint management for mission resumption."""

import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from jarvis.memory.sqlite_store import SQLiteStore
import logging

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages mission and task checkpoints for resumption on crash."""

    def __init__(self, store: SQLiteStore):
        self.store = store

    def checkpoint_mission_start(self, mission_id: str) -> bool:
        """Save checkpoint at mission start."""
        state = {
            "phase": "mission_start",
            "timestamp": datetime.utcnow().isoformat(),
            "completed_tasks": [],
        }
        checkpoint_id = f"mission-start-{mission_id}"
        return self.store.save_checkpoint(checkpoint_id, mission_id, "mission_start", state)

    def checkpoint_task_complete(self, mission_id: str, task_id: str, task_result: Dict[str, Any]) -> bool:
        """Save checkpoint after task completion."""
        state = {
            "phase": "task_complete",
            "task_id": task_id,
            "result": task_result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        checkpoint_id = f"task-{task_id}"
        return self.store.save_checkpoint(checkpoint_id, mission_id, "task_complete", state)

    def checkpoint_mission_complete(self, mission_id: str, artifacts: Dict[str, Any]) -> bool:
        """Save checkpoint at mission completion."""
        state = {
            "phase": "mission_complete",
            "artifacts": artifacts,
            "timestamp": datetime.utcnow().isoformat(),
        }
        checkpoint_id = f"mission-complete-{mission_id}"
        return self.store.save_checkpoint(checkpoint_id, mission_id, "mission_complete", state)

    def get_latest_checkpoint(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent checkpoint for resumption."""
        return self.store.get_latest_checkpoint(mission_id)

    def can_resume(self, mission_id: str) -> bool:
        """Check if a mission can be resumed from checkpoint."""
        checkpoint = self.get_latest_checkpoint(mission_id)
        return checkpoint is not None and checkpoint["state"].get("phase") != "mission_complete"
