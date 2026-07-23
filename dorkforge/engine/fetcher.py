from __future__ import annotations

import logging
import re
import ssl
import urllib.request
import urllib.error
from typing import Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


class PageFetcher:
    """Lightweight HTTP fetcher for enrichment (no browser needed)."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def fetch(self, url: str) -> Optional[str]:
        """Fetch page HTML. Returns None on failure."""
        try:
            req = urllib.request.Request(url, headers=self.HEADERS, method="GET")
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                return html
        except Exception as e:
            logger.debug("fetch failed for %s: %s", url, e)
            return None

    def status_code(self, url: str) -> int:
        """GET the URL and return the HTTP status code."""
        try:
            req = urllib.request.Request(url, headers=self.HEADERS, method="HEAD")
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=self.timeout) as resp:
                return resp.status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            return 0

    @staticmethod
    def extract_title(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else ""

    @staticmethod
    def detect_tech(html: str) -> list[str]:
        tech = []
        patterns = {
            "WordPress": r"/wp-(content|includes|admin)/",
            "Drupal": r"/sites/default/",
            "Joomla": r"/components/com_",
            "Laravel": r"csrf-token\s*content=",
            "React": r"(react\.js|react-dom|__NEXT_DATA__)",
            "Vue": r"vue\.(js|min\.js)",
            "Angular": r"angular\.(js|min\.js)",
            "jQuery": r"jquery",
            "Bootstrap": r"bootstrap\.(min\.)?(css|js)",
            "nginx": r"nginx",
            "Apache": r"apache",
            "Cloudflare": r"cloudflare",
            "PHP": r"\.php",
            "ASP.NET": r"__VIEWSTATE",
            "Django": r"csrfmiddlewaretoken",
            "Flask": r"flask",
        }
        for name, pattern in patterns.items():
            if re.search(pattern, html, re.I):
                tech.append(name)
        return tech

    @staticmethod
    def extract_endpoints(html: str, base_url: str) -> list[str]:
        endpoints = set()
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "link", "a", "form"]):
            attr = ""
            if tag.name == "a":
                attr = tag.get("href", "")
            elif tag.name == "form":
                attr = tag.get("action", "")
            elif tag.name == "script":
                attr = tag.get("src", "")
            elif tag.name == "link":
                attr = tag.get("href", "")

            if not attr or attr.startswith(("#", "javascript:", "data:", "mailto:")):
                continue

            full = urljoin(base_url, attr)
            parsed = urlparse(full)
            if parsed.scheme in ("http", "https"):
                path = parsed.path.rstrip("/")
                if path and len(path) > 1:
                    endpoints.add(path)
        return sorted(endpoints)

    @staticmethod
    def count_forms(html: str) -> int:
        return html.count("<form") if html else 0
