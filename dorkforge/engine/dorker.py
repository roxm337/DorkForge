from __future__ import annotations

import logging
import time
from typing import Callable, Optional
from urllib.parse import parse_qs, unquote, urlparse, urlunparse

from bs4 import BeautifulSoup

from dorkforge.engine.browser import BrowserManager
from dorkforge.models.result import DorkResult

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]


class DorkEngine:
    """Core dorking engine — runs Google searches via CloakBrowser."""

    BASE_URL = "https://www.google.com/search"
    BLOCKED_HOSTS = {
        "accounts.google.com", "maps.google.com", "policies.google.com",
        "support.google.com", "translate.google.com", "webcache.googleusercontent.com",
    }
    # These are information sources, not candidate systems. Excluding them at
    # collection time keeps the triage queue focused on externally reachable
    # hosts rather than advisory pages, PoCs, social posts, or documentation.
    REFERENCE_DOMAINS = {
        "github.com", "gitlab.com", "bitbucket.org", "gist.github.com",
        "reddit.com", "x.com", "twitter.com", "facebook.com", "instagram.com",
        "linkedin.com", "youtube.com", "tiktok.com",
        "wordpress.org", "wpmudev.com", "wp-kama.com",
        "stackoverflow.com", "stackexchange.com",
        "hackerone.com", "bugcrowd.com", "exploit-db.com", "packetstormsecurity.com",
        "wordfence.com", "rapid7.com", "tenable.com", "qualys.com", "cloudflare.com",
        "cve.org", "nvd.nist.gov", "mitre.org", "cisa.gov",
    }

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

                for u, title in self._parse_result_items(html):
                    if u not in seen_urls:
                        seen_urls.add(u)
                        results.append(DorkResult(url=u, title=title, dork=dork))

                if p < self.pages - 1:
                    time.sleep(self.delay)

        logger.info("Dork complete — %d unique results", len(results))
        return self._filter_scope(results)

    def _encode(self, dork: str) -> str:
        from urllib.parse import quote
        return quote(dork)

    def _parse_results(self, html: str, dork: str) -> list[str]:
        """Return verified organic-result URLs from Google SERP HTML.

        Kept as a small public helper for callers that only need URLs.  Unlike
        the prior implementation, it never falls back to every absolute link
        on the page; those links are Google navigation, account, map, and
        translation controls rather than search results.
        """
        return [url for url, _ in self._parse_result_items(html)]

    def _parse_result_items(self, html: str) -> list[tuple[str, str]]:
        """Extract only anchors that contain a Google organic result heading."""
        results: list[tuple[str, str]] = []
        soup = BeautifulSoup(html, "html.parser")

        # Google has changed its outer DOM several times, but an organic
        # result consistently exposes a heading inside a clickable anchor.
        for heading in soup.find_all("h3"):
            anchor = heading.find_parent("a", href=True)
            if not anchor:
                continue
            clean = self._normalise_result_url(anchor["href"])
            if clean:
                results.append((clean, heading.get_text(" ", strip=True)))

        seen: set[str] = set()
        deduped: list[tuple[str, str]] = []
        for url, title in results:
            if url not in seen:
                seen.add(url)
                deduped.append((url, title))

        if not deduped:
            logger.warning("No organic result anchors found; refusing to export SERP navigation links")
        return deduped

    @classmethod
    def _normalise_result_url(cls, href: str) -> Optional[str]:
        """Unwrap a Google redirect and reject non-result / Google-owned URLs."""
        if href.startswith("/"):
            href = f"https://www.google.com{href}"

        parsed = urlparse(href)
        if parsed.netloc.endswith("google.com") and parsed.path == "/url":
            target = parse_qs(parsed.query).get("q", parse_qs(parsed.query).get("url", [""]))[0]
            href = unquote(target)
            parsed = urlparse(href)

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        if cls._is_google_owned(parsed.hostname) or cls._is_reference_source(parsed.hostname):
            return None

        # Fragments are presentation-only and make the same target look
        # unique. Keep query strings because dorks often intentionally match
        # a query parameter or REST route.
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/") or "/", "", parsed.query, ""))

    @classmethod
    def _is_google_owned(cls, hostname: str) -> bool:
        host = hostname.lower().strip(".")
        return (
            host in cls.BLOCKED_HOSTS
            or host.endswith(".google.com")
            or host.startswith("google.")
            or ".google." in host
            or host.endswith(("googleusercontent.com", "gstatic.com", "googleapis.com"))
        )

    @classmethod
    def _is_reference_source(cls, hostname: str) -> bool:
        host = hostname.lower().strip(".")
        return any(host == domain or host.endswith(f".{domain}") for domain in cls.REFERENCE_DOMAINS)

    def _filter_scope(self, results: list[DorkResult]) -> list[DorkResult]:
        if not self.scope_domains:
            return results
        filtered: list[DorkResult] = []
        for r in results:
            hostname = urlparse(r.url).hostname or ""
            if any(self._domain_in_scope(hostname, scope) for scope in self.scope_domains):
                filtered.append(r)
        logger.info("Scope filter: %d/%d results kept", len(filtered), len(results))
        return filtered

    @staticmethod
    def _domain_in_scope(hostname: str, scope: str) -> bool:
        scope = scope.lower().strip().lstrip(".")
        hostname = hostname.lower().strip(".")
        return hostname == scope or hostname.endswith(f".{scope}")
