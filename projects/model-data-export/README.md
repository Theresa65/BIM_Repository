# Model Data Export

**Python portfolio demonstration · element schedules · grouped quantities**

## Problem and workflow

Manual transfers from model data to reporting tables can produce duplicate records, unclear units, and missing quantities. This sample creates a flat element schedule and a grouped summary from a documented input contract.

~~~shell
python -m bim_automation export data/model.json --output outputs/elements.csv --summary outputs/summary.csv
~~~

Run from the repository root. Success returns exit code 0; invalid data or I/O failure returns 2.

## Outputs

- [Element schedule](../../examples/expected/elements.csv): one row per element, with identity, category, type, level, mark, fire rating, area, and volume.
- [Grouped summary](../../examples/expected/summary.csv): category/type/level groups, element counts, known quantity totals, and counts of measured values.

The two synthetic floor records total 160 m² and 32 m³. Each is on a separate level. Door area and volume totals stay blank because no quantities were supplied. This prevents missing values from silently becoming a misleading zero.

## Implementation decisions

[export.py](../../bim_automation/export.py) uses Decimal for quantity handling and Python's CSV writer for quoting. Duplicate element IDs and invalid, negative, or non-finite quantities cause rejection before report content is written.

Formula-like text is prefixed with an apostrophe. How an application imports CSV can still affect interpretation, so inspect imported reports before using them. Input units must already be m² and m³; the sample does not convert units.

Text fields are trimmed where they identify category, type, level, or element ID. Parameter text is preserved apart from the CSV formula prefix.

## Limits

A grouped volume is meaningful only within the measurement context supplied by the source. The sample does not derive quantities from geometry, reconcile materials, subtract openings, or apply quantity-surveying measurement standards.

Both complete reports are constructed before writing. Individual files are replaced atomically, but the two-file export is not a single transactional write: an I/O failure during the second file can leave only the first updated.

This is an exported-data workflow, not a validated live Revit integration.
