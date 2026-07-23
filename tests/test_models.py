"""Test DorkResult model."""

from dorkforge.models.result import DorkResult


class TestDorkResult:
    def test_default_timestamp(self):
        r = DorkResult(url="https://example.com")
        assert r.timestamp.endswith("Z")

    def test_to_dict(self):
        r = DorkResult(url="https://test.com", title="Test", status=200, tech=["nginx"])
        d = r.to_dict()
        assert d["url"] == "https://test.com"
        assert d["title"] == "Test"
        assert d["status"] == 200
        assert d["tech"] == ["nginx"]

    def test_to_json(self):
        r = DorkResult(url="https://test.com")
        j = r.to_json()
        assert "test.com" in j

    def test_from_dict(self):
        r = DorkResult.from_dict({"url": "https://test.com", "title": "Test", "status": 200})
        assert r.url == "https://test.com"
        assert r.title == "Test"
        assert r.status == 200

    def test_domain_property(self):
        r = DorkResult(url="https://sub.example.com/path")
        assert r.domain == "sub.example.com"

    def test_from_dict_ignores_extra_keys(self):
        r = DorkResult.from_dict({"url": "https://x.com", "extra": "ignored"})
        assert not hasattr(r, "extra")

    def test_roundtrip_json(self):
        r1 = DorkResult(url="https://a.com", dork="test", status=200)
        j = r1.to_json()
        from json import loads
        d = loads(j)
        r2 = DorkResult.from_dict(d)
        assert r1.url == r2.url
        assert r1.dork == r2.dork
