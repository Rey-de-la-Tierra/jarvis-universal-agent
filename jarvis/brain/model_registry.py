"""Model capability registry and metadata store."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum


class ModelCapability(Enum):
    """Model capability flags."""
    VISION = "vision"
    TOOL_USE = "tool_use"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"
    STREAMING = "streaming"
    LONG_CONTEXT = "long_context"
    CODE_EXECUTION = "code_execution"
    REASONING = "reasoning"


@dataclass
class ModelMetadata:
    """Complete model metadata."""
    name: str
    provider: str  # "openrouter", "ollama", "lm_studio", etc.
    context_window: int
    max_output_tokens: int
    capabilities: Set[ModelCapability] = field(default_factory=set)
    latency_ms: Optional[int] = None  # Typical latency, empirically measured
    cost_per_1m_input_tokens: Optional[float] = None
    cost_per_1m_output_tokens: Optional[float] = None
    vision_capable: bool = False
    tool_use_capable: bool = False
    enabled: bool = True
    notes: str = ""

    def has_capability(self, capability: ModelCapability) -> bool:
        """Check if model has a capability."""
        return capability in self.capabilities

    def matches_requirements(self, required_capabilities: Set[ModelCapability]) -> bool:
        """Check if model meets all required capabilities."""
        return required_capabilities.issubset(self.capabilities)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Optional[float]:
        """Estimate cost for a request (in USD)."""
        if self.cost_per_1m_input_tokens is None or self.cost_per_1m_output_tokens is None:
            return None
        input_cost = (input_tokens / 1_000_000) * self.cost_per_1m_input_tokens
        output_cost = (output_tokens / 1_000_000) * self.cost_per_1m_output_tokens
        return input_cost + output_cost


class ModelRegistry:
    """Central registry of all available models."""

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize with known high-quality models."""
        # OpenRouter models (sample)
        self._models["openrouter:claude-3-opus"] = ModelMetadata(
            name="openrouter:claude-3-opus",
            provider="openrouter",
            context_window=200000,
            max_output_tokens=4096,
            capabilities={
                ModelCapability.VISION,
                ModelCapability.TOOL_USE,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
                ModelCapability.REASONING,
            },
            latency_ms=2000,
            cost_per_1m_input_tokens=15.0,
            cost_per_1m_output_tokens=75.0,
            vision_capable=True,
            tool_use_capable=True,
            notes="Best-in-class reasoning and vision",
        )

        self._models["openrouter:claude-3-sonnet"] = ModelMetadata(
            name="openrouter:claude-3-sonnet",
            provider="openrouter",
            context_window=200000,
            max_output_tokens=4096,
            capabilities={
                ModelCapability.VISION,
                ModelCapability.TOOL_USE,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            },
            latency_ms=1500,
            cost_per_1m_input_tokens=3.0,
            cost_per_1m_output_tokens=15.0,
            vision_capable=True,
            tool_use_capable=True,
            notes="Best price/performance balance",
        )

        self._models["openrouter:gpt-4-vision"] = ModelMetadata(
            name="openrouter:gpt-4-vision",
            provider="openrouter",
            context_window=128000,
            max_output_tokens=4096,
            capabilities={
                ModelCapability.VISION,
                ModelCapability.TOOL_USE,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            },
            latency_ms=3000,
            cost_per_1m_input_tokens=30.0,
            cost_per_1m_output_tokens=60.0,
            vision_capable=True,
            tool_use_capable=True,
            notes="Strong vision and reasoning",
        )

        # Local Ollama models
        self._models["ollama:mistral"] = ModelMetadata(
            name="ollama:mistral",
            provider="ollama",
            context_window=32000,
            max_output_tokens=8000,
            capabilities={
                ModelCapability.TOOL_USE,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            },
            latency_ms=500,
            cost_per_1m_input_tokens=0.0,
            cost_per_1m_output_tokens=0.0,
            tool_use_capable=True,
            notes="Fast, efficient, local. No vision.",
        )

        self._models["ollama:llama2-13b"] = ModelMetadata(
            name="ollama:llama2-13b",
            provider="ollama",
            context_window=4096,
            max_output_tokens=2048,
            capabilities={
                ModelCapability.TOOL_USE,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            },
            latency_ms=800,
            cost_per_1m_input_tokens=0.0,
            cost_per_1m_output_tokens=0.0,
            tool_use_capable=True,
            notes="General purpose, local. No vision.",
        )

        self._models["ollama:neural-chat"] = ModelMetadata(
            name="ollama:neural-chat",
            provider="ollama",
            context_window=8192,
            max_output_tokens=4096,
            capabilities={
                ModelCapability.STREAMING,
            },
            latency_ms=600,
            cost_per_1m_input_tokens=0.0,
            cost_per_1m_output_tokens=0.0,
            notes="Conversational, local. Lightweight.",
        )

    def register_model(self, metadata: ModelMetadata) -> None:
        """Register a new model."""
        self._models[metadata.name] = metadata

    def get_model(self, name: str) -> Optional[ModelMetadata]:
        """Get model metadata by name."""
        return self._models.get(name)

    def list_models(
        self,
        provider: Optional[str] = None,
        capabilities: Optional[Set[ModelCapability]] = None,
        enabled_only: bool = True,
    ) -> List[ModelMetadata]:
        """List models with optional filtering."""
        result = list(self._models.values())

        if enabled_only:
            result = [m for m in result if m.enabled]

        if provider:
            result = [m for m in result if m.provider == provider]

        if capabilities:
            result = [m for m in result if m.matches_requirements(capabilities)]

        # Sort by latency (faster first)
        result.sort(key=lambda m: m.latency_ms or float('inf'))
        return result

    def find_best_model(
        self,
        required_capabilities: Set[ModelCapability],
        prefer_provider: Optional[str] = None,
        max_cost_per_1m_output: Optional[float] = None,
        prefer_low_latency: bool = True,
    ) -> Optional[ModelMetadata]:
        """Find the best model for a task.
        
        Ranking criteria (in order):
        1. Capability match (required)
        2. Provider preference
        3. Cost limit
        4. Latency (if prefer_low_latency)
        """
        candidates = self.list_models(capabilities=required_capabilities, enabled_only=True)

        if not candidates:
            return None

        # Filter by cost if specified
        if max_cost_per_1m_output:
            candidates = [
                m for m in candidates
                if m.cost_per_1m_output_tokens is None
                or m.cost_per_1m_output_tokens <= max_cost_per_1m_output
            ]

        if not candidates:
            return None

        # Prefer specified provider
        if prefer_provider:
            provider_matches = [m for m in candidates if m.provider == prefer_provider]
            if provider_matches:
                candidates = provider_matches

        # Sort by latency (local models typically faster)
        if prefer_low_latency:
            candidates.sort(key=lambda m: m.latency_ms or float('inf'))

        return candidates[0] if candidates else None

    def get_provider_models(self, provider: str) -> List[ModelMetadata]:
        """Get all models from a specific provider."""
        return [m for m in self._models.values() if m.provider == provider and m.enabled]
