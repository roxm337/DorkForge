from __future__ import annotations

import logging
import re
import time
from typing import Callable, Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from cloakbrowser import BrowserContext

from dorkforge.engine.browser import BrowserManager
from dorkforge.models.result import DorkResult

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]


class DorkEngine:
    """Core dorking engine — runs Google searches via CloakBrowser."""

    BASE_URL = "https://www.google.com/search"

    def __init__(
        self,
        headless: bool = True,
        pages: int = 2,
        delay: int = 4,
        proxy: Optional[str] = None,
        scope_domains: Optional[list[str]] = None,
    ):
        self.headless = headless
        self.pages = pages
        self.delay = delay
        self.proxy = proxy
        self.scope_domains = scope_domains or []
        self._browser: Optional[BrowserManager] = None

    def search(self, dork: str, progress_cb: Optional[ProgressCallback] = None) -> list[DorkResult]:
        """Execute a single dork query over N pages, return deduplicated results."""
        logger.info("Searching dork: %s (pages=%d, delay=%d)", dork, self.pages, self.delay)
        results: list[DorkResult] = []
        seen_urls: set[str] = set()

        self._browser = BrowserManager(headless=self.headless, proxy=self.proxy)
        with self._browser.context() as ctx:
            page = ctx.new_page()

            for p in range(self.pages):
                if progress_cb:
                    progress_cb(p + 1, self.pages, f"Page {p+1}/{self.pages} — {dork[:60]}")

                start = p * 10
                url = f"{self.BASE_URL}?q={self._encode(dork)}&start={start}"
                logger.debug("Fetching page %d: %s", p + 1, url)

                try:
                    html = BrowserManager.stealth_navigate(page, url)
                except Exception as e:
                    logger.warning("Navigation failed on page %d: %s", p + 1, e)
                    time.sleep(self.delay)
                    continue

                urls = self._parse_results(html, dork)
                for u in urls:
                    if u not in seen_urls:
                        seen_urls.add(u)
                        results.append(DorkResult(url=u, dork=dork))

                if p < self.pages - 1:
                    time.sleep(self.delay)

        logger.info("Dork complete — %d unique results", len(results))
        return self._filter_scope(results)

    def _encode(self, dork: str) -> str:
        import urllib.parse
        return urllib.parse.quote(dork)

    def _parse_results(self, html: str, dork: str) -> list[str]:
        """Extract result URLs from Google SERP HTML."""
        urls: list[str] = []
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/url?q="):
                match = re.search(r"/url\?q=([^&]+)", href)
                if match:
                    url = urllib.parse.unquote(match.group(1))
                    if url.startswith(("http://", "https://")):
                        urls.append(url)

        if not urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("http://", "https://")):
                    urls.append(href)

        seen: set[str] = set()
        deduped: list[str] = []
        for u in urls:
            clean = u.rstrip("/")
            if clean not in seen:
                seen.add(clean)
                deduped.append(clean)

        return deduped

    def _filter_scope(self, results: list[DorkResult]) -> list[DorkResult]:
        if not self.scope_domains:
            return results
        filtered: list[DorkResult] = []
        for r in results:
            domain = r.domain
            if any(sd in domain for sd in self.scope_domains):
                filtered.append(r)
        logger.info("Scope filter: %d/%d results kept", len(filtered), len(results))
        return filtered
