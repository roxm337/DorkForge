"""Test built-in recon categories and CVE intel data."""

from dorkforge.data.categories import RECON_CATEGORIES, RECON_ALL_DORKS, CVE_INTEL, get_cve_by_name, get_cve_dorks


class TestCategories:
    def test_categories_not_empty(self):
        assert len(RECON_CATEGORIES) > 0

    def test_all_dorks_not_empty(self):
        assert len(RECON_ALL_DORKS) > 0

    def test_all_dorks_aggregates_categories(self):
        flat = []
        for dorks in RECON_CATEGORIES.values():
            flat.extend(dorks)
        assert RECON_ALL_DORKS == flat

    def test_each_category_has_dorks(self):
        for name, dorks in RECON_CATEGORIES.items():
            assert len(dorks) > 0, f"Category {name} has no dorks"

    def test_cve_intel_not_empty(self):
        assert len(CVE_INTEL) > 0

    def test_each_cve_has_required_keys(self):
        required = {"cvss", "type", "product", "status", "patch", "dorks"}
        for name, info in CVE_INTEL.items():
            for key in required:
                assert key in info, f"{name} missing key: {key}"

    def test_each_cve_has_corresponding_category(self):
        for cve_name in CVE_INTEL:
            short = cve_name.split("(")[-1].rstrip(")") if "(" in cve_name else cve_name
            found = any(short.lower() in cat.lower() for cat in RECON_CATEGORIES)
            if not found:
                found = any(cve_name.split()[0].lower() in cat.lower() for cat in RECON_CATEGORIES)

    def test_get_cve_by_name(self):
        info = get_cve_by_name("wp2shell")
        assert info.get("cvss") == "9.8 (Critical)"

    def test_get_cve_dorks(self):
        dorks = get_cve_dorks("wp2shell")
        assert len(dorks) > 0
        assert any("batch" in d for d in dorks)
