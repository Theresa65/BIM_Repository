# Parameter Quality Checker

**Python portfolio demonstration · exported BIM data · synthetic input**

## Problem and workflow

A model-data handover can contain incomplete parameters and inconsistent identifiers. This sample applies explicit rules to exported records and produces an issue list that refers to element IDs and zero-based record indexes.

~~~shell
python -m bim_automation check data/model.json --rules data/rules.json --output outputs/quality.json
~~~

Run from the repository root. Use --fail-on-issues to return exit code 1 when defects are found; the report is still written. Without that flag, successfully producing a report returns 0 even when it contains issues. Invalid input or I/O failure returns 2.

## Rules demonstrated

- Required type and level fields.
- Required fire-rating values for walls and doors, and marks for doors.
- Door-mark uniqueness within the Doors category.
- An allowed-level list.
- Duplicate element IDs, regardless of configured parameter rules.

These rules check data presence and consistency. A nonblank fire-rating value is not proof of fire-code compliance.

## Reproducible result

The [fixture](../../data/model.json) contains eight synthetic elements. Its [expected report](../../examples/expected/quality.json) lists four issues: one wall lacks fire-rating data; one door lacks a level and fire-rating data and repeats another door's mark. The duplicate involves both door records, so three records are affected overall.

| Element | Issue |
| --- | --- |
| 1002 | Missing fire_rating |
| 2002 | Missing level |
| 2002 | Missing fire_rating |
| 2002, related to 2001 | Duplicate door mark D-001 |

The tests also correct the intentional defects and verify that the resulting dataset passes the rules.

## Implementation and limits

The implementation is in [quality.py](../../bim_automation/quality.py). Rules are in [rules.json](../../data/rules.json). The checker preserves the input and reports issues without editing source models. Text uniqueness trims outer whitespace and is case-sensitive; numeric, boolean, and text values have distinct identities.

This example does not execute Revit, inspect geometry, check every BIM standard, or validate an actual project model. Extend the rules and test them on representative authorized data before relying on the report.
