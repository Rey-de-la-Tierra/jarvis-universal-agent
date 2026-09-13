"""JARVIS Universal Agent - Autonomous OS automation with any LLM."""

__version__ = "0.1.0"
__author__ = "Rey-de-la-Tierra"
__description__ = "Privacy-first, reliability-obsessed, vendor-agnostic OS automation"

from jarvis.core.config import Config
from jarvis.core.logger import Logger
from jarvis.core.state import GlobalState

__all__ = ["Config", "Logger", "GlobalState"]
