"""CVE-specific target probler — uses CloakBrowser to check live targets."""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional, Callable
from urllib.parse import urljoin, urlparse

from dorkforge.engine.browser import BrowserManager
from dorkforge.models.result import DorkResult

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]


@dataclass
class CVEProbe:
    cve_id: str
    name: str
    endpoints: list[str] = field(default_factory=list)
    fingerprint: dict[str, list[str]] = field(default_factory=dict)
    auth_required: bool = False
    severity: str = "Critical"

    def match_status(self, status: int) -> str:
        if status == 200:
            return "VULNERABLE"
        if status == 403:
            return "EXISTS_BLOCKED"
        if status == 404:
            return "NOT_FOUND"
        if status in (500, 502, 503):
            return "SERVER_ERROR"
        if status == 0:
            return "UNREACHABLE"
        return f"HTTP_{status}"


# Probe definitions keyed by CVE short name (matched against dork category names)
PROBE_DEFS: dict[str, CVEProbe] = {
    "sharepoint": CVEProbe(
        cve_id="CVE-2026-50522 / CVE-2026-58644",
        name="SharePoint Deserialization RCE",
        endpoints=[
            "/_trust/default.aspx",
            "/_layouts/15/spcontnt.aspx",
            "/_vti_bin/webpartpages.asmx",
        ],
        fingerprint={
            "header": ["MicrosoftSharePointTeamServices", "SPRequestGuid", "SharePoint"],
            "body": ["SharePoint", "_spPageContextInfo", "SP.UI"],
        },
    ),
    "servicenow": CVEProbe(
        cve_id="CVE-2026-6875",
        name="ServiceNow Pre-Auth Sandbox Escape RCE",
        endpoints=[
            "/assessment_thanks.do",
            "/login.do",
            "/navpage.do",
        ],
        fingerprint={
            "body": ["servicenow", "glide", "sysparm", "now.nav"],
        },
    ),
    "wp2shell": CVEProbe(
        cve_id="CVE-2026-63030 / CVE-2026-60137",
        name="WordPress wp2shell RCE",
        endpoints=[
            "/wp-json/batch/v1",
            "/?rest_route=/batch/v1",
            "/wp-json/wp/v2/users",
        ],
        fingerprint={
            "body": ["generator\" content=\"WordPress 6.9", "generator\" content=\"WordPress 7.0"],
            "header": [],
        },
    ),
    "grav": CVEProbe(
        cve_id="CVE-2026-65008 / CVE-2026-65608",
        name="Grav CMS RCE",
        endpoints=[
            "/admin",
            "/admin/login",
            "/login",
        ],
        fingerprint={
            "body": ["Grav", "getgrav", "Admin Panel"],
        },
    ),
    "dbgate": CVEProbe(
        cve_id="CVE-2026-47668",
        name="DbGate Unauthenticated RCE",
        endpoints=[
            "/runners/start",
            "/login",
            "/api/status",
        ],
        fingerprint={
            "body": ["DbGate", "dbgate", "database manager"],
        },
    ),
    "nginx": CVEProbe(
        cve_id="CVE-2026-42533 / CVE-2026-42945",
        name="NGINX Rift",
        endpoints=[
            "/",
        ],
        fingerprint={
            "header": ["Server: nginx"],
            "body": ["Welcome to nginx"],
        },
    ),
    "laravel-mediable": CVEProbe(
        cve_id="CVE-2026-49972",
        name="Laravel-Mediable File Upload RCE",
        endpoints=[
            "/media/upload",
            "/",
        ],
        fingerprint={
            "body": ["Laravel", "MEDIA_UPLOAD", "mediable"],
        },
    ),
    "codeigniter": CVEProbe(
        cve_id="CVE-2026-48062",
        name="CodeIgniter Upload Bypass",
        endpoints=[
            "/public/uploads",
            "/",
        ],
        fingerprint={
            "body": ["CodeIgniter", "CI_VERSION"],
        },
    ),
    "cpanel": CVEProbe(
        cve_id="CVE-2026-41940",
        name="cPanel Auth Bypass",
        endpoints=[
            "/cpanel",
            "/:2083/",
        ],
        fingerprint={
            "body": ["cPanel", "WHM", "Web Host Manager"],
        },
    ),
    "pan-os": CVEProbe(
        cve_id="CVE-2026-0300",
        name="PAN-OS RCE",
        endpoints=[
            "/",
        ],
        fingerprint={
            "body": ["PAN-OS", "GlobalProtect"],
        },
    ),
    "nginx-ui": CVEProbe(
        cve_id="CVE-2026-33032",
        name="Nginx UI Missing Auth",
        endpoints=[
            "/",
            "/login",
        ],
        fingerprint={
            "body": ["Nginx UI", "Nginx Web UI"],
        },
    ),
    "ivanti": CVEProbe(
        cve_id="CVE-2026-6973",
        name="Ivanti EPMM RCE",
        endpoints=[
            "/mifs/user/login",
            "/",
        ],
        fingerprint={
            "body": ["Ivanti", "MobileIron"],
        },
    ),
    "exchange": CVEProbe(
        cve_id="Exchange CVEs",
        name="Exchange OWA",
        endpoints=[
            "/owa/auth/logon.aspx",
            "/ecp/login.aspx",
        ],
        fingerprint={
            "body": ["Outlook Web App", "Exchange", "logon"],
        },
    ),
}


