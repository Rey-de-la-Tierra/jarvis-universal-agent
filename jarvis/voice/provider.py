"""Abstract voice provider interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class VoiceProfile:
    """Voice configuration."""
    name: str
    language: str = "en-US"
    rate: float = 1.0  # 0.5-2.0
    volume: float = 1.0  # 0.0-1.0
    gender: Optional[str] = None  # "male", "female", or None


class VoiceProvider(ABC):
    """Abstract interface for voice I/O providers."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize provider."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown provider."""
        pass

    @abstractmethod
    async def transcribe(self, audio_file: str, language: str = "en-US") -> Optional[str]:
        """Transcribe audio file to text."""
        pass

    @abstractmethod
    async def synthesize(self, text: str, voice_profile: Optional[VoiceProfile] = None) -> Optional[str]:
        """Synthesize text to speech.
        
        Returns:
            Path to generated audio file, or None on failure
        """
        pass

    @abstractmethod
    def list_voices(self) -> List[VoiceProfile]:
        """List available voices."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available/connected."""
        pass
