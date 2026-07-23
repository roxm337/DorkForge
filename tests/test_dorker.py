"""Tests for SERP result quality gates."""

from dorkforge.engine.dorker import DorkEngine
from dorkforge.models.result import DorkResult


SERP_HTML = """
<html><body>
  <a href="https://accounts.google.com/ServiceLogin">Sign in</a>
  <a href="https://translate.google.com/translate?u=https://target.example/admin">Translate</a>
  <a href="/url?q=https%3A%2F%2Ftarget.example%2Fadmin%3Fpage%3D1&sa=U"><h3>Target admin</h3></a>
  <a href="https://sub.target.example/wp-json"><h3>Target API</h3></a>
  <a href="https://www.google.com/webhp"><h3>Google navigation heading</h3></a>
</body></html>
"""


class TestDorkEngineResultQuality:
    def test_extracts_only_organic_result_anchors(self):
        engine = DorkEngine()
        assert engine._parse_results(SERP_HTML, "test") == [
            "https://target.example/admin?page=1",
            "https://sub.target.example/wp-json",
        ]

    def test_rejects_google_owned_and_translation_hosts(self):
        assert DorkEngine._normalise_result_url("https://translate.google.com/translate?u=https://x.example") is None
        assert DorkEngine._normalise_result_url("https://www.google.com/webhp") is None

    def test_scope_requires_exact_domain_or_subdomain(self):
        engine = DorkEngine(scope_domains=["target.example"])
        results = [
            DorkResult(url="https://target.example/a"),
            DorkResult(url="https://sub.target.example/b"),
            DorkResult(url="https://not-target.example/c"),
        ]
        assert [r.url for r in engine._filter_scope(results)] == [
            "https://target.example/a", "https://sub.target.example/b"
        ]