def resolve_probe(category_name: str) -> Optional[CVEProbe]:
    """Match a dork category name to its probe definition."""
    cat = category_name.lower()
    for key, probe in PROBE_DEFS.items():
        if key in cat:
            return probe
    return None


@dataclass
class ProbeResult:
    url: str
    cve: str
    endpoint: str
    status: int
    body_snippet: str = ""
    verdict: str = "UNKNOWN"
    title: str = ""

    @property
    def is_interesting(self) -> bool:
        return self.verdict in ("VULNERABLE", "EXISTS_BLOCKED")


class ProbeEngine:
    """Probes URLs against CVE-specific endpoints using CloakBrowser."""

    def __init__(self, headless: bool = True, proxy: Optional[str] = None, timeout: int = 20):
        self.headless = headless
        self.proxy = proxy
        self.timeout = timeout
        self._page = None

    def _ensure_browser(self):
        if not self._page:
            bm = BrowserManager(headless=self.headless, proxy=self.proxy)
            ctx = bm.start()
            self._page = ctx.new_page()
            self._bm = bm

    def _close(self):
        if hasattr(self, '_bm') and self._bm:
            try:
                self._bm.stop()
            except Exception:
                pass

    def probe_single(self, target_url: str, probe: CVEProbe) -> list[ProbeResult]:
        """Check all endpoints of a CVE probe against one target URL."""
        results = []
        parsed = urlparse(target_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        for endpoint in probe.endpoints:
            full_url = base.rstrip("/") + "/" + endpoint.lstrip("/")
            try:
                self._ensure_browser()
                self._page.set_extra_http_headers({
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                })
                resp = self._page.goto(full_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                time.sleep(1)
                status = resp.status
                html = self._page.content()
                title = ""
                m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
                if m:
                    title = m.group(1).strip()[:100]
                body_lower = html.lower()
                snippet = ""
                for kw in probe.fingerprint.get("body", []):
                    if kw.lower() in body_lower:
                        snippet = kw
                        break
                if not snippet and probe.fingerprint.get("header"):
                    for h in probe.fingerprint["header"]:
                        if h.lower() in html.lower():
                            snippet = h
                            break

                verdict = probe.match_status(status)
                # Upgrade verdict if fingerprint matched
                if verdict == "VULNERABLE":
                    verdict = "VULNERABLE"
                elif verdict == "EXISTS_BLOCKED" and snippet:
                    verdict = "CONFIRMED_BLOCKED"
                elif verdict == "HTTP_200" and snippet:
                    verdict = "VULNERABLE"
                elif status == 200 and (snippet or title):
                    verdict = "REACHABLE"
                elif status in (401, 403):
                    verdict = "AUTH_REQUIRED"

                results.append(ProbeResult(
                    url=full_url,
                    cve=probe.cve_id,
                    endpoint=endpoint,
                    status=status,
                    body_snippet=snippet,
                    verdict=verdict,
                    title=title,
                ))
            except Exception as e:
                logger.debug("Probe failed for %s: %s", full_url, e)
                results.append(ProbeResult(
                    url=full_url,
                    cve=probe.cve_id,
                    endpoint=endpoint,
                    status=0,
                    verdict="UNREACHABLE",
                ))

        return results

    def probe_batch(
        self,
        results: list[DorkResult],
        progress_cb: Optional[ProgressCallback] = None,
    ) -> dict[str, list[ProbeResult]]:
        """Probe all results with matching CVE definitions."""
        all_probes: dict[str, list[ProbeResult]] = {}

        total = len(results)
        for i, r in enumerate(results):
            probe = resolve_probe(r.dork)
            if not probe:
                continue
            if progress_cb:
                progress_cb(i + 1, total, f"Probing {r.domain} — {probe.cve_id}")
            prs = self.probe_single(r.url, probe)
            all_probes[r.url] = prs

        self._close()
        return all_probes

    def probe(
        self,
        results: list[DorkResult],
        progress_cb: Optional[ProgressCallback] = None,
    ) -> list[ProbeResult]:
        """Flatten batch probe into one list sorted by interest."""
        batch = self.probe_batch(results, progress_cb)
        flat = []
        for prs in batch.values():
            flat.extend(prs)
        flat.sort(key=lambda p: (
            0 if p.verdict in ("VULNERABLE", "CONFIRMED_BLOCKED", "EXISTS_BLOCKED") else
            1 if p.verdict == "AUTH_REQUIRED" else
            2 if p.verdict == "REACHABLE" else
            3
        ))
        return flat
