"""API regression oracles are fixed expected outcomes, not generator implementation calls.

Run Python: python -m unittest discover -s tests -p test_api_hardening.py -v
Run TS behavior independently: node --test tests/api_helpers_hardening.mjs (Node >=22.13).
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/testing-apis/scripts/openapi_tests.py'
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location('api_hardening_generator', SCRIPT)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class ApiHardeningTests(unittest.TestCase):
    def test_independent_json_schema_suite_oracle(self):
        from schema_support import validate
        groups = json.loads((ROOT / 'tests/fixtures/api-hardening/schema-oracle.json').read_text(encoding='utf-8'))
        for group in groups:
            for case in group['tests']:
                with self.subTest(group=group['description'], case=case['description']):
                    errors = validate(case['data'], group['schema'])
                    self.assertEqual(not errors, case['valid'], errors)

    def test_samples_obey_independent_constraints(self):
        cases = [
            ({'type': 'integer', 'exclusiveMinimum': 5}, lambda v: isinstance(v, int) and v > 5),
            ({'type': 'integer', 'minimum': 0, 'exclusiveMinimum': True}, lambda v: v > 0),
            ({'type': 'integer', 'maximum': 0}, lambda v: v <= 0),
            ({'type': 'number', 'minimum': 0.011, 'multipleOf': 0.01}, lambda v: v >= .011 and round(v * 100) == v * 100),
            ({'type': 'array', 'minItems': 2, 'items': {'type': 'integer'}}, lambda v: len(v) >= 2),
            ({'type': 'string', 'maxLength': 0}, lambda v: v == ''),
        ]
        for schema, oracle in cases:
            with self.subTest(schema=schema):
                self.assertTrue(oracle(api.sample(schema)))

    def test_boundary_generation_has_a_string_allocation_budget(self):
        probes = api.boundaries('x', {'type': 'string', 'maxLength': 1001}, api.T['en'])
        self.assertTrue(all(not isinstance(v, str) or len(v) <= 1000 for _, v, _, _ in probes))

    def test_impossible_or_unsupported_samples_are_explicit(self):
        for schema in ({'type': 'string', 'pattern': '^[A-Z]{3}$'},
                       {'type': 'integer', 'minimum': 5, 'maximum': 2},
                       {'type': 'object', 'unevaluatedProperties': False}):
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                api.sample(schema)

    def test_allof_and_ref_siblings_survive_resolution(self):
        schema = {'allOf': [{'type': 'string'}, {'minLength': 5}], 'maxLength': 8}
        self.assertEqual(api.Resolver({})(schema), schema)
        doc = {'components': {'schemas': {'N': {'type': 'integer', 'minimum': 0}}}}
        resolved = api.Resolver(doc)({'$ref': '#/components/schemas/N', 'maximum': 2})
        self.assertIn('maximum', resolved)
        self.assertIn('minimum', resolved)

    def generate(self, directory, schema=None, code='200'):
        op = {'responses': {code: {'description': 'ok'}}}
        if schema is not None:
            op['requestBody'] = {'content': {'application/json': {'schema': schema}}}
        doc = {'openapi': '3.1.0', 'info': {'title': 'fixture', 'version': '1'}, 'paths': {'/x': {'post': op}}}
        source, out, ts = (Path(directory) / n for n in ('api.json', 'cases.md', 'api.spec.ts'))
        source.write_text(json.dumps(doc), encoding='utf-8')
        result = subprocess.run([sys.executable, str(SCRIPT), str(source), '--req', 'REQ-1', '--out', str(out),
                                 '--spec-out', str(ts)], capture_output=True, text=True, encoding='utf-8')
        return result, out.read_text(encoding='utf-8') if out.exists() else '', ts.read_text(encoding='utf-8') if ts.exists() else ''

    def test_status_range_generates_executable_assertions(self):
        with tempfile.TemporaryDirectory() as d:
            result, _, ts = self.generate(d, code='2XX')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('toBeGreaterThanOrEqual(200)', ts)
            self.assertIn('toBeLessThan(300)', ts)

    def test_unverified_payload_is_skeleton_and_question(self):
        with tempfile.TemporaryDirectory() as d:
            result, compact, ts = self.generate(d, {'type': 'string', 'pattern': '^[A-Z]{3}$'})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('# QUESTION:', compact)
            self.assertIn('test.fixme(', ts)
            self.assertIn('unverified', ts.lower())

    @unittest.skipUnless(shutil.which('node'), 'Node >=22.13 required for TypeScript behavior tests')
    def test_typescript_behavior(self):
        result = subprocess.run(['node', '--test', str(ROOT / 'tests/api_helpers_hardening.mjs')],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
