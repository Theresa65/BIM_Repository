import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bim_automation.export import export_model, quantity
from bim_automation.model import InputError, load_json
from bim_automation.quality import check_model

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.model = load_json(ROOT / "data/model.json")
        self.rules = load_json(ROOT / "data/rules.json")

    def test_known_quality_issues_and_affected_records(self):
        report = check_model(self.model, self.rules)
        self.assertEqual(report["summary"]["element_count"], 8)
        self.assertEqual(report["summary"]["issue_count"], 4)
        self.assertEqual(report["summary"]["affected_record_count"], 3)
        self.assertEqual(report["summary"]["records_without_issues"], 5)
        self.assertEqual(report["summary"]["issues_by_code"],
                         {"duplicate_parameter": 1, "missing_field": 1, "missing_parameter": 2})
        self.assertEqual({i["element_id"] for i in report["issues"]}, {"1002", "2002"})

    def test_correcting_data_removes_all_issues(self):
        self.model["elements"][1]["parameters"]["fire_rating"] = "120"
        self.model["elements"][3].update(level="L00")
        self.model["elements"][3]["parameters"].update(mark="D-002", fire_rating="60")
        self.assertEqual(check_model(self.model, self.rules)["summary"]["issue_count"], 0)

    def test_zero_and_false_are_present_values(self):
        self.model["elements"][1]["parameters"]["fire_rating"] = 0
        self.model["elements"][3]["parameters"]["fire_rating"] = False
        missing = [i for i in check_model(self.model, self.rules)["issues"] if i["code"] == "missing_parameter"]
        self.assertEqual(missing, [])

    def test_duplicate_ids_reported_and_export_rejected(self):
        self.model["elements"][1]["element_id"] = " 1001 "
        report = check_model(self.model, self.rules)
        self.assertIn("duplicate_element_id", report["summary"]["issues_by_code"])
        with self.assertRaises(InputError):
            export_model(self.model)

    def test_unique_parameter_is_scoped_to_category(self):
        self.model["elements"][0]["parameters"]["mark"] = "D-001"
        report = check_model(self.model, self.rules)
        self.assertEqual(report["summary"]["issues_by_code"]["duplicate_parameter"], 1)

    def test_unknown_rule_and_invalid_units_rejected(self):
        with self.assertRaises(InputError):
            check_model(self.model, {"requird_fields": ["level"]})
        self.model["units"]["area"] = "ft2"
        with self.assertRaises(InputError):
            export_model(self.model)

    def test_export_counts_and_exact_floor_quantities(self):
        element_csv, summary_csv = export_model(self.model)
        rows = list(csv.DictReader(io.StringIO(element_csv)))
        groups = list(csv.DictReader(io.StringIO(summary_csv)))
        self.assertEqual(len(rows), 8)
        floors = [r for r in groups if r["category"] == "Floors"]
        self.assertEqual(sum(Decimal(r["area_m2"]) for r in floors), Decimal("160"))
        self.assertEqual(sum(Decimal(r["volume_m3"]) for r in floors), Decimal("32"))
        doors = [r for r in groups if r["category"] == "Doors"]
        self.assertTrue(all(r["area_m2"] == "" and r["area_measured_count"] == "0" for r in doors))

    def test_formula_like_text_and_csv_quoting(self):
        self.model["elements"][0]["type"] = '  =HYPERLINK("x"), dangerous'
        element_csv, summary_csv = export_model(self.model)
        row = next(csv.DictReader(io.StringIO(element_csv)))
        self.assertEqual(row["type"], "'" + self.model["elements"][0]["type"].strip())
        group = next(r for r in csv.DictReader(io.StringIO(summary_csv)) if r["category"] == "Walls" and "HYPERLINK" in r["type"])
        self.assertEqual(group["type"], row["type"])

    def test_invalid_quantities_rejected_before_export(self):
        for value in ("NaN", "Infinity", "-1", True, {"value": 10}, "not a number", "1e99"):
            with self.subTest(value=value), self.assertRaises(InputError):
                quantity(value, "1001", "area_m2")

    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaises(InputError):
                load_json(path)

    def test_empty_models_produce_header_only_csv(self):
        self.model["elements"] = []
        element_csv, summary_csv = export_model(self.model)
        self.assertEqual(len(list(csv.reader(io.StringIO(element_csv)))), 1)
        self.assertEqual(len(list(csv.reader(io.StringIO(summary_csv)))), 1)
        self.assertEqual(check_model(self.model, self.rules)["summary"]["issue_count"], 0)

    def test_cli_end_to_end_and_input_protection(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            command = [sys.executable, "-m", "bim_automation"]
            check = subprocess.run(command + ["check", "data/model.json", "--output",
                                    str(directory / "quality.json"), "--fail-on-issues"],
                                   cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(check.returncode, 1, check.stderr)
            report = json.loads((directory / "quality.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["issue_count"], 4)
            self.assertEqual(report, load_json(ROOT / "examples/expected/quality.json"))
            export = subprocess.run(command + ["export", "data/model.json", "--output",
                                     str(directory / "elements.csv"), "--summary", str(directory / "summary.csv")],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(export.returncode, 0, export.stderr)
            self.assertEqual((directory / "elements.csv").read_text(encoding="utf-8"),
                             (ROOT / "examples/expected/elements.csv").read_text(encoding="utf-8"))
            self.assertEqual((directory / "summary.csv").read_text(encoding="utf-8"),
                             (ROOT / "examples/expected/summary.csv").read_text(encoding="utf-8"))
            protected = subprocess.run(command + ["export", "data/model.json", "--output", "data/model.json"],
                                       cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(protected.returncode, 2)


if __name__ == "__main__":
    unittest.main()
