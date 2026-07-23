from __future__ import annotations

import json
import logging
import urllib.request
from typing import Optional

from dorkforge.models.result import DorkResult

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send results to a Slack webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, results: list[DorkResult], title: str = "DorkForge Results") -> bool:
        if not self.webhook_url:
            logger.warning("No Slack webhook URL configured")
            return False

        chunks = self._chunk(results, 10)
        for i, chunk in enumerate(chunks):
            lines = "\n".join(
                f"{j+1}. <{r.url}|[{r.status}] {r.url}>" for j, r in enumerate(chunk)
            )
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{title} (batch {i+1}/{len(chunks)})"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```\n{lines}\n```"},
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"DorkForge — {len(results)} total results"}],
                },
            ]
            payload = {"blocks": blocks}
            try:
                data = json.dumps(payload).encode()
                req = urllib.request.Request(
                    self.webhook_url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=10)
            except Exception as e:
                logger.error("Slack webhook failed: %s", e)
                return False
        return True

    @staticmethod
    def _chunk(items, n):
        for i in range(0, len(items), n):
            yield items[i:i + n]
