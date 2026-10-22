"""Regression cases and output invariants for synthetic generation (stdlib only)."""
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/preparing-test-data/scripts/gen_data.py"
spec = importlib.util.spec_from_file_location("data_invariants_generator", SCRIPT)
gd = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(SCRIPT.parent))
try:
    spec.loader.exec_module(gd)
finally:
    sys.path.remove(str(SCRIPT.parent))


def generate(fields, rows=30, seed=1, **kwargs):
    table = {"name": "sample", "fields": fields, "unique": kwargs.pop("unique", [])}
    return gd.generate_table(table, rows, seed, **kwargs)


class DecimalInvariantTests(unittest.TestCase):
    def test_unrepresentable_decimal_interval_is_rejected_before_generation(self):
        field = {"name": "amount", "type": "decimal", "min": "1.234", "max": "1.239", "scale": 2}
        self.assertIn("representable", " ".join(gd.validate_schema({"fields": [field]})))
        with self.assertRaisesRegex(gd.SchemaError, "representable"):
            generate([field])

    def test_generated_and_edge_decimals_stay_in_inclusive_bounds(self):
        for minimum, maximum, scale in (("1.234", "1.259", 2), ("-1.259", "-1.234", 2),
                                        ("-0.019", "0.019", 2), ("1.1", "2.9", 0)):
            for seed in range(5):
                with self.subTest(minimum=minimum, seed=seed):
                    field = {"name": "amount", "type": "decimal", "min": minimum, "max": maximum,
                             "scale": scale, "edge": True, "decimal_sep": ","}
                    _, rows, _ = generate([field], seed=seed, edge_fraction=0.8)
                    for row in rows:
                        value = Decimal(row["amount"].replace(",", "."))
                        self.assertGreaterEqual(value, Decimal(minimum))
                        self.assertLessEqual(value, Decimal(maximum))
                        self.assertEqual(value.as_tuple().exponent, -scale)

    def test_nonfinite_decimal_bounds_are_schema_errors(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                errors = gd.validate_schema({"fields": [{"name": "amount", "type": "decimal", "min": value}]})
                self.assertIn("finite", " ".join(errors))

    def test_json_output_preserves_decimal_precision_without_binary_float(self):
        field = {"name": "amount", "type": "decimal", "min": "123456789012345678901234567890.12",
                 "max": "123456789012345678901234567890.12", "scale": 2}
        cols, rows, _ = generate([field], rows=1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.json"
            gd.write_rows(path, cols, rows, "json", [field])
            restored = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(restored[0]["amount"], Decimal(field["min"]))


class DatetimeInvariantTests(unittest.TestCase):
    def test_aware_datetime_edges_keep_offset_and_bounds(self):
        field = {"name": "when", "type": "datetime", "min": "2026-01-01T12:00:00+03:00",
                 "max": "2026-01-04T12:00:00+03:00", "edge": True}
        _, rows, _ = generate([field], edge_fraction=1)
        for row in rows:
            value = datetime.fromisoformat(row["when"])
            self.assertIsNotNone(value.utcoffset())
            self.assertGreaterEqual(value, datetime.fromisoformat(field["min"]))
            self.assertLessEqual(value, datetime.fromisoformat(field["max"]))

    def test_mixed_naive_and_aware_bounds_are_schema_error(self):
        field = {"name": "when", "type": "datetime", "min": "2026-01-01T00:00:00",
                 "max": "2026-01-02T00:00:00+03:00"}
        self.assertIn("timezone", " ".join(gd.validate_schema({"fields": [field]})))
        with self.assertRaisesRegex(gd.SchemaError, "timezone"):
            generate([field])

    def test_subsecond_bounds_use_representable_whole_seconds(self):
        field = {"name": "when", "type": "datetime", "min": "2026-01-01T12:00:00.750",
                 "max": "2026-01-01T12:00:02.250", "edge": True}
        _, rows, _ = generate([field], edge_fraction=0.5)
        self.assertTrue({row["when"] for row in rows} <= {"2026-01-01T12:00:01", "2026-01-01T12:00:02"})

    def test_offsets_can_differ_when_instants_are_ordered(self):
        field = {"name": "when", "type": "datetime", "min": "2026-01-01T12:00:00+03:00",
                 "max": "2026-01-01T12:00:00+01:00", "edge": True}
        _, rows, _ = generate([field], edge_fraction=0.5)
        self.assertTrue(all(datetime.fromisoformat(field["min"]) <= datetime.fromisoformat(row["when"])
                            <= datetime.fromisoformat(field["max"]) for row in rows))

    def test_lossy_datetime_format_cannot_emit_out_of_bounds_values(self):
        field = {"name": "when", "type": "datetime", "min": "2026-01-01T12:00:30",
                 "max": "2026-01-01T12:00:45", "format": "%Y-%m-%dT%H:%M"}
        with self.assertRaisesRegex(gd.SchemaError, "bounds.*precision"):
            generate([field])


class ReferenceInvariantTests(unittest.TestCase):
    def test_uniqueness_retries_do_not_consume_distinct_parent(self):
        fields = [{"name": "parent", "type": "ref", "source": "parents:id", "distinct": True},
                  {"name": "token", "type": "int", "min": 0, "max": 5}]
        parents = {"parents": (["id"], [{"id": f"P{i}"} for i in range(6)])}
        for seed in range(20):
            with self.subTest(seed=seed):
                _, rows, _ = generate(fields, rows=6, seed=seed, unique=["token"], generated=parents)
                self.assertEqual(len({row["parent"] for row in rows}), 6)
                self.assertEqual(len({row["token"] for row in rows}), 6)
                self.assertTrue({row["parent"] for row in rows} <= {f"P{i}" for i in range(6)})

    def test_duplicate_parent_values_are_not_distinct_capacity(self):
        field = {"name": "parent", "type": "ref", "source": "parents:id", "distinct": True}
        parents = {"parents": (["id"], [{"id": "P1"}, {"id": "P1"}, {"id": "P2"}])}
        with self.assertRaisesRegex(gd.SchemaError, "distinct.*2"):
            generate([field], rows=3, generated=parents)
        _, rows, _ = generate([field], rows=2, generated=parents)
        self.assertEqual({row["parent"] for row in rows}, {"P1", "P2"})

    def test_seed_remains_deterministic_with_retries_and_edges(self):
        fields = [{"name": "parent", "type": "ref", "source": "parents:id", "distinct": True},
                  {"name": "token", "type": "int", "min": 0, "max": 6, "edge": True}]
        parents = {"parents": (["id"], [{"id": f"P{i}"} for i in range(6)])}
        first = generate(fields, rows=6, seed="stable", unique=["token"], generated=parents, mark_edges=True)
        second = generate(fields, rows=6, seed="stable", unique=["token"], generated=parents, mark_edges=True)
        self.assertEqual(first, second)


class InputInvariantTests(unittest.TestCase):
    def test_invalid_runtime_options_fail_clearly(self):
        field = {"name": "n", "type": "int"}
        for kwargs in ({"rows": -1}, {"rows": True}, {"edge_fraction": 1.5}, {"edge_fraction": float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(gd.SchemaError):
                generate([field], **kwargs)

    def test_malformed_schema_returns_diagnostics(self):
        for schema in ({"tables": [None]}, {"fields": [{"name": ["n"], "type": "int"}]},
                       {"fields": [{"name": "n", "type": ["int"]}]},
                       {"fields": [{"name": "n", "type": "int"}], "unique": None},
                       {"fields": [{"name": "n", "type": "enum", "values": [[1], [2]]}]},
                       {"fields": [{"name": "n", "type": "text", "charset": []}]},
                       {"fields": [{"name": "n", "type": "seq", "width": -1}]},
                       {"fields": [{"name": "n", "type": "seq", "width": True}]},
                       {"fields": [{"name": "n", "type": "date", "format": "%Q"}]},
                       {"fields": [{"name": "n", "type": "int", "edge": "true"}]}):
            with self.subTest(schema=schema):
                self.assertTrue(gd.validate_schema(schema))

    def test_edge_marker_cannot_overwrite_schema_column(self):
        with self.assertRaisesRegex(gd.SchemaError, "_edge"):
            generate([{"name": "_edge", "type": "seq"}], mark_edges=True)


if __name__ == "__main__":
    unittest.main()
