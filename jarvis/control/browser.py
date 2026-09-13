"""Browser automation via Chrome DevTools Protocol (CDP)."""

from typing import List, Optional, Dict, Any
import asyncio
import json
import logging

try:
    from pyppeteer import launch, Browser
    PYPPETEER_AVAILABLE = True
except ImportError:
    PYPPETEER_AVAILABLE = False
    Browser = None

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Browser control via Chrome DevTools Protocol."""

    def __init__(self, headless: bool = False, devtools_port: int = 9222):
        self.headless = headless
        self.devtools_port = devtools_port
        self.browser: Optional[Browser] = None
        self.page = None

    async def launch(self) -> bool:
        """Launch browser."""
        if not PYPPETEER_AVAILABLE:
            logger.warning("pyppeteer not installed. Install with: pip install pyppeteer")
            return False

        try:
            self.browser = await launch(
                headless=self.headless,
                args=[f"--remote-debugging-port={self.devtools_port}"]
            )
            self.page = await self.browser.newPage()
            logger.info(f"Browser launched on port {self.devtools_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            return False

    async def close(self) -> None:
        """Close browser."""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

    async def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        if not self.page:
            return False

        try:
            await self.page.goto(url, {"waitUntil": "networkidle2"})
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def click(self, selector: str) -> bool:
        """Click an element by CSS selector."""
        if not self.page:
            return False

        try:
            await self.page.click(selector)
            logger.info(f"Clicked: {selector}")
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    async def type_text(self, selector: str, text: str, delay_ms: int = 100) -> bool:
        """Type text into an input field."""
        if not self.page:
            return False

        try:
            await self.page.type(selector, text, {"delay": delay_ms})
            logger.info(f"Typed into {selector}: {text}")
            return True
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False

    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content of an element."""
        if not self.page:
            return None

        try:
            text = await self.page.evaluate(f"document.querySelector('{selector}').textContent")
            return text
        except Exception as e:
            logger.error(f"Get text failed: {e}")
            return None

    async def execute_script(self, script: str) -> Any:
        """Execute arbitrary JavaScript."""
        if not self.page:
            return None

        try:
            result = await self.page.evaluate(script)
            logger.info(f"Script executed")
            return result
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return None

    async def screenshot(self, filename: str = "page.png") -> Optional[str]:
        """Take page screenshot."""
        if not self.page:
            return None

        try:
            await self.page.screenshot({"path": filename})
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    async def wait_for_selector(self, selector: str, timeout_ms: int = 5000) -> bool:
        """Wait for an element to appear."""
        if not self.page:
            return False

        try:
            await self.page.waitForSelector(selector, {"timeout": timeout_ms})
            logger.info(f"Element appeared: {selector}")
            return True
        except Exception as e:
            logger.error(f"Wait failed: {e}")
            return False

    async def get_page_content(self) -> Optional[str]:
        """Get full page HTML."""
        if not self.page:
            return None

        try:
            return await self.page.content()
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return None
