<div align="center">

# BIM Automation Portfolio
### Theresa Safwat · Python · Model Data · Workflow Automation

Two runnable examples of practical BIM-data automation.

[Parameter checks](projects/parameter-quality-checker/README.md) · [Model-data exports](projects/model-data-export/README.md) · [Profile](https://github.com/Theresa65)

</div>

---

**Status:** AI-assisted portfolio demonstrations using synthetic data. These examples process exported model records; they are not live Revit add-ins or historical client projects.

## Sample projects

| Project | Workflow | Deliverables |
| --- | --- | --- |
| [Parameter Quality Checker](projects/parameter-quality-checker/README.md) | Validate required fields, category-specific parameters, allowed levels, and uniqueness | Configurable rules, element-level JSON issues, known test cases |
| [Model Data Export](projects/model-data-export/README.md) | Export elements and group quantities by category, type, and level | CSV schedules, quantity summaries, explicit missing-data counts |

~~~mermaid
flowchart LR
    A[Exported BIM records] --> B[Validate schema and units]
    B --> C[Check parameter rules]
    B --> D[Export and group records]
    C --> E[Element-level issue report]
    D --> F[CSV schedules and quantities]
    E --> G[Human review]
    F --> G
~~~

## Run the demonstrations

Use **Python 3.11 or newer**. No third-party packages, Revit installation, credentials, or API keys are required. Clone this repository, then run these commands from its root:

~~~shell
python -m bim_automation check data/model.json --rules data/rules.json --output outputs/quality.json
python -m bim_automation export data/model.json --output outputs/elements.csv --summary outputs/summary.csv
python -m unittest discover -s tests -v
~~~

On Windows, use the Python launcher if Python is not on PATH: replace python with py -3.

## Inspect the sample results

The synthetic dataset has **8 records** and deliberate defects. The expected quality report contains **4 issues** involving **3 records**, including the first door sharing a duplicate mark.

| Result | Expected sample outcome |
| --- | --- |
| Missing parameters | 2 missing fire-rating values |
| Missing fields | 1 missing level |
| Duplicate values | 1 repeated door mark, linking the two door records |
| Floor quantities | 160 m² and 32 m³ across two levels |
| Missing door quantities | Blank totals with measured-value counts of zero |

Browse the [expected JSON report](examples/expected/quality.json), [element CSV](examples/expected/elements.csv), and [grouped CSV](examples/expected/summary.csv). These are checked by the automated tests. No time-saving or production-quality claims are made.

## Validation

**Local validation:** all 12 tests passed on Windows on 8 October 2026. See the [validation record](docs/VALIDATION.md).

The suite covers known defects, corrected data, zero/false parameter values, duplicate element IDs, category-scoped uniqueness, invalid rules and units, quantity aggregation, formula-like CSV text, invalid quantities, non-finite JSON, empty models, CLI execution, and input-file protection.

[GitHub Actions runs](https://github.com/Theresa65/BIM_Repository/actions) provide execution evidence when the workflow is installed and runs successfully. Test files alone do not establish a passing result.

## Use your own model data

Follow the [input and rules contract](docs/DATA-CONTRACT.md). Units must already be m² and m³. An upstream Revit, Dynamo, pyRevit, or IFC adapter would need to produce that contract; no such adapter is included or validated in these demonstrations.

Source values are exported as supplied. The quality checker does not repair a model, assess fire-code compliance, or verify geometry. Quantity grouping is illustrative; it is not a complete quantity-surveying workflow.

## Development and attribution

These samples were created with AI assistance for Theresa Safwat's portfolio in October 2026. They demonstrate a reproducible workflow and are intended for review, adaptation, and extension. They do not document independently completed past work.

See the [development notes](docs/DEVELOPMENT.md) for limitations and a path to live BIM integration.
