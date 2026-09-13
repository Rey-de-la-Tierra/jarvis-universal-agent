"""Brain router: intelligent LLM selection based on task requirements and system state."""

import logging
from typing import List, Optional, Set
from enum import Enum
from jarvis.brain.model_registry import ModelCapability, ModelRegistry, ModelMetadata
from jarvis.core.config import Config
from jarvis.core.state import GlobalState

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    """JARVIS operation mode."""
    AUTO = "AUTO"    # Auto-detect, intelligent fallback
    LAND = "LAND"    # Cloud-first
    SEA = "SEA"      # Offline-only


class Arbiter:
    """Intelligent LLM router based on capability, cost, privacy, latency."""

    def __init__(self, registry: ModelRegistry, config: Config, state: GlobalState):
        self.registry = registry
        self.config = config
        self.state = state

    def select_model(
        self,
        required_capabilities: Set[ModelCapability],
        max_budget_usd: Optional[float] = None,
        privacy_level: Optional[str] = None,
        mode_override: Optional[str] = None,
    ) -> Optional[ModelMetadata]:
        """Select the best model for a task.
        
        Decision tree:
        1. Check privacy level (high → force SEA/offline)
        2. Check operation mode (AUTO/LAND/SEA)
        3. Filter by required capabilities
        4. Filter by budget
        5. Rank by: capability match → reliability → latency → cost
        6. Fall back to alternatives on primary choice unavailable
        """
        # Get effective privacy level and mode
        privacy = privacy_level or self.config.get("privacy_level", "normal")
        mode = mode_override or self.config.get_mode()
        budget = max_budget_usd or self.config.get_cost_limit()

        # Force offline if privacy-critical
        if privacy == "high":
            return self._select_offline_model(required_capabilities, budget)

        # Route based on mode
        if mode == "AUTO":
            return self._select_auto_mode(required_capabilities, budget)
        elif mode == "LAND":
            return self._select_land_mode(required_capabilities, budget)
        elif mode == "SEA":
            return self._select_sea_mode(required_capabilities, budget)
        else:
            logger.warning(f"Unknown mode: {mode}, defaulting to AUTO")
            return self._select_auto_mode(required_capabilities, budget)

    def _select_offline_model(
        self,
        required_capabilities: Set[ModelCapability],
        max_budget_usd: Optional[float] = None,
    ) -> Optional[ModelMetadata]:
        """Select best offline (Ollama/LM Studio) model."""
        candidates = self.registry.list_models(
            provider=None,
            capabilities=required_capabilities,
            enabled_only=True,
        )
        candidates = [m for m in candidates if m.provider in ["ollama", "lm_studio"]]

        if not candidates:
            logger.warning(
                f"No offline model found with capabilities: {required_capabilities}"
            )
            return None

        # Sort by latency (local is fastest)
        candidates.sort(key=lambda m: m.latency_ms or float('inf'))
        logger.info(f"Selected offline model: {candidates[0].name}")
        return candidates[0]

    def _select_auto_mode(
        self,
        required_capabilities: Set[ModelCapability],
        max_budget_usd: Optional[float] = None,
    ) -> Optional[ModelMetadata]:
        """AUTO mode: try cloud, fall back to local."""
        # Check internet availability
        internet_available = self.state.get("internet_available")
        if internet_available is None:
            # Assume online for now; probe will update state
            internet_available = True

        # Try primary online API first
        if internet_available:
            primary_api = self.config.get("primary_api", "openrouter")
            candidates = self.registry.list_models(
                provider=primary_api,
                capabilities=required_capabilities,
                enabled_only=True,
            )
            if candidates:
                logger.info(f"AUTO mode: using {primary_api} ({candidates[0].name})")
                return candidates[0]

            # Try fallback chain
            fallback_chain = self.config.get("fallback_chain", ["ollama", "lm_studio"])
            for provider in fallback_chain:
                candidates = self.registry.list_models(
                    provider=provider,
                    capabilities=required_capabilities,
                    enabled_only=True,
                )
                if candidates:
                    logger.info(f"AUTO mode: falling back to {provider} ({candidates[0].name})")
                    return candidates[0]

        # Fall back to offline
        return self._select_offline_model(required_capabilities, max_budget_usd)

    def _select_land_mode(
        self,
        required_capabilities: Set[ModelCapability],
        max_budget_usd: Optional[float] = None,
    ) -> Optional[ModelMetadata]:
        """LAND mode: cloud-first, local fallback."""
        primary_api = self.config.get("primary_api", "openrouter")
        candidates = self.registry.list_models(
            provider=primary_api,
            capabilities=required_capabilities,
            enabled_only=True,
        )

        if candidates:
            logger.info(f"LAND mode: using {primary_api} ({candidates[0].name})")
            return candidates[0]

        # Try fallback chain
        fallback_chain = self.config.get("fallback_chain", ["ollama", "lm_studio"])
        for provider in fallback_chain:
            candidates = self.registry.list_models(
                provider=provider,
                capabilities=required_capabilities,
                enabled_only=True,
            )
            if candidates:
                logger.info(f"LAND mode: falling back to {provider} ({candidates[0].name})")
                return candidates[0]

        logger.error(f"LAND mode: no model found for capabilities {required_capabilities}")
        return None

    def _select_sea_mode(
        self,
        required_capabilities: Set[ModelCapability],
        max_budget_usd: Optional[float] = None,
    ) -> Optional[ModelMetadata]:
        """SEA mode: offline-only, no cloud APIs."""
        return self._select_offline_model(required_capabilities, max_budget_usd)

    def get_fallback_chain(self) -> List[str]:
        """Get configured fallback API chain."""
        return self.config.get("fallback_chain", ["ollama", "lm_studio"])

    def set_mode(self, mode: str) -> None:
        """Change operation mode."""
        if mode not in ["AUTO", "LAND", "SEA"]:
            raise ValueError(f"Invalid mode: {mode}")
        self.config.set_mode(mode)
        logger.info(f"Operation mode changed to: {mode}")
