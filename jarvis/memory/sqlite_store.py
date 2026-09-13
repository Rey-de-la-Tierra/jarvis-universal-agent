"""SQLite-based operational memory and checkpoint storage."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class SQLiteStore:
    """SQLite database for authoritative operational state."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".jarvis" / "memory" / "jarvis.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema."""
        with self._connection() as conn:
            cursor = conn.cursor()

            # Missions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    intent TEXT NOT NULL,
                    mode TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    cost_usd REAL,
                    metadata JSON
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    parent_task_id TEXT,
                    description TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata JSON,
                    FOREIGN KEY (mission_id) REFERENCES missions(mission_id)
                )
            """)

            # Actions table (audit trail)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    action_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    task_id TEXT,
                    action_type TEXT,
                    tool TEXT,
                    status TEXT,
                    input JSON,
                    output JSON,
                    error TEXT,
                    screenshot_path TEXT,
                    duration_ms INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (mission_id) REFERENCES missions(mission_id),
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            """)

            # Checkpoints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    checkpoint_type TEXT,
                    state JSON NOT NULL,
                    created_at TIMESTAMP,
                    FOREIGN KEY (mission_id) REFERENCES missions(mission_id)
                )
            """)

            # Audit log (immutable append-only)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL,
                    mission_id TEXT,
                    details JSON,
                    created_at TIMESTAMP,
                    FOREIGN KEY (mission_id) REFERENCES missions(mission_id)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_mission ON tasks(mission_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_mission ON actions(mission_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_mission ON checkpoints(mission_id)")

            logger.info(f"SQLite database initialized: {self.db_path}")

    def create_mission(self, mission_id: str, intent: str, mode: str, metadata: Optional[Dict] = None) -> bool:
        """Create a new mission record."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO missions (mission_id, intent, mode, status, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (mission_id, intent, mode, "pending", datetime.utcnow().isoformat(), json.dumps(metadata or {}))
                )
            logger.info(f"Mission created: {mission_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create mission: {e}")
            return False

    def update_mission(self, mission_id: str, status: str, cost_usd: Optional[float] = None) -> bool:
        """Update mission status and cost."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                if status == "running" and cost_usd is None:
                    cursor.execute(
                        "UPDATE missions SET status = ?, started_at = ? WHERE mission_id = ?",
                        (status, datetime.utcnow().isoformat(), mission_id)
                    )
                elif status == "completed":
                    cursor.execute(
                        "UPDATE missions SET status = ?, completed_at = ?, cost_usd = ? WHERE mission_id = ?",
                        (status, datetime.utcnow().isoformat(), cost_usd, mission_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE missions SET status = ? WHERE mission_id = ?",
                        (status, mission_id)
                    )
            return True
        except Exception as e:
            logger.error(f"Failed to update mission: {e}")
            return False

    def get_mission(self, mission_id: str) -> Optional[Dict]:
        """Retrieve mission details."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Failed to get mission: {e}")
        return None

    def create_task(self, task_id: str, mission_id: str, description: str, parent_task_id: Optional[str] = None) -> bool:
        """Create a new task record."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO tasks (task_id, mission_id, parent_task_id, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (task_id, mission_id, parent_task_id, description, "pending", datetime.utcnow().isoformat())
                )
            return True
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return False

    def update_task(self, task_id: str, status: str) -> bool:
        """Update task status."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                completed_at = datetime.utcnow().isoformat() if status == "completed" else None
                cursor.execute(
                    "UPDATE tasks SET status = ?, completed_at = ? WHERE task_id = ?",
                    (status, completed_at, task_id)
                )
            return True
        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return False

    def get_tasks_for_mission(self, mission_id: str) -> List[Dict]:
        """Get all tasks for a mission."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks WHERE mission_id = ? ORDER BY created_at", (mission_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

    def log_action(
        self,
        action_id: str,
        mission_id: str,
        task_id: Optional[str],
        action_type: str,
        tool: str,
        status: str,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        error: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Log an executed action."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO actions 
                    (action_id, mission_id, task_id, action_type, tool, status, input, output, error, screenshot_path, duration_ms, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        action_id,
                        mission_id,
                        task_id,
                        action_type,
                        tool,
                        status,
                        json.dumps(input_data or {}),
                        json.dumps(output_data or {}),
                        error,
                        screenshot_path,
                        duration_ms,
                        datetime.utcnow().isoformat()
                    )
                )
            return True
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
            return False

    def save_checkpoint(self, checkpoint_id: str, mission_id: str, checkpoint_type: str, state: Dict) -> bool:
        """Save a checkpoint."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO checkpoints (checkpoint_id, mission_id, checkpoint_type, state, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (checkpoint_id, mission_id, checkpoint_type, json.dumps(state), datetime.utcnow().isoformat())
                )
            logger.info(f"Checkpoint saved: {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    def get_latest_checkpoint(self, mission_id: str, checkpoint_type: Optional[str] = None) -> Optional[Dict]:
        """Get the most recent checkpoint for a mission."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                if checkpoint_type:
                    cursor.execute(
                        """
                        SELECT * FROM checkpoints 
                        WHERE mission_id = ? AND checkpoint_type = ? 
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (mission_id, checkpoint_type)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM checkpoints WHERE mission_id = ? ORDER BY created_at DESC LIMIT 1",
                        (mission_id,)
                    )
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result["state"] = json.loads(result["state"])
                    return result
        except Exception as e:
            logger.error(f"Failed to get checkpoint: {e}")
        return None

    def audit_log(
        self,
        event: str,
        mission_id: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> bool:
        """Write to immutable audit log."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO audit_log (event, mission_id, details, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (event, mission_id, json.dumps(details or {}), datetime.utcnow().isoformat())
                )
            return True
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            return False

    def get_audit_log(self, mission_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve audit log entries."""
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                if mission_id:
                    cursor.execute(
                        "SELECT * FROM audit_log WHERE mission_id = ? ORDER BY created_at DESC LIMIT ?",
                        (mission_id, limit)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get audit log: {e}")
            return []
