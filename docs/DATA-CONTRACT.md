# Input and rules contract

## Model input

The top-level object has schema_version "1.0", units exactly {"area": "m2", "volume": "m3"}, and an elements list. Empty lists are supported.

Each record requires a nonempty string element_id and category. Type and level may be text, blank, null, or absent. Parameters, when supplied, must be an object.

~~~json
{
  "schema_version": "1.0",
  "units": {"area": "m2", "volume": "m3"},
  "elements": [
    {
      "element_id": "1001",
      "category": "Walls",
      "type": "Basic Wall 200",
      "level": "L00",
      "parameters": {"mark": "W-001", "fire_rating": "120"},
      "area_m2": "12.5",
      "volume_m3": "2.5"
    }
  ]
}
~~~

Use decimal strings to preserve source precision. Quantities can be nonnegative finite numeric values or decimal strings, or blank/null/absent for missing data. Booleans, containers, negative numbers, non-finite numbers, and values above the supported precision are rejected by the exporter. The precision limit is 18 coefficient digits and an absolute decimal exponent no greater than 9.

Quantity totals sum known values only. Measured-value counts indicate coverage. Counts lower than element counts mean incomplete data, even when a numeric total exists.

Quality checks are about configured fields and parameters, not quantity validity. The exporter independently validates quantities and rejects duplicate element IDs.

## Rules

~~~json
{
  "required_fields": ["type", "level"],
  "required_parameters": {
    "Walls": ["fire_rating"],
    "Doors": ["mark", "fire_rating"]
  },
  "unique_parameters": {"Doors": ["mark"]},
  "allowed_levels": ["L00", "L01", "L02"]
}
~~~

Rule keys are optional. Unknown keys are rejected. Required fields currently support type and level. Lists contain unique, nonempty strings. Category and parameter names are case-sensitive. Values of null or whitespace-only text count as missing; numeric zero and false do not.

Unique-parameter rules accept scalar values only. Values are unique within a category and parameter, with text trimmed and checked case-sensitively. Duplicate reports link to the first matching record and count both records as affected.

## Upstream BIM adapter

A future adapter must read the desired model elements, map fields and category names into this schema, convert units explicitly, and preserve stable element identifiers. Do not label these records as an actual Revit export until that adapter has been implemented and validated on a representative model.
