"""Windows UIA (UI Automation) for application control."""

from typing import List, Optional, Dict, Any, Tuple
import logging

try:
    from pywinauto import Application, Desktop
    from pywinauto.controls.win32_controls import WindowSpecification
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    WindowSpecification = None

logger = logging.getLogger(__name__)


class UIAutomation:
    """Windows UI Automation (UIA) for app control."""

    def __init__(self):
        if not PYWINAUTO_AVAILABLE:
            logger.warning("pywinauto not installed. Install with: pip install pywinauto")

    def find_window(self, title: Optional[str] = None, class_name: Optional[str] = None) -> Optional[Any]:
        """Find a window by title or class name."""
        if not PYWINAUTO_AVAILABLE:
            return None

        try:
            desktop = Desktop(backend="uia")
            if title:
                windows = desktop.windows(title=title)
            elif class_name:
                windows = desktop.windows(class_name=class_name)
            else:
                return None

            return windows[0] if windows else None
        except Exception as e:
            logger.error(f"Window search failed: {e}")
            return None

    def get_window_text(self, window: Any) -> Optional[str]:
        """Get window title/text."""
        try:
            return window.window_text()
        except Exception as e:
            logger.error(f"Failed to get window text: {e}")
            return None

    def get_window_rect(self, window: Any) -> Optional[Tuple[int, int, int, int]]:
        """Get window coordinates (left, top, right, bottom)."""
        try:
            rect = window.rectangle()
            return (rect.left, rect.top, rect.right, rect.bottom)
        except Exception as e:
            logger.error(f"Failed to get window rect: {e}")
            return None

    def find_element_by_name(self, window: Any, name: str) -> Optional[Any]:
        """Find UI element by name/label."""
        try:
            return window.child_window(title=name)
        except Exception as e:
            logger.error(f"Element search failed: {e}")
            return None

    def find_elements_by_class(self, window: Any, class_name: str) -> List[Any]:
        """Find all UI elements of a class."""
        try:
            return window.children(class_name=class_name)
        except Exception as e:
            logger.error(f"Element search failed: {e}")
            return []

    def click_element(self, element: Any) -> bool:
        """Click a UI element."""
        try:
            element.click()
            logger.info(f"Clicked element: {element}")
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    def send_keys_to_element(self, element: Any, text: str) -> bool:
        """Send text to a UI element (input field)."""
        try:
            element.set_focus()
            element.type_keys(text)
            logger.info(f"Sent keys to element: {text}")
            return True
        except Exception as e:
            logger.error(f"Send keys failed: {e}")
            return False

    def get_element_value(self, element: Any) -> Optional[str]:
        """Get element text/value."""
        try:
            return element.window_text()
        except Exception as e:
            logger.error(f"Failed to get element value: {e}")
            return None

    def is_element_visible(self, element: Any) -> bool:
        """Check if element is visible."""
        try:
            return element.is_visible()
        except Exception as e:
            logger.error(f"Visibility check failed: {e}")
            return False

    def list_child_elements(self, window: Any) -> List[Dict[str, Any]]:
        """List all child elements of a window."""
        try:
            children = window.children()
            result = []
            for child in children:
                result.append({
                    "name": child.window_text(),
                    "class": child.class_name(),
                    "visible": child.is_visible(),
                    "enabled": child.is_enabled(),
                })
            return result
        except Exception as e:
            logger.error(f"Failed to list children: {e}")
            return []
