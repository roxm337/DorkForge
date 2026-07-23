from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from dorkforge.engine.fetcher import PageFetcher
from dorkforge.models.result import DorkResult

logger = logging.getLogger(__name__)


class Enricher:
    """Enriches URL lists with status codes, titles, tech detection, endpoints, forms."""

    def __init__(self, max_workers: int = 10, timeout: int = 15):
        self.fetcher = PageFetcher(timeout=timeout)
        self.max_workers = max_workers

    def enrich(self, results: list[DorkResult]) -> list[DorkResult]:
        """Batch-enrich results in parallel."""
        logger.info("Enriching %d results (workers=%d)", len(results), self.max_workers)

        def _process(r: DorkResult) -> DorkResult:
            r.status = self.fetcher.status_code(r.url)
            if r.status != 200:
                return r
            html = self.fetcher.fetch(r.url)
            if not html:
                return r
            r.title = self.fetcher.extract_title(html)
            r.tech = self.fetcher.detect_tech(html)
            r.endpoints = self.fetcher.extract_endpoints(html, r.url)
            r.forms = self.fetcher.count_forms(html)
            return r

        enriched: list[DorkResult] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            fut_map = {pool.submit(_process, r): r for r in results}
            for fut in as_completed(fut_map):
                try:
                    enriched.append(fut.result())
                except Exception:
                    logger.warning("Enrichment failed for %s", fut_map[fut].url, exc_info=True)
                    enriched.append(fut_map[fut])

        enriched.sort(key=lambda r: r.status or 999)
        logger.info("Enrichment complete — %d/%d successful", sum(1 for r in enriched if r.status == 200), len(enriched))
        return enriched
