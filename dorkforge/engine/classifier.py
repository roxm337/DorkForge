"""Result quality classifier — separates real instances from noise."""

from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from dorkforge.models.result import DorkResult

logger = logging.getLogger(__name__)

# Domains that are ALWAYS noise — documentation, community, SaaS, marketplaces
NOISE_DOMAINS: set[str] = {
    "docs.n8n.io", "community.n8n.io", "forum.n8n.io",
    "feedback.n8n.io", "status.n8n.io", "blog.n8n.io",
    "learn.n8n.io", "university.n8n.io",
    "github.com", "gitlab.com", "bitbucket.org",
    "reddit.com", "x.com", "twitter.com", "youtube.com",
    "stackoverflow.com", "stackexchange.com", "serverfault.com",
    "medium.com", "dev.to", "hackernoon.com",
    "substack.com", "hubspot.com",
    "freshdesk.com", "zendesk.com",
    "fiverr.com", "freelancer.com", "upwork.com",
    "udemy.com", "classcentral.com", "coursera.org",
    "scribd.com", "arxiv.org", "academia.edu",
    "spotify.com", "podcasts.", "note.com",
}

# Subdomain patterns that signal noise
NOISE_SUBDOMAIN_PATTERNS = [
    r"^docs\.", r"^community\.", r"^forum\.", r"^feedback\.",
    r"^blog\.", r"^learn\.", r"^university\.", r"^status\.",
    r"^support\.", r"^help\.", r"^api\.docs\.",
    r"^developer\.", r"^developers\.",
]

# Host-level signals (checked against netloc)
HOST_NOISE_SIGNALS = [
    "docs", "community", "forum", "feedback", "blog",
    "learn", "university", "status", "support", "help",
    "kb", "wiki", "knowledgebase",
    "academy", "campus", "training", "education",
]

# Title patterns that indicate non-instance content
TITLE_NOISE_PATTERNS = [
    r"(?i)\b(guide|tutorial|docs?|documentation|manual|quickstart)\b",
    r"(?i)\b(integration|integrate|connecting|connect)\b",
    r"(?i)\b(review|vs\.?|alternative|comparison|versus)\b",
    r"(?i)\b(blog|article|news|update|changelog)\b",
    r"(?i)\b(pricing|price|cost|plan|subscription)\b",
    r"(?i)\b(marketplace|listing|directory|hub)\b",
    r"(?i)\b(job|hire|freelance|gig|certification)\b",
    r"(?i)\b(forum|question|answer|thread|discussion)\b",
    r"(?i)\b(what is|how to|getting started|beginners?)\b",
    r"(?i)\b(api|sdk|cli)\s+(reference|docs|documentation)\b",
    r"(?i)\b(course|lesson|curriculum|class)\b",
]

# Path patterns that indicate non-instance content
PATH_NOISE_PATTERNS = [
    r"(?i)/docs?/", r"(?i)/tutorial", r"(?i)/guide",
    r"(?i)/blog/", r"(?i)/community/", r"(?i)/forum/",
    r"(?i)/kb/", r"(?i)/wiki/", r"(?i)/help/",
    r"(?i)/pricing", r"(?i)/features", r"(?i)/about",
    r"(?i)/jobs?", r"(?i)/hire", r"(?i)/certification",
    r"(?i)/marketplace", r"(?i)/integration",
    r"(?i)/alternatives?", r"(?i)/vs/",
    r"(?i)/course/", r"(?i)/learn/",
    r"(?i)/assignment", r"(?i)/quickstart",
]

# === Product-specific noise classifiers ===

