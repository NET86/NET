"""Live branch movement must not mix related AI artifacts in a single CI run."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('snapshot_checks', ROOT / '.github/check_templates.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
BASE = 'https://raw.githubusercontent.com/NET86/rules/'
REF_API = 'https://api.github.com/repos/NET86/rules/git/ref/heads/stable'
SHA = 'a' * 40


class SnapshotConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.config = {'rule-providers': {'AI-Daily': {'path': 'ai.yaml', 'format': 'yaml',
            'behavior': 'classical', 'url': BASE + 'stable/rules/mihomo/ai-daily.yaml'}}}
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        if url == REF_API:
            return json.dumps({'ref': 'refs/heads/stable', 'object': {'type': 'commit', 'sha': SHA}}).encode()
        # Simulate stable advancing between the aggregate and vendor requests.
        extra = url.startswith(BASE + 'stable/') and 'github-copilot' in url
        rules = ['DOMAIN,copilot.example.com'] + (['DOMAIN,new-copilot.example.com'] if extra else [])
        if url.endswith('.yaml'):
            return ('payload:\n' + ''.join('  - ' + json.dumps(r) + '\n' for r in rules)).encode()
        return ('\n'.join(rules) + '\n').encode()

    def test_all_related_files_use_one_immutable_revision(self):
        with tempfile.TemporaryDirectory() as td, patch.object(checks, 'CONFIG', self.config), \
                patch.object(checks, 'fetch', side_effect=self.fetch):
            self.assertEqual(checks.cache_rules(Path(td)), {'AI-Daily': 1})
        self.assertEqual(self.calls.count(REF_API), 1)
        artifact_calls = [u for u in self.calls if u != REF_API]
        self.assertEqual(len(artifact_calls), 4)
        self.assertTrue(all(u.startswith(BASE + SHA + '/') for u in artifact_calls), artifact_calls)
        self.assertEqual(self.config['rule-providers']['AI-Daily']['url'], BASE + 'stable/rules/mihomo/ai-daily.yaml')

    def test_bad_ref_resolution_cannot_fall_back_to_mutable_stable(self):
        for body in ({}, {'ref': 'refs/heads/main', 'object': {'type': 'commit', 'sha': SHA}},
                     {'ref': 'refs/heads/stable', 'object': {'type': 'tag', 'sha': SHA}},
                     {'ref': 'refs/heads/stable', 'object': {'type': 'commit', 'sha': '../main'}}):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as td, \
                    patch.object(checks, 'CONFIG', self.config), patch.object(checks, 'fetch', return_value=json.dumps(body).encode()):
                with self.assertRaises((ValueError, AssertionError, KeyError)):
                    checks.cache_rules(Path(td))

    def test_consistent_snapshot_does_not_hide_a_real_missing_rule(self):
        def missing(url):
            value = self.fetch(url)
            if url.endswith('github-copilot.yaml'):
                value = b'payload:\n  - "DOMAIN,missing.example.com"\n'
            return value
        with tempfile.TemporaryDirectory() as td, patch.object(checks, 'CONFIG', self.config), \
                patch.object(checks, 'fetch', side_effect=missing), self.assertRaises(AssertionError):
            checks.cache_rules(Path(td))


if __name__ == '__main__':
    unittest.main()
