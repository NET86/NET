"""Product group tests should follow validated upstream catalog changes."""
import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "check_templates.py"
spec = importlib.util.spec_from_file_location("check_templates", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DynamicVendorTests(unittest.TestCase):
    def test_vendor_rules_follow_new_and_removed_upstream_domains(self):
        current = ["DOMAIN-SUFFIX,githubcopilot.com"]
        module.verify_dynamic_vendor_coverage(current, current, "live vendor")
        new = ["DOMAIN-SUFFIX,githubcopilot.com", "DOMAIN,entirely-new.example"]
        module.verify_dynamic_vendor_coverage(new, new, "updated vendor")
        # A legitimately withdrawn endpoint need not remain hard-coded.
        module.verify_dynamic_vendor_coverage(current, current, "reduced vendor")

    def test_missing_or_empty_vendor_fails_even_with_dynamic_contract(self):
        for vendor, profile in (
            ([], ["DOMAIN-SUFFIX,githubcopilot.com"]),
            (["DOMAIN,missing.example"], ["DOMAIN-SUFFIX,githubcopilot.com"]),
        ):
            with self.subTest(vendor=vendor), self.assertRaises(AssertionError):
                module.verify_dynamic_vendor_coverage(profile, vendor, "missing")


if __name__ == "__main__":
    unittest.main()
