from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from cloakbrowser import launch, BrowserContext

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages CloakBrowser lifecycle — launch, context, teardown."""

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None,
        viewport: tuple[int, int] = (1920, 1080),
    ):
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent
        self.viewport = viewport
        self._context: Optional[BrowserContext] = None

    def start(self) -> BrowserContext:
        """Launch CloakBrowser and return a browser context."""
        logger.info("Launching CloakBrowser (headless=%s, proxy=%s)", self.headless, self.proxy or "none")
        args = {
            "headless": self.headless,
            "viewport": self.viewport,
            "stealth": True,
        }
        if self.proxy:
            args["proxy"] = self.proxy
        if self.user_agent:
            args["user_agent"] = self.user_agent

        browser = launch(**args)
        self._context = browser.default_context
        logger.info("CloakBrowser ready")
        return self._context

    def stop(self):
        """Close the browser context."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                logger.warning("Error closing browser context", exc_info=True)
            self._context = None
            logger.info("CloakBrowser closed")

    @contextmanager
    def context(self) -> Iterator[BrowserContext]:
        """Context manager for safe browser lifecycle."""
        ctx = self.start()
        try:
            yield ctx
        finally:
            self.stop()

    def new_page(self):
        """Get a new page from the context."""
        if not self._context:
            self.start()
        return self._context.new_page()

    @staticmethod
    def stealth_navigate(page, url: str, timeout: int = 30) -> str:
        """Navigate with stealth headers and return page content."""
        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        logger.debug("Navigating to %s", url)
        page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
        time.sleep(1.5)
        return page.content()
