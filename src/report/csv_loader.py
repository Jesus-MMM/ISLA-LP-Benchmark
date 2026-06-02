from __future__ import annotations

import csv
import os
from typing import Any, Optional

from .core.types import ReportElement, ContentType, DocumentModel, PageConfig
from .core.exceptions import CSVParseError


CSV_FIELD_NAMES = [
    "type", "id", "content", "style", "language",
    "visible", "condition", "order", "metadata",
]

CONTENT_TYPE_MAP: dict[str, ContentType] = {
    "title": ContentType.TITLE,
    "subtitle": ContentType.SUBTITLE,
    "heading": ContentType.HEADING,
    "paragraph": ContentType.PARAGRAPH,
    "image": ContentType.IMAGE,
    "table": ContentType.TABLE,
    "chart": ContentType.CHART,
    "spacer": ContentType.SPACER,
    "citation": ContentType.CITATION,
    "reference": ContentType.REFERENCE,
    "page_break": ContentType.PAGE_BREAK,
    "list": ContentType.LIST,
    "code_block": ContentType.CODE_BLOCK,
    "formula": ContentType.FORMULA,
    "note": ContentType.NOTE,
    "footer": ContentType.FOOTER,
    "header": ContentType.HEADER,
    "abstract": ContentType.ABSTRACT,
    "caption": ContentType.CAPTION,
    "data_block": ContentType.DATA_BLOCK,
    "custom": ContentType.CUSTOM,
}


def parse_metadata(metadata_str: str) -> dict[str, Any]:
    """Analiza el campo de metadatos de una fila CSV y lo convierte en un diccionario."""
    if not metadata_str or metadata_str.strip() == "":
        return {}
    result: dict[str, Any] = {}
    parts = metadata_str.split(",")
    for part in parts:
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            result[key.strip()] = value.strip()
        else:
            result[part] = True
    return result


def parse_bool(value: str) -> bool:
    """Interpreta una cadena como un valor booleano."""
    return value.strip().lower() in ("true", "yes", "1", "t", "y")


def parse_int(value: str, default: int = 0) -> int:
    """Convierte una cadena a entero; devuelve el valor por defecto si falla."""
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return default


def load_csv(file_path: str, encoding: str = "utf-8-sig") -> list[dict[str, Any]]:
    """Load and parse a CSV report definition file.

    Args:
        file_path: Path to the CSV file.
        encoding: File encoding (default: utf-8-sig for BOM support).

    Returns:
        List of parsed row dictionaries.

    Raises:
        CSVParseError: If the file cannot be read or parsed.
    """
    if not os.path.exists(file_path):
        raise CSVParseError(f"CSV file not found: {file_path}", file_path=file_path)

    rows: list[dict[str, Any]] = []
    try:
        with open(file_path, encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise CSVParseError("Empty CSV file", file_path=file_path)

            for i, row in enumerate(reader, start=2):
                row_type = row.get("type", "").strip()
                if not row_type or row_type.startswith("#"):
                    continue
                if row_type.startswith(";"):
                    continue

                parsed: dict[str, Any] = {
                    "type": row_type,
                    "id": row.get("id", "").strip(),
                    "content": row.get("content", "").strip(),
                    "style": row.get("style", "default").strip(),
                    "language": row.get("language", "").strip(),
                    "visible": parse_bool(row.get("visible", "true")),
                    "condition": row.get("condition", "").strip() or None,
                    "order": parse_int(row.get("order", "0")),
                    "metadata": parse_metadata(row.get("metadata", "")),
                    "_row": i,
                }
                rows.append(parsed)
    except csv.Error as e:
        raise CSVParseError(f"CSV parsing error: {e}", file_path=file_path) from e
    except UnicodeDecodeError as e:
        raise CSVParseError(f"Encoding error: {e}", file_path=file_path) from e
    except OSError as e:
        raise CSVParseError(f"File read error: {e}", file_path=file_path) from e

    return rows


def rows_to_elements(rows: list[dict[str, Any]]) -> list[ReportElement]:
    """Convert parsed CSV rows into ReportElement objects.

    Args:
        rows: Parsed CSV rows from load_csv().

    Returns:
        List of ReportElement instances sorted by order.
    """
    elements: list[ReportElement] = []
    for row in rows:
        content_type = CONTENT_TYPE_MAP.get(row["type"], ContentType.CUSTOM)

        element = ReportElement(
            element_id=row.get("id", ""),
            content_type=content_type,
            content=row.get("content", ""),
            style=row.get("style", "default"),
            language=row.get("language", ""),
            visible=row.get("visible", True),
            condition=row.get("condition") or None,
            order=row.get("order", 0),
            metadata=row.get("metadata", {}),
        )
        elements.append(element)

    elements.sort(key=lambda e: e.order)
    return elements


def load_report_definition(
    csv_path: str,
    page_config: Optional[PageConfig] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> DocumentModel:
    """Load a complete report definition from a CSV file.

    Args:
        csv_path: Path to the CSV definition file.
        page_config: Optional page configuration.
        metadata: Optional report metadata.

    Returns:
        A DocumentModel populated with elements from the CSV.
    """
    rows = load_csv(csv_path)
    elements = rows_to_elements(rows)
    model = DocumentModel(
        elements=elements,
        page_config=page_config or PageConfig(),
        metadata=metadata or {},
    )
    return model


def validate_csv_schema(rows: list[dict[str, Any]]) -> list[str]:
    """Validate CSV rows against expected schema.

    Args:
        rows: Parsed CSV rows.

    Returns:
        List of validation warning/error messages.
    """
    issues: list[str] = []
    seen_ids: set[str] = set()

    for row in rows:
        row_num = row.get("_row", "?")
        element_id = row.get("id", "")

        if not element_id:
            issues.append(f"Row {row_num}: missing 'id' field")

        if element_id in seen_ids:
            issues.append(f"Row {row_num}: duplicate id '{element_id}'")
        seen_ids.add(element_id)

        content_type = row.get("type", "")
        if content_type not in CONTENT_TYPE_MAP:
            issues.append(f"Row {row_num}: unknown type '{content_type}'")

    return issues


def merge_definitions(*csv_paths: str) -> DocumentModel:
    """Load and merge multiple CSV definition files.

    Later files override earlier ones with the same element id.

    Args:
        *csv_paths: Paths to CSV definition files.

    Returns:
        Merged DocumentModel.
    """
    merged = DocumentModel()
    seen_ids: set[str] = set()

    for path in csv_paths:
        rows = load_csv(path)
        for row in rows:
            element_id = row["id"]
            if element_id in seen_ids:
                merged.remove_element(element_id)
            element = ReportElement(
                element_id=element_id,
                content_type=CONTENT_TYPE_MAP.get(row["type"], ContentType.CUSTOM),
                content=row["content"],
                style=row["style"],
                language=row["language"],
                visible=row["visible"],
                condition=row["condition"],
                order=row["order"],
                metadata=row["metadata"],
            )
            merged.add_element(element)
            seen_ids.add(element_id)

    merged.elements.sort(key=lambda e: e.order)
    return merged
