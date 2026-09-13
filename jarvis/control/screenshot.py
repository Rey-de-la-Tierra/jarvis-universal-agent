"""Screen capture and OCR capabilities."""

import asyncio
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
import logging

try:
    from PIL import ImageGrab, Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScreenCapture:
    """Screen capture and OCR."""

    def __init__(self, screenshot_dir: Optional[Path] = None):
        if not PILLOW_AVAILABLE:
            raise RuntimeError("Pillow not installed. Install with: pip install pillow")

        self.screenshot_dir = screenshot_dir or Path.home() / ".jarvis" / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def capture_screen(self, filename: Optional[str] = None) -> Optional[Path]:
        """Capture full screen to PNG.
        
        Args:
            filename: Optional custom filename (default: timestamp)
            
        Returns:
            Path to saved screenshot, or None on failure
        """
        try:
            screenshot = ImageGrab.grab()
            if filename is None:
                filename = f"screenshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.screenshot_dir / filename
            screenshot.save(filepath)
            logger.info(f"Screenshot captured: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None

    def capture_region(self, x: int, y: int, width: int, height: int, filename: Optional[str] = None) -> Optional[Path]:
        """Capture a specific screen region.
        
        Args:
            x, y: Top-left corner coordinates
            width, height: Region dimensions
            filename: Optional custom filename
            
        Returns:
            Path to saved screenshot, or None on failure
        """
        try:
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox=bbox)
            if filename is None:
                filename = f"region_{x}_{y}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.screenshot_dir / filename
            screenshot.save(filepath)
            logger.info(f"Region screenshot captured: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to capture region: {e}")
            return None

    def extract_text(self, image_path: Path, language: str = "eng") -> Optional[str]:
        """Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            language: Tesseract language (default: 'eng')
            
        Returns:
            Extracted text, or None on failure
        """
        if not TESSERACT_AVAILABLE:
            logger.warning("pytesseract not installed. Install with: pip install pytesseract")
            return None

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=language)
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None

    def find_text_in_screenshot(self, text: str, screenshot_path: Optional[Path] = None) -> Optional[List[Tuple[int, int, int, int]]]:
        """Find text bounding boxes in screenshot.
        
        Args:
            text: Text to find
            screenshot_path: Optional specific screenshot (default: latest)
            
        Returns:
            List of bounding boxes, or None if not found
        """
        if not TESSERACT_AVAILABLE:
            return None

        try:
            if screenshot_path is None:
                # Use most recent screenshot
                screenshots = sorted(self.screenshot_dir.glob("screenshot_*.png"))
                if not screenshots:
                    return None
                screenshot_path = screenshots[-1]

            image = Image.open(screenshot_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # Find matching text
            matches = []
            for i, word in enumerate(data["text"]):
                if text.lower() in word.lower():
                    x = data["left"][i]
                    y = data["top"][i]
                    w = data["width"][i]
                    h = data["height"][i]
                    matches.append((x, y, w, h))

            return matches if matches else None
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return None

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen resolution."""
        try:
            screenshot = ImageGrab.grab()
            width, height = screenshot.size
            return (width, height)
        except Exception as e:
            logger.error(f"Failed to get screen size: {e}")
            return (1920, 1080)  # Fallback default
