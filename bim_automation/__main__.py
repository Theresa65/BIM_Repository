"""Command line: python -m bim_automation check|export ..."""
import argparse
import json
import sys
from pathlib import Path
from .export import export_model
from .model import InputError, load_json, write_text_atomic
from .quality import check_model


def main(argv=None):
    parser = argparse.ArgumentParser(description="BIM data quality and CSV export demonstrations")
    commands = parser.add_subparsers(dest="command", required=True)
    checker = commands.add_parser("check", help="Check exported model parameters")
    checker.add_argument("input", type=Path)
    checker.add_argument("--rules", type=Path, default=Path("data/rules.json"))
    checker.add_argument("--output", type=Path, default=Path("outputs/quality.json"))
    checker.add_argument("--fail-on-issues", action="store_true")
    exporter = commands.add_parser("export", help="Export element and grouped quantity CSVs")
    exporter.add_argument("input", type=Path)
    exporter.add_argument("--output", type=Path, default=Path("outputs/elements.csv"))
    exporter.add_argument("--summary", type=Path, default=Path("outputs/summary.csv"))
    args = parser.parse_args(argv)
    try:
        outputs = [args.output] if args.command == "check" else [args.output, args.summary]
        inputs = [args.input, args.rules] if args.command == "check" else [args.input]
        resolved_outputs = [path.resolve() for path in outputs]
        if len(set(resolved_outputs)) != len(outputs) or set(resolved_outputs) & {p.resolve() for p in inputs}:
            raise InputError("Output paths must be distinct and must not overwrite input or rules files.")
        model = load_json(args.input)
        if args.command == "check":
            report = check_model(model, load_json(args.rules))
            write_text_atomic(args.output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(f"Checked {report['summary']['element_count']} records; {report['summary']['issue_count']} issues.")
            return 1 if args.fail_on_issues and report["summary"]["issue_count"] else 0
        element_csv, summary_csv = export_model(model)
        # Validate and build both complete reports before writing either output.
        write_text_atomic(args.output, element_csv)
        write_text_atomic(args.summary, summary_csv)
        print(f"Exported {len(model['elements'])} records.")
        return 0
    except (InputError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
