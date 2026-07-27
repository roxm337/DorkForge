from __future__ import annotations

import html as html_mod
from datetime import datetime, timezone

from dorkforge.exporters.base import Exporter
from dorkforge.models.result import DorkResult


class HTMLExporter(Exporter):
    extension = "html"

    TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DorkForge Report — {date}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #0d1117; color: #c9d1d9; }}
  h1 {{ color: #58a6ff; }}
  .summary {{ margin: 10px 0; padding: 10px; background: #161b22; border-radius: 6px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #30363d; }}
  th {{ background: #21262d; color: #8b949e; text-transform: uppercase; font-size: 12px; }}
  tr:hover {{ background: #1c2128; }}
  .status-200 {{ color: #3fb950; }}
  .status-30x {{ color: #d29922; }}
  .status-40x, .status-50x {{ color: #f85149; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .tag {{ display: inline-block; padding: 2px 6px; margin: 2px; background: #21262d; border-radius: 4px; font-size: 11px; }}
  .critical {{ background: #da3633; color: white; }}
</style>
</head>
<body>
<h1>🔎 DorkForge Recon Report</h1>
<div class="summary">
  <strong>Generated:</strong> {date}<br>
  <strong>Total Results:</strong> {count}<br>
  <strong>Alive (2xx):</strong> {alive}<br>
  <strong>Dorks Used:</strong> {dorks_count}
</div>
<table>
<tr><th>#</th><th>URL</th><th>Status</th><th>Title</th><th>Tech</th><th>Forms</th><th>Endpoints</th></tr>
{rows}
</table>
</body>
</html>"""

    ROW = """\
<tr>
  <td>{idx}</td>
  <td><a href="{url}" target="_blank">{url}</a></td>
  <td class="status-{status_class}">{status}</td>
  <td>{title}</td>
  <td>{tech}</td>
  <td>{forms}</td>
  <td>{endpoints}</td>
</tr>"""

    def export(self, results: list[DorkResult], path: str) -> str:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        alive = sum(1 for r in results if r.status and 200 <= r.status < 400)
        dorks_used = len({r.dork for r in results if r.dork})

        def status_class(s: int) -> str:
            if not s:
                return "0"
            if s < 300:
                return "200"
            if s < 400:
                return "30x"
            return "40x" if s < 500 else "50x"

        rows = []
        for i, r in enumerate(results, 1):
            rows.append(self.ROW.format(
                idx=i,
                url=html_mod.escape(r.url),
                status=r.status or 0,
                status_class=status_class(r.status),
                title=html_mod.escape(r.title[:100] if r.title else ""),
                tech=" ".join(f'<span class="tag">{html_mod.escape(t)}</span>' for t in r.tech),
                forms=r.forms,
                endpoints=f'<span class="tag">{len(r.endpoints)}</span>',
            ))

        html = self.TEMPLATE.format(
            date=date,
            count=len(results),
            alive=alive,
            dorks_count=dorks_used,
            rows="\n".join(rows),
        )

        with open(path, "w") as f:
            f.write(html)
        return path
