from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from cloakbrowser import launch

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages CloakBrowser lifecycle — launch, context, teardown."""

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
    ):
        self.headless = headless
        self.proxy = proxy
        self._browser = None
        self._context = None

    def start(self):
        """Launch CloakBrowser and return a browser context."""
        logger.info("Launching CloakBrowser (headless=%s, proxy=%s)", self.headless, self.proxy or "none")
        kwargs = {
            "headless": self.headless,
            "stealth_args": True,
        }
        if self.proxy:
            kwargs["proxy"] = self.proxy

        self._browser = launch(**kwargs)
        self._context = self._browser.new_context()
        logger.info("CloakBrowser ready")
        return self._context

    def stop(self):
        """Close the browser."""
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                logger.warning("Error closing browser", exc_info=True)
            self._browser = None
            self._context = None
            logger.info("CloakBrowser closed")

    @contextmanager
    def context(self):
        """Context manager for safe browser lifecycle."""
        self.start()
        try:
            yield self._context
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
