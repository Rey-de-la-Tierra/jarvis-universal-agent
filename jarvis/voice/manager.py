"""Unified voice interface with automatic fallback."""

from typing import Optional, List, Dict, Any
import logging

from jarvis.voice.provider import VoiceProvider, VoiceProfile
from jarvis.voice.voicestudio import VoiceStudioProvider
from jarvis.voice.sapi import SAPIVoiceProvider

logger = logging.getLogger(__name__)


class VoiceManager:
    """Manages voice I/O with automatic fallback chain."""

    def __init__(self):
        self.providers: List[VoiceProvider] = [
            VoiceStudioProvider(),
            SAPIVoiceProvider(),
        ]
        self.active_provider: Optional[VoiceProvider] = None
        self.fallback_chain: List[VoiceProvider] = []

    async def initialize(self) -> bool:
        """Initialize voice system with fallback chain."""
        for provider in self.providers:
            try:
                if await provider.initialize():
                    self.active_provider = provider
                    logger.info(f"Voice provider initialized: {provider.__class__.__name__}")
                    self.fallback_chain.append(provider)
            except Exception as e:
                logger.warning(f"Failed to initialize {provider.__class__.__name__}: {e}")

        if not self.active_provider:
            logger.error("No voice providers available")
            return False

        return True

    async def shutdown(self) -> None:
        """Shutdown all voice providers."""
        for provider in self.providers:
            try:
                await provider.shutdown()
            except Exception as e:
                logger.error(f"Shutdown error: {e}")

    async def transcribe(
        self,
        audio_file: str,
        language: str = "en-US",
        confidence_threshold: float = 0.8,
    ) -> Optional[str]:
        """Transcribe audio with automatic fallback.
        
        Args:
            audio_file: Path to audio file
            language: Language code (e.g., 'en-US')
            confidence_threshold: If confidence < threshold, ask for clarification
            
        Returns:
            Transcribed text, or None if all providers fail
        """
        for provider in self.fallback_chain:
            try:
                text = await provider.transcribe(audio_file, language)
                if text:
                    logger.info(f"Transcribed via {provider.__class__.__name__}: {text}")
                    return text
            except Exception as e:
                logger.warning(f"Transcription failed on {provider.__class__.__name__}: {e}")
                continue

        logger.error("All transcription providers failed")
        return None

    async def synthesize(
        self,
        text: str,
        voice_profile: Optional[VoiceProfile] = None,
    ) -> Optional[str]:
        """Synthesize speech with automatic fallback.
        
        Args:
            text: Text to synthesize
            voice_profile: Optional voice configuration
            
        Returns:
            Path to generated audio file, or None if all providers fail
        """
        for provider in self.fallback_chain:
            try:
                audio_file = await provider.synthesize(text, voice_profile)
                if audio_file:
                    logger.info(f"Synthesized via {provider.__class__.__name__}: {audio_file}")
                    return audio_file
            except Exception as e:
                logger.warning(f"Synthesis failed on {provider.__class__.__name__}: {e}")
                continue

        logger.error("All synthesis providers failed")
        return None

    def list_voices(self) -> List[VoiceProfile]:
        """List voices from active provider."""
        if self.active_provider:
            return self.active_provider.list_voices()
        return []

    def set_voice_profile(self, voice_profile: VoiceProfile) -> None:
        """Set the active voice profile."""
        if self.active_provider:
            # Store in provider for next synthesis
            self.active_provider.current_voice_profile = voice_profile
            logger.info(f"Voice profile set: {voice_profile.name}")

    async def is_available(self) -> bool:
        """Check if any voice provider is available."""
        if not self.active_provider:
            return False
        return await self.active_provider.is_available()
