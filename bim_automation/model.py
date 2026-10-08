"""Read and validate the documented interchange format."""
import json
import math
import os
import tempfile
from pathlib import Path


class InputError(ValueError):
    """Input does not follow the supported schema."""


def is_blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def load_json(path):
    try:
        with Path(path).open(encoding="utf-8-sig") as stream:
            return json.load(stream, parse_constant=reject_constant, parse_float=finite_float)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"Cannot read {path}: {exc}") from exc


def finite_float(token):
    value = float(token)
    if not math.isfinite(value):
        raise InputError(f"JSON number is outside the finite range: {token}")
    return value


def reject_constant(token):
    raise InputError(f"Non-finite JSON number is not supported: {token}")


def validate_model(model):
    if not isinstance(model, dict) or model.get("schema_version") != "1.0":
        raise InputError("Expected an object with schema_version '1.0'.")
    if model.get("units") != {"area": "m2", "volume": "m3"}:
        raise InputError("Expected units: area=m2 and volume=m3. Convert upstream.")
    elements = model.get("elements")
    if not isinstance(elements, list):
        raise InputError("elements must be a list.")
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            raise InputError(f"Element at index {index} must be an object.")
        for field in ("element_id", "category"):
            if not isinstance(element.get(field), str) or not element[field].strip():
                raise InputError(f"Element at index {index}: {field} must be a nonempty string.")
        if not isinstance(element.get("parameters", {}), dict):
            raise InputError(f"Element {element['element_id']}: parameters must be an object.")
        for field in ("type", "level"):
            if field in element and element[field] is not None and not isinstance(element[field], str):
                raise InputError(f"Element {element['element_id']}: {field} must be text or null.")
    return elements


def write_text_atomic(path, text):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
