"""Unified action executor: keyboard, mouse, and system actions."""

from typing import Optional, Tuple, List, Dict, Any
from enum import Enum
import time
import logging

try:
    from pynput.mouse import Mouse, Button
    from pynput.keyboard import Controller as KeyboardController, Key
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    Mouse = None
    KeyboardController = None

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions JARVIS can execute."""
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"
    MOUSE_RIGHT_CLICK = "mouse_right_click"
    MOUSE_SCROLL = "mouse_scroll"
    KEYBOARD_TYPE = "keyboard_type"
    KEYBOARD_HOTKEY = "keyboard_hotkey"
    SCREENSHOT = "screenshot"
    WINDOW_FOCUS = "window_focus"
    WINDOW_CLOSE = "window_close"
    CLIPBOARD_COPY = "clipboard_copy"
    CLIPBOARD_PASTE = "clipboard_paste"


class ActionExecutor:
    """Executes computer control actions."""

    def __init__(self):
        if not PYNPUT_AVAILABLE:
            logger.warning("pynput not installed. Install with: pip install pynput")
        self.mouse = Mouse()
        self.keyboard = KeyboardController()
        self.last_action_time = time.time()

    def mouse_move(self, x: int, y: int, duration: float = 0.5, human_like: bool = True) -> bool:
        """Move mouse to coordinates.
        
        Args:
            x, y: Target coordinates
            duration: Movement duration (seconds)
            human_like: Use human-like curve motion (future)
        """
        if not PYNPUT_AVAILABLE:
            return False

        try:
            self.mouse.position = (x, y)
            time.sleep(min(duration, 0.1))  # Keep it fast
            logger.info(f"Mouse moved to: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return False

    def mouse_click(self, x: int, y: int, button: str = "left") -> bool:
        """Click mouse at coordinates."""
        if not PYNPUT_AVAILABLE:
            return False

        try:
            self.mouse.position = (x, y)
            button_obj = Button.left if button == "left" else Button.right
            self.mouse.click(button_obj)
            logger.info(f"Mouse clicked at: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Mouse click failed: {e}")
            return False

    def mouse_double_click(self, x: int, y: int) -> bool:
        """Double-click mouse at coordinates."""
        if not PYNPUT_AVAILABLE:
            return False

        try:
            self.mouse.position = (x, y)
            self.mouse.click(Button.left, 2)
            logger.info(f"Double-clicked at: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Double-click failed: {e}")
            return False

    def keyboard_type(self, text: str, interval: float = 0.05) -> bool:
        """Type text.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes (seconds)
        """
        if not PYNPUT_AVAILABLE:
            return False

        try:
            self.keyboard.type(text)
            logger.info(f"Typed: {text}")
            return True
        except Exception as e:
            logger.error(f"Keyboard type failed: {e}")
            return False

    def keyboard_hotkey(self, *keys: str) -> bool:
        """Execute keyboard hotkey (e.g., Ctrl+C, Alt+Tab).
        
        Args:
            keys: Key names (e.g., 'ctrl', 'c') or special keys ('enter', 'escape')
        """
        if not PYNPUT_AVAILABLE:
            return False

        try:
            key_map = {
                "ctrl": Key.ctrl,
                "alt": Key.alt,
                "shift": Key.shift,
                "enter": Key.enter,
                "escape": Key.esc,
                "tab": Key.tab,
                "backspace": Key.backspace,
                "delete": Key.delete,
                "home": Key.home,
                "end": Key.end,
                "pgup": Key.page_up,
                "pgdn": Key.page_down,
            }

            with self.keyboard.pressed(*[key_map.get(k, k) for k in keys[:-1]]):
                self.keyboard.press(key_map.get(keys[-1], keys[-1]))
                self.keyboard.release(key_map.get(keys[-1], keys[-1]))

            logger.info(f"Hotkey executed: {'+'.join(keys)}")
            return True
        except Exception as e:
            logger.error(f"Hotkey failed: {e}")
            return False

    def execute_action(
        self,
        action_type: ActionType,
        **kwargs
    ) -> bool:
        """Execute a named action."""
        if action_type == ActionType.MOUSE_MOVE:
            return self.mouse_move(kwargs["x"], kwargs["y"])
        elif action_type == ActionType.MOUSE_CLICK:
            return self.mouse_click(kwargs["x"], kwargs["y"])
        elif action_type == ActionType.MOUSE_DOUBLE_CLICK:
            return self.mouse_double_click(kwargs["x"], kwargs["y"])
        elif action_type == ActionType.KEYBOARD_TYPE:
            return self.keyboard_type(kwargs["text"])
        elif action_type == ActionType.KEYBOARD_HOTKEY:
            return self.keyboard_hotkey(*kwargs["keys"])
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return False
