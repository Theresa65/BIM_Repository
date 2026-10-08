"""Export flat records and grouped quantities with explicit missing-data counts."""
import csv
import io
from decimal import Decimal, InvalidOperation
from .model import InputError, is_blank, validate_model

ELEMENT_COLUMNS = ("element_id", "category", "type", "level", "mark", "fire_rating", "area_m2", "volume_m3")
SUMMARY_COLUMNS = ("category", "type", "level", "element_count", "area_m2",
                   "area_measured_count", "volume_m3", "volume_measured_count")


def safe_cell(value):
    """Prefix formula-like text with an apostrophe before passing it to csv.writer."""
    if value is None:
        return ""
    if not isinstance(value, (str, int, float, bool, Decimal)):
        raise InputError("CSV fields must be scalar values.")
    text = str(value)
    stripped = text.lstrip()
    if stripped.startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def quantity(value, element_id, field):
    if is_blank(value):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise InputError(f"Element {element_id}: {field} must be a nonnegative number or null.")
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise InputError(f"Element {element_id}: invalid {field}.") from exc
    if not number.is_finite() or number < 0:
        raise InputError(f"Element {element_id}: {field} must be finite and nonnegative.")
    if len(number.as_tuple().digits) > 18 or abs(number.as_tuple().exponent) > 9:
        raise InputError(f"Element {element_id}: {field} exceeds supported precision.")
    return number


def decimal_text(number):
    return "" if number is None else format(number, "f")


def make_csv(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([safe_cell(row.get(column)) for column in columns])
    return stream.getvalue()


def export_model(model):
    elements = validate_model(model)
    rows = []
    groups = {}
    seen = set()
    for element in elements:
        element_id = element["element_id"].strip()
        if element_id in seen:
            raise InputError(f"Duplicate element ID '{element_id}'; refusing ambiguous export.")
        seen.add(element_id)
        category = element["category"].strip()
        element_type = (element.get("type") or "").strip()
        level = (element.get("level") or "").strip()
        area = quantity(element.get("area_m2"), element_id, "area_m2")
        volume = quantity(element.get("volume_m3"), element_id, "volume_m3")
        parameters = element.get("parameters", {})
        rows.append({"element_id": element_id, "category": category, "type": element_type,
                     "level": level, "mark": parameters.get("mark"),
                     "fire_rating": parameters.get("fire_rating"),
                     "area_m2": decimal_text(area), "volume_m3": decimal_text(volume)})
        key = (category, element_type, level)
        group = groups.setdefault(key, {"category": category, "type": element_type, "level": level,
                                       "element_count": 0, "area_sum": Decimal(0),
                                       "area_measured_count": 0, "volume_sum": Decimal(0),
                                       "volume_measured_count": 0})
        group["element_count"] += 1
        if area is not None:
            group["area_sum"] += area
            group["area_measured_count"] += 1
        if volume is not None:
            group["volume_sum"] += volume
            group["volume_measured_count"] += 1
    summaries = []
    for key in sorted(groups):
        group = groups[key].copy()
        group["area_m2"] = decimal_text(group.pop("area_sum")) if group["area_measured_count"] else ""
        group["volume_m3"] = decimal_text(group.pop("volume_sum")) if group["volume_measured_count"] else ""
        summaries.append(group)
    return make_csv(ELEMENT_COLUMNS, rows), make_csv(SUMMARY_COLUMNS, summaries)
