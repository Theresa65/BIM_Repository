"""Configurable checks on exported model records; no model modification."""
from collections import Counter
from .model import InputError, is_blank, validate_model


def validate_rules(rules):
    if not isinstance(rules, dict):
        raise InputError("Rules must be an object.")
    allowed_keys = {"required_fields", "required_parameters", "unique_parameters", "allowed_levels"}
    if set(rules) - allowed_keys:
        raise InputError("Unknown rule key; check the documented rules schema.")
    for key in ("required_fields", "allowed_levels"):
        values = rules.get(key, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise InputError(f"{key} must be a list of nonempty strings.")
        if len(values) != len(set(values)):
            raise InputError(f"{key} contains duplicate values.")
    supported_fields = {"type", "level"}
    if set(rules.get("required_fields", [])) - supported_fields:
        raise InputError("required_fields supports type and level.")
    for key in ("required_parameters", "unique_parameters"):
        mappings = rules.get(key, {})
        if not isinstance(mappings, dict):
            raise InputError(f"{key} must map categories to parameter lists.")
        for category, names in mappings.items():
            if not isinstance(category, str) or not category.strip() or not isinstance(names, list):
                raise InputError(f"Invalid category mapping in {key}.")
            if any(not isinstance(name, str) or not name.strip() for name in names):
                raise InputError(f"Invalid parameter name in {key}.")
            if len(names) != len(set(names)):
                raise InputError(f"Duplicate parameter name in {key}.")


def check_model(model, rules):
    elements = validate_model(model)
    validate_rules(rules)
    issues = []
    seen_ids = {}
    seen_parameters = {}
    affected = set()

    def add(index, element, code, field, message, related=None):
        issue = {"record_index": index, "element_id": element["element_id"],
                 "category": element["category"], "code": code,
                 "field": field, "message": message}
        if related is not None:
            issue["related_record_index"] = related
        issues.append(issue)
        affected.add(index)

    for index, element in enumerate(elements):
        element_id = element["element_id"].strip()
        category = element["category"].strip()
        if element_id in seen_ids:
            add(index, element, "duplicate_element_id", "element_id",
                "Element ID repeats an earlier record.", seen_ids[element_id])
            affected.add(seen_ids[element_id])
        else:
            seen_ids[element_id] = index
        for field in rules.get("required_fields", []):
            if is_blank(element.get(field)):
                add(index, element, "missing_field", field, f"Required field '{field}' is blank.")
        level = element.get("level")
        if rules.get("allowed_levels") and not is_blank(level) and level.strip() not in rules["allowed_levels"]:
            add(index, element, "invalid_level", "level", "Level is outside the configured allowed list.")
        parameters = element.get("parameters", {})
        for name in rules.get("required_parameters", {}).get(category, []):
            if is_blank(parameters.get(name)):
                add(index, element, "missing_parameter", name, f"Required parameter '{name}' is blank.")
        for name in rules.get("unique_parameters", {}).get(category, []):
            value = parameters.get(name)
            if is_blank(value):
                continue
            if not isinstance(value, (str, int, float, bool)):
                raise InputError(f"Element {element_id}: unique parameter '{name}' must be scalar.")
            # Keep types separate; trim text; uniqueness is case-sensitive within a category.
            normalized = value.strip() if isinstance(value, str) else str(value)
            key = (category, name, type(value).__name__, normalized)
            if key in seen_parameters:
                earlier = seen_parameters[key]
                add(index, element, "duplicate_parameter", name,
                    f"Parameter '{name}' repeats another value in this category.", earlier)
                affected.add(earlier)
            else:
                seen_parameters[key] = index
    return {
        "schema_version": "1.0",
        "scope": "exported_data_quality",
        "summary": {"element_count": len(elements), "issue_count": len(issues),
                    "affected_record_count": len(affected),
                    "records_without_issues": len(elements) - len(affected),
                    "issues_by_code": dict(sorted(Counter(i["code"] for i in issues).items()))},
        "issues": issues,
    }
