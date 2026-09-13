"""VoiceStudio integration for voice I/O."""

from typing import Optional, List
import logging
import json
import asyncio
import subprocess
from pathlib import Path

from jarvis.voice.provider import VoiceProvider, VoiceProfile

logger = logging.getLogger(__name__)


class VoiceStudioProvider(VoiceProvider):
    """Integration with VoiceStudio for voice I/O.
    
    Assumes VoiceStudio is running locally with API available.
    """

    def __init__(self, api_endpoint: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.available = False
        self.current_voice_profile = VoiceProfile("default", "en-US")

    async def initialize(self) -> bool:
        """Initialize VoiceStudio connection."""
        try:
            # Probe VoiceStudio availability
            self.available = await self._probe_availability()
            if self.available:
                logger.info(f"VoiceStudio connected: {self.api_endpoint}")
            else:
                logger.warning(f"VoiceStudio unavailable at {self.api_endpoint}")
            return self.available
        except Exception as e:
            logger.error(f"VoiceStudio initialization failed: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown VoiceStudio connection."""
        logger.info("VoiceStudio connection closed")

    async def _probe_availability(self) -> bool:
        """Check if VoiceStudio API is reachable."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_endpoint}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def transcribe(self, audio_file: str, language: str = "en-US") -> Optional[str]:
        """Transcribe audio using VoiceStudio."""
        if not self.available:
            logger.warning("VoiceStudio not available")
            return None

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                with open(audio_file, "rb") as f:
                    files = {"audio": f}
                    response = await client.post(
                        f"{self.api_endpoint}/transcribe",
                        files=files,
                        params={"language": language},
                        headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("text")
        except Exception as e:
            logger.error(f"VoiceStudio transcription failed: {e}")
        return None

    async def synthesize(self, text: str, voice_profile: Optional[VoiceProfile] = None) -> Optional[str]:
        """Synthesize speech using VoiceStudio.
        
        Returns:
            Audio file path, or None on failure
        """
        if not self.available:
            logger.warning("VoiceStudio not available")
            return None

        if voice_profile:
            self.current_voice_profile = voice_profile

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                payload = {
                    "text": text,
                    "voice": self.current_voice_profile.name,
                    "language": self.current_voice_profile.language,
                    "rate": self.current_voice_profile.rate,
                    "volume": self.current_voice_profile.volume,
                }
                response = await client.post(
                    f"{self.api_endpoint}/synthesize",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                )
                if response.status_code == 200:
                    # Save audio file
                    output_file = f"/tmp/speech_{hash(text)}.wav"
                    with open(output_file, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Speech synthesized: {output_file}")
                    return output_file
        except Exception as e:
            logger.error(f"VoiceStudio synthesis failed: {e}")
        return None

    def list_voices(self) -> List[VoiceProfile]:
        """List available VoiceStudio voices."""
        # TODO: Fetch from VoiceStudio API
        return [
            VoiceProfile("default", "en-US"),
            VoiceProfile("male", "en-US", gender="male"),
            VoiceProfile("female", "en-US", gender="female"),
        ]

    async def is_available(self) -> bool:
        """Check if VoiceStudio is available."""
        return await self._probe_availability()
