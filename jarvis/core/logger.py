"""Audit-trail logging with credential masking and append-only records."""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
import re
from typing import Any, Dict, Optional


class CredentialMaskingFormatter(logging.Formatter):
    """Log formatter that redacts sensitive data."""

    SENSITIVE_PATTERNS = [
        (r'(api[_-]?key)[\s=:]+([\S]+)', r'\1=***REDACTED***'),
        (r'(password)[\s=:]+([\S]+)', r'\1=***REDACTED***'),
        (r'(token)[\s=:]+([\S]+)', r'\1=***REDACTED***'),
        (r'(authorization)[\s=:]+([\S]+)', r'\1=***REDACTED***'),
        (r'(bearer)[\s=:]+([\S]+)', r'\1=***REDACTED***'),
        (r'("key")[\s=:]+"([^"]+)"', r'\1: "***REDACTED***"'),
    ]

    def format(self, record: logging.LogRecord) -> str:
        # Format the message
        msg = super().format(record)
        # Redact sensitive patterns
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        return msg


class Logger:
    """Centralized logging with audit trail, app log, and error log."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".jarvis" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._setup_loggers()

    def _setup_loggers(self):
        """Initialize all loggers."""
        # Audit logger (immutable append-only)
        self.audit_logger = self._create_logger(
            "jarvis.audit",
            str(self.log_dir / "audit.log"),
            max_bytes=10 * 1024 * 1024,  # 10MB
            backup_count=10,
        )

        # App logger (rotating)
        self.app_logger = self._create_logger(
            "jarvis.app",
            str(self.log_dir / "app.log"),
            max_bytes=5 * 1024 * 1024,  # 5MB
            backup_count=5,
        )

        # Error logger (rotating)
        self.error_logger = self._create_logger(
            "jarvis.error",
            str(self.log_dir / "error.log"),
            max_bytes=5 * 1024 * 1024,  # 5MB
            backup_count=5,
        )

    def _create_logger(
        self,
        name: str,
        log_file: str,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 5,
    ) -> logging.Logger:
        """Create a rotating file logger."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        formatter = CredentialMaskingFormatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def audit(self, event: str, **context) -> None:
        """Log an audit event with context."""
        log_entry = {"event": event, "timestamp": datetime.utcnow().isoformat()}
        log_entry.update(context)
        self.audit_logger.info(json.dumps(log_entry))

    def info(self, msg: str, **kwargs) -> None:
        """Log info message."""
        self.app_logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message."""
        self.app_logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        """Log error message."""
        self.error_logger.error(msg, **kwargs)
        self.app_logger.error(msg, **kwargs)

    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message."""
        self.app_logger.debug(msg, **kwargs)

    def mission_started(self, mission_id: str, intent: str, mode: str) -> None:
        """Log mission start."""
        self.audit(
            "mission_started",
            mission_id=mission_id,
            intent=intent,
            mode=mode,
        )

    def mission_completed(self, mission_id: str, status: str, artifacts: int) -> None:
        """Log mission completion."""
        self.audit(
            "mission_completed",
            mission_id=mission_id,
            status=status,
            artifacts_generated=artifacts,
        )

    def action_executed(
        self,
        mission_id: str,
        action_type: str,
        tool: str,
        status: str,
        duration_ms: int,
    ) -> None:
        """Log an executed action."""
        self.audit(
            "action_executed",
            mission_id=mission_id,
            action_type=action_type,
            tool=tool,
            status=status,
            duration_ms=duration_ms,
        )

    def error_occurred(
        self,
        mission_id: str,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error with full context."""
        log_data = {
            "mission_id": mission_id,
            "error_type": error_type,
            "message": message,
        }
        if context:
            log_data.update(context)
        self.audit("error_occurred", **log_data)
        self.error(f"[{mission_id}] {error_type}: {message}")
