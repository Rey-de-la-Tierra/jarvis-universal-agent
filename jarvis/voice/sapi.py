"""Windows SAPI fallback for voice (TTS/STT)."""

from typing import Optional, List
import logging

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from jarvis.voice.provider import VoiceProvider, VoiceProfile

logger = logging.getLogger(__name__)


class SAPIVoiceProvider(VoiceProvider):
    """Windows SAPI voice provider (Text-to-Speech only initially)."""

    def __init__(self):
        self.tts_engine = None
        self.recognizer = None
        self.current_voice_profile = VoiceProfile("default", "en-US")

    async def initialize(self) -> bool:
        """Initialize SAPI."""
        try:
            if PYTTSX3_AVAILABLE:
                self.tts_engine = pyttsx3.init("sapi5")
                self.tts_engine.setProperty("rate", 150)
                self.tts_engine.setProperty("volume", 1.0)
                logger.info("SAPI TTS initialized")
            
            if SPEECH_RECOGNITION_AVAILABLE:
                self.recognizer = sr.Recognizer()
                logger.info("SAPI STT initialized")
            
            return True
        except Exception as e:
            logger.error(f"SAPI initialization failed: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown SAPI."""
        if self.tts_engine:
            self.tts_engine.stop()
        logger.info("SAPI shutdown")

    async def transcribe(self, audio_file: str, language: str = "en-US") -> Optional[str]:
        """Transcribe audio to text using SAPI."""
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.warning("speech_recognition not available")
            return None

        try:
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=language)
                logger.info(f"Transcribed: {text}")
                return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    async def synthesize(self, text: str, voice_profile: Optional[VoiceProfile] = None) -> Optional[str]:
        """Synthesize text to speech using SAPI.
        
        Returns:
            Audio file path, or None on failure
        """
        if not PYTTSX3_AVAILABLE:
            logger.warning("pyttsx3 not available")
            return None

        if voice_profile:
            self.current_voice_profile = voice_profile

        try:
            output_file = f"/tmp/speech_{hash(text)}.wav"
            self.tts_engine.setProperty("rate", 150 * self.current_voice_profile.rate)
            self.tts_engine.setProperty("volume", self.current_voice_profile.volume)
            
            self.tts_engine.save_to_file(text, output_file)
            self.tts_engine.runAndWait()
            
            logger.info(f"Speech synthesized: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return None

    def list_voices(self) -> List[VoiceProfile]:
        """List available SAPI voices."""
        if not PYTTSX3_AVAILABLE:
            return []

        try:
            voices = []
            for voice in self.tts_engine.getProperty("voices"):
                profile = VoiceProfile(
                    name=voice.name,
                    gender="male" if "male" in voice.name.lower() else "female"
                )
                voices.append(profile)
            return voices
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return [VoiceProfile("default", "en-US")]

    async def is_available(self) -> bool:
        """Check if SAPI is available."""
        return PYTTSX3_AVAILABLE or SPEECH_RECOGNITION_AVAILABLE
