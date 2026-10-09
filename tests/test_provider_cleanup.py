"""A valid upstream cleanup must not be rejected as a new provider failure."""
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('net_template_cleanup_checks', ROOT / '.github/check_templates.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class ProviderCleanupTests(unittest.TestCase):
    provider = {'format': 'text', 'behavior': 'ipcidr'}

    def test_clean_china_cidr_source_is_accepted_after_upstream_removes_asn(self):
        payload = b'1.0.1.0/24\n2400:3200::/32\n'
        self.assertEqual(checks.provider_payload('China-IP', self.provider, payload),
                         ['1.0.1.0/24', '2400:3200::/32'])

    def test_known_asn_compatibility_remains_explicit(self):
        self.assertEqual(checks.provider_payload('China-IP', self.provider, b'1.0.1.0/24\n132203\n'),
                         ['1.0.1.0/24'])

    def test_unknown_malformed_entries_remain_rejected(self):
        for invalid in ('123456', '1.2.3.999/24', 'garbage'):
            with self.subTest(invalid=invalid), self.assertRaises(AssertionError):
                checks.provider_payload('China-IP', self.provider, ('1.0.1.0/24\n' + invalid).encode())

    def test_known_asn_cannot_hide_missing_explicit_routing(self):
        without_asn = dict(checks.CONFIG, rules=[rule for rule in checks.CONFIG['rules']
                                              if rule != 'IP-ASN,132203,DIRECT'])
        with mock.patch.object(checks, 'CONFIG', without_asn), self.assertRaises(AssertionError):
            checks.provider_payload('China-IP', self.provider, b'1.0.1.0/24\n132203\n')

    def test_other_providers_do_not_inherit_the_exception(self):
        with self.assertRaises(AssertionError):
            checks.provider_payload('Private', self.provider, b'1.0.1.0/24\n132203\n')

    def test_template_static_contracts_remain_intact(self):
        checks.static_checks()


if __name__ == '__main__':
    unittest.main()
