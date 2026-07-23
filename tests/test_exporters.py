"""Test exporters."""

import json
import os
import tempfile

from dorkforge.exporters import JSONExporter, CSVExporter, URLExporter, HTMLExporter
from dorkforge.models.result import DorkResult

SAMPLE = [
    DorkResult(url="https://example.com", title="Example", dork="test", status=200, tech=["nginx"], forms=2),
    DorkResult(url="https://test.com/admin", title="Admin", dork="admin", status=403),
]


class TestExporters:
    def test_json_export(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = JSONExporter().export(SAMPLE, f.name)
            with open(path) as fh:
                data = json.load(fh)
            assert len(data) == 2
            assert data[0]["url"] == "https://example.com"
            os.unlink(path)

    def test_csv_export(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = CSVExporter().export(SAMPLE, f.name)
            with open(path) as fh:
                lines = fh.readlines()
            assert len(lines) == 3  # header + 2 rows
            os.unlink(path)

    def test_url_export(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = URLExporter().export(SAMPLE, f.name)
            with open(path) as fh:
                lines = fh.read().strip().split("\n")
            assert lines == ["https://example.com", "https://test.com/admin"]
            os.unlink(path)

    def test_html_export(self):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = HTMLExporter().export(SAMPLE, f.name)
            with open(path) as fh:
                html = fh.read()
            assert "DorkForge Recon Report" in html
            assert "example.com" in html
            assert "test.com" in html
            assert "nginx" in html
            os.unlink(path)

    def test_empty_export(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = JSONExporter().export([], f.name)
            with open(path) as fh:
                data = json.load(fh)
            assert data == []
            os.unlink(path)
