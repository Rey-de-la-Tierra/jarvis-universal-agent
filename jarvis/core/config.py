"""Configuration management with YAML support and schema validation."""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for a single LLM API."""
    name: str
    endpoint: str
    api_key_env: Optional[str] = None  # e.g., "OPENROUTER_API_KEY"
    enabled: bool = True
    timeout_seconds: int = 60
    max_retries: int = 3
    cost_per_1m_tokens: Optional[float] = None
    capabilities: Dict[str, bool] = None  # {"vision": True, "tool_use": True}

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = {}


@dataclass
class ModelConfig:
    """Configuration for a single LLM model."""
    name: str
    provider: str  # "openrouter", "ollama", "lm_studio", etc.
    context_window: int
    enabled: bool = True
    vision_capable: bool = False
    tool_use_capable: bool = False
    typical_latency_ms: Optional[int] = None
    max_concurrent: int = 1


class Config:
    """Unified configuration manager."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".jarvis"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.yaml"
        self.profiles_file = self.config_dir / "profiles.yaml"
        self.models_file = self.config_dir / "models.yaml"
        self.logging_file = self.config_dir / "logging.yaml"

        # Load configurations
        self._raw_config = self._load_yaml(self.config_file) or {}
        self._profiles = self._load_yaml(self.profiles_file) or {}
        self._models = self._load_yaml(self.models_file) or {}

        # Ensure defaults
        self._ensure_defaults()

    def _load_yaml(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load YAML file, return None if doesn't exist."""
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            return {}

    def _ensure_defaults(self):
        """Ensure critical config keys exist."""
        defaults = {
            "mode": "AUTO",
            "primary_api": "openrouter",
            "fallback_chain": ["ollama", "lm_studio"],
            "cost_limit_per_mission": 5.0,
            "cost_limit_per_month": 100.0,
            "privacy_level": "normal",  # or "high" (forces offline)
            "voice_enabled": True,
            "voice_provider": "voicestudio",  # or "sapi"
            "auto_checkpoint_interval_seconds": 60,
            "max_mission_depth": 10,
            "max_retries_per_task": 3,
            "task_timeout_seconds": 3600,
        }
        for key, value in defaults.items():
            if key not in self._raw_config:
                self._raw_config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key."""
        parts = key.split(".")
        value = self._raw_config
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set config value by dot-notation key."""
        parts = key.split(".")
        current = self._raw_config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        self._save_config()

    def _save_config(self) -> None:
        """Save config to YAML file."""
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(self._raw_config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_mode(self) -> str:
        """Get current operation mode (AUTO, LAND, SEA)."""
        return self.get("mode", "AUTO")

    def set_mode(self, mode: str) -> None:
        """Set operation mode."""
        if mode not in ["AUTO", "LAND", "SEA"]:
            raise ValueError(f"Invalid mode: {mode}. Must be AUTO, LAND, or SEA.")
        self.set("mode", mode)

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a named profile (e.g., 'production', 'research', 'heavy-work')."""
        return self._profiles.get(name)

    def list_profiles(self) -> list:
        """List all available profiles."""
        return list(self._profiles.keys())

    def set_profile(self, name: str) -> None:
        """Activate a profile by copying its settings to main config."""
        profile = self.get_profile(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found")
        self._raw_config.update(profile)
        self._save_config()
        logger.info(f"Profile '{name}' activated")

    def get_api_config(self, api_name: str) -> Optional[APIConfig]:
        """Get configuration for a specific API."""
        apis = self.get("apis", {})
        api_data = apis.get(api_name)
        if not api_data:
            return None
        return APIConfig(**api_data)

    def list_apis(self) -> list:
        """List all configured APIs."""
        apis = self.get("apis", {})
        return list(apis.keys())

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        models = self.get("models", {})
        model_data = models.get(model_name)
        if not model_data:
            return None
        return ModelConfig(**model_data)

    def list_models(self, provider: Optional[str] = None) -> list:
        """List models, optionally filtered by provider."""
        models = self.get("models", {})
        if provider:
            return [name for name, cfg in models.items() if cfg.get("provider") == provider]
        return list(models.keys())

    def is_sensitive_work(self) -> bool:
        """Check if current privacy level forces offline-only (SEA mode)."""
        return self.get("privacy_level") == "high"

    def get_cost_limit(self) -> float:
        """Get cost limit per mission (in USD)."""
        return self.get("cost_limit_per_mission", 5.0)

    def dump(self) -> Dict[str, Any]:
        """Export entire config as dict (secrets redacted)."""
        config_copy = json.loads(json.dumps(self._raw_config))
        # Redact API keys
        if "apis" in config_copy:
            for api_name in config_copy["apis"]:
                if "api_key_env" in config_copy["apis"][api_name]:
                    config_copy["apis"][api_name]["api_key_env"] = "***REDACTED***"
        return config_copy