def _classify_n8n(result: DorkResult) -> tuple[int, str]:
    url = result.url
    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path
    title = result.title or ""

    # Hard block: official n8n doc/community domains
    if host in NOISE_DOMAINS:
        return 0, f"Blocked domain: {host}"
    if any(host.endswith(f".{d}") for d in NOISE_DOMAINS if "." in d):
        # e.g. *.docs.n8n.io
        for noise_domain in NOISE_DOMAINS:
            if host.endswith(f".{noise_domain}"):
                return 0, f"Blocked subdomain: {host}"
    # Subdomain patterns
    for pat in NOISE_SUBDOMAIN_PATTERNS:
        if re.match(pat, host.split(".")[0] if "." in host else ""):
            return 0, f"Noise subdomain pattern: {host}"

    # Title noise
    title_lower = title.lower()
    score = 5
    reasons = []

    for pat in TITLE_NOISE_PATTERNS:
        if re.search(pat, title):
            score -= 1
            label = pat if isinstance(pat, str) else pat.pattern
            reasons.append(f"title:{label[:30]}")

    # Path noise
    for pat in PATH_NOISE_PATTERNS:
        if re.search(pat, path):
            score -= 1
            label = pat if isinstance(pat, str) else pat.pattern
            reasons.append(f"path:{label[:30]}")

    # SaaS / cloud platform noise (these host n8n but we can't test their internals)
    saas_platforms = {"n8n.cloud", "railway.com", "cloudron.io", "pipedream.com"}
    for sp in saas_platforms:
        if sp in host:
            score -= 2
            reasons.append(f"SaaS platform: {sp}")

    # Marketplace / directory
    marketplace_signals = ["n8n-hub", "n8nmarkets", "n8ntemplate", "n8ntips", "n8nar",
                           "n8npro", "n8npp", "n8nup", "n8ntraining",
                           "readyn8ntemplates", "easyworkflows",
                           "toolsurf", "aitoolpipelines", "bika.ai",
                           "joinground", "soverin", "onei.ai",
                           "any2aigc", "fomiapp", "runwork",
                           "taskagi", "klardaten", "azerion",
                           "opentrain", "commudle", "hospedainfo",
                           "timidlly", "buildfastwithai", "alekgir",
                           "deep-impact", "metehanugus", "nordflux",
                           "simonesmerilli", "kevindelapena",
                           "pnta", "void.ma", "digitalgarden",
                           "maketime", "ayn8n", "mybotn8nflow",
                           "unify-ai", "hedy.ai", "newline.co",
                           "skool.com", "station.railway.com",
                           "forum.cloudron.io", "community.latenode.com",
                           "community.typeform.com", "community.suitecrm.com",
                           "community.make.com", "community.openai.com",
                           "community.hubspot.com",
                           "community.zendesk.com",
                           ]
    for ms in marketplace_signals:
        if ms in host:
            score = min(score, 1)
            reasons.append(f"marketplace:{ms}")
            break

    # Tech stack: if it's WordPress/PHP it's probably a blog/site about n8n, not n8n itself
    if result.tech:
        tech_lower = result.tech.lower()
        if "wordpress" in tech_lower or ("php" in tech_lower and "cloudflare" not in tech_lower):
            score = min(score, 1)
            reasons.append(f"tech:WordPress/PHP")

    # Check for n8n port signature
    if ":5678" in url:
        score += 2
        reasons.append("port:5678")
    if ":5678" not in url and score > 3:
        # Missing port is a negative signal for self-hosted n8n
        score -= 1
        reasons.append("no port 5678")

    score = max(0, min(5, score))
    return score, "; ".join(reasons[:3]) if reasons else "clean"


PRODUCT_CLASSIFIERS = {
    "n8n": _classify_n8n,
}


def classify_result(result: DorkResult) -> tuple[int, str]:
    """Classify a result's quality. Returns (score 0-5, reason).

    Scores:
        5 = likely real instance
        4 = probable instance
        3 = possible instance
        2 = likely noise
        1 = probable noise
        0 = definite noise
    """
    parsed = urlparse(result.url)
    host = parsed.hostname or ""

    # Block reference domains (existing filter)
    from dorkforge.engine.dorker import DorkEngine
    if DorkEngine._is_reference_source(host):
        return 0, f"reference domain: {host}"

    # Detect product for specialized classifier
    dork_lower = (result.dork or "").lower()
    for product_key, classifier_fn in PRODUCT_CLASSIFIERS.items():
        if product_key in dork_lower:
            return classifier_fn(result)

    # Generic classifier
    score = 5
    reasons = []

    for pat in TITLE_NOISE_PATTERNS:
        if re.search(pat, result.title or ""):
            score -= 1
            label = pat if isinstance(pat, str) else pat.pattern
            reasons.append(f"title:{label[:30]}")

    for pat in PATH_NOISE_PATTERNS:
        if re.search(pat, parsed.path):
            score -= 1
            label = pat if isinstance(pat, str) else pat.pattern
            reasons.append(f"path:{label[:30]}")

    if any(sig in host for sig in HOST_NOISE_SIGNALS):
        score -= 1
        reasons.append(f"host signal:{host}")

    score = max(0, min(5, score))
    return score, "; ".join(reasons[:3]) if reasons else "clean"


def filter_quality(
    results: list[DorkResult],
    min_score: int = 3,
) -> list[tuple[DorkResult, int, str]]:
    """Filter and annotate results by quality score."""
    scored = []
    for r in results:
        score, reason = classify_result(r)
        if score >= min_score:
            scored.append((r, score, reason))
    scored.sort(key=lambda x: -x[1])
    return scored
