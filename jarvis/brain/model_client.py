"""Unified LLM client abstracting multiple providers."""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """Unified message format."""
    role: str  # "user", "assistant", "system"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMResponse:
    """Unified response format."""
    content: str
    model_used: str
    stop_reason: str  # "end_turn", "tool_calls", "max_tokens", etc.
    tokens_used: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[float] = None


class BaseLLMClient:
    """Base class for LLM client implementations."""

    def __init__(self, api_key: str, model_name: str, endpoint: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = endpoint

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate a completion."""
        raise NotImplementedError

    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion."""
        raise NotImplementedError


class UnifiedLLMClient:
    """Unified client that routes to provider-specific implementations."""

    def __init__(self, registry: Any):  # ModelRegistry
        self.registry = registry
        self._clients: Dict[str, BaseLLMClient] = {}

    def register_client(self, provider: str, client: BaseLLMClient) -> None:
        """Register a provider-specific client."""
        self._clients[provider] = client

    def _get_client(self, model_name: str) -> BaseLLMClient:
        """Get the appropriate client for a model."""
        metadata = self.registry.get_model(model_name)
        if not metadata:
            raise ValueError(f"Unknown model: {model_name}")

        provider = metadata.provider
        if provider not in self._clients:
            raise ValueError(f"No client registered for provider: {provider}")

        return self._clients[provider]

    async def generate(
        self,
        model_name: str,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate a completion with the specified model."""
        client = self._get_client(model_name)
        return await client.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            json_mode=json_mode,
        )

    async def stream_generate(
        self,
        model_name: str,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion with the specified model."""
        client = self._get_client(model_name)
        async for chunk in client.stream_generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        ):
            yield chunk

    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Optional[float]:
        """Estimate cost for a request."""
        metadata = self.registry.get_model(model_name)
        if not metadata:
            return None
        return metadata.estimate_cost(input_tokens, output_tokens)
