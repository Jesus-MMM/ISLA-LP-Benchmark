from __future__ import annotations

import csv
import os
import typing
from typing import Any, Optional

from .core.types import StyleDefinition, PageConfig
from .core.exceptions import StyleNotFoundError


_STYLE_CACHE: dict[str, dict[str, StyleDefinition]] = {}

_BOOL_VALUES = {"true", "yes", "1", "t", "y"}

_STYLE_FIELD_TYPES = typing.get_type_hints(StyleDefinition)
_PAGE_FIELD_TYPES = typing.get_type_hints(PageConfig)


def _parse_field_value(value: str, field_type: type) -> Any:
    """Convert a CSV string to the appropriate Python type.

    Args:
        value: Raw string value from CSV.
        field_type: Target Python type (from dataclass field annotation).

    Returns:
        Converted value or None for empty strings.
    """
    if value is None or value.strip() == "":
        return None

    origin = typing.get_origin(field_type)
    if origin is typing.Union:
        args = typing.get_args(field_type)
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _parse_field_value(value, non_none[0])
        return None

    if field_type is bool:
        return value.strip().lower() in _BOOL_VALUES
    if field_type is int:
        try:
            return int(value.strip())
        except ValueError:
            return 0
    if field_type is float:
        try:
            return float(value.strip())
        except ValueError:
            return 0.0
    return value.strip()


def load_styles_csv(file_path: str) -> dict[str, StyleDefinition]:
    """Load style definitions from a CSV file.

    CSV format:
        section,name,property,value
        style,default,font_family,Helvetica
        style,default,font_size,10
        style,title,font_family,Helvetica
        style,title,font_size,24
        style,title,bold,true

    The ``section`` column distinguishes style rows from other sections.
    Each ``(name, property)`` pair defines one field of a StyleDefinition.

    Args:
        file_path: Path to the theme CSV file.

    Returns:
        Dictionary of style name to StyleDefinition.

    Raises:
        StyleNotFoundError: If the file cannot be loaded.
    """
    cache_key = file_path
    if cache_key in _STYLE_CACHE:
        return _STYLE_CACHE[cache_key]

    if not os.path.exists(file_path):
        raise StyleNotFoundError(file_path)

    styles: dict[str, dict[str, Any]] = {}
    valid_fields = set(StyleDefinition.__dataclass_fields__.keys())

    try:
        with open(file_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return {}

            for row in reader:
                section = row.get("section", "").strip()
                if section != "style":
                    continue
                name = row.get("name", "").strip()
                if not name:
                    continue
                prop = row.get("property", "").strip()
                if prop not in valid_fields:
                    continue
                value = row.get("value", "").strip()

                if name not in styles:
                    styles[name] = {}
                field_type = _STYLE_FIELD_TYPES.get(prop, str)
                styles[name][prop] = _parse_field_value(value, field_type)

    except (csv.Error, OSError) as e:
        raise StyleNotFoundError(f"Cannot load theme CSV: {e}") from e

    result: dict[str, StyleDefinition] = {
        name: StyleDefinition.from_dict(props)
        for name, props in styles.items()
    }

    _STYLE_CACHE[cache_key] = result
    return result


def load_theme_dir(directory: str) -> dict[str, StyleDefinition]:
    """Load all theme style definitions from a directory.

    Looks for ``theme.csv`` files in the given directory.

    Args:
        directory: Path to directory containing theme CSV files.

    Returns:
        Merged styles from all themes.
    """
    merged: dict[str, StyleDefinition] = {}
    if not os.path.isdir(directory):
        return merged

    for filename in sorted(os.listdir(directory)):
        if filename == "theme.csv":
            file_path = os.path.join(directory, filename)
            try:
                styles = load_styles_csv(file_path)
                merged.update(styles)
            except StyleNotFoundError:
                continue

    return merged


def load_page_config_csv(file_path: str) -> Optional[PageConfig]:
    """Load page configuration from a theme CSV file.

    Extracts rows with ``section == page`` and maps them to a PageConfig.

    Args:
        file_path: Path to theme CSV file.

    Returns:
        PageConfig if page properties are found, None otherwise.
    """
    try:
        with open(file_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return None

            page_data: dict[str, Any] = {}
            valid_fields = set(PageConfig.__dataclass_fields__.keys())

            for row in reader:
                section = row.get("section", "").strip()
                if section != "page":
                    continue
                prop = row.get("property", "").strip()
                if prop not in valid_fields:
                    continue
                value = row.get("value", "").strip()

                field_type = _PAGE_FIELD_TYPES.get(prop, str)
                page_data[prop] = _parse_field_value(value, field_type)

            if not page_data:
                return None

            return PageConfig(**{
                k: v for k, v in page_data.items()
                if k in PageConfig.__dataclass_fields__
            })

    except (csv.Error, OSError):
        return None


def get_style(name: str, styles: dict[str, StyleDefinition]) -> StyleDefinition:
    """Get a style by name, falling back to 'default'.

    Args:
        name: Style name.
        styles: Dictionary of available styles.

    Returns:
        The requested StyleDefinition or the default style.
    """
    if name in styles:
        return styles[name]

    if "default" in styles:
        return styles["default"]

    return StyleDefinition()


def merge_styles(
    base: dict[str, StyleDefinition],
    override: dict[str, StyleDefinition],
) -> dict[str, StyleDefinition]:
    """Merge two style dictionaries, override taking priority.

    For styles that exist in both, individual fields from override
    take precedence over base.

    Args:
        base: Base styles.
        override: Override styles.

    Returns:
        Merged style dictionary.
    """
    merged = dict(base)

    for name, override_style in override.items():
        if name in merged:
            base_dict = merged[name].__dict__
            override_dict = override_style.__dict__
            merged_dict = dict(base_dict)
            for k, v in override_dict.items():
                merged_dict[k] = v
            merged[name] = StyleDefinition(**merged_dict)
        else:
            merged[name] = override_style

    return merged


def create_default_styles() -> dict[str, StyleDefinition]:
    """Create a set of sensible default styles.

    Returns:
        Dictionary with common style definitions.
    """
    return {
        "default": StyleDefinition(),
        "title": StyleDefinition(
            font_family="Helvetica",
            font_size=24,
            bold=True,
            alignment="center",
            spacing_before=10.0,
            spacing_after=6.0,
        ),
        "subtitle": StyleDefinition(
            font_family="Helvetica",
            font_size=16,
            italic=True,
            alignment="center",
            spacing_before=4.0,
            spacing_after=8.0,
        ),
        "heading": StyleDefinition(
            font_family="Helvetica",
            font_size=14,
            bold=True,
            spacing_before=6.0,
            spacing_after=3.0,
        ),
        "subheading": StyleDefinition(
            font_family="Helvetica",
            font_size=12,
            bold=True,
            italic=False,
            spacing_before=4.0,
            spacing_after=2.0,
        ),
        "body": StyleDefinition(
            font_family="Helvetica",
            font_size=10,
            line_height=1.5,
            spacing_after=2.0,
        ),
        "apa_table": StyleDefinition(
            font_family="Helvetica",
            font_size=9,
            border=True,
            border_width=0.3,
            padding=2.0,
        ),
        "apa_table_header": StyleDefinition(
            font_family="Helvetica",
            font_size=9,
            bold=True,
            border=True,
            border_width=0.3,
            padding=2.0,
        ),
        "caption": StyleDefinition(
            font_family="Helvetica",
            font_size=9,
            italic=True,
            alignment="left",
            spacing_before=2.0,
            spacing_after=4.0,
        ),
        "image_caption": StyleDefinition(
            font_family="Helvetica",
            font_size=9,
            italic=True,
            alignment="center",
            spacing_before=2.0,
            spacing_after=4.0,
        ),
        "note": StyleDefinition(
            font_family="Helvetica",
            font_size=8,
            italic=True,
            color="555555",
            spacing_before=2.0,
            spacing_after=2.0,
        ),
        "code": StyleDefinition(
            font_family="Courier",
            font_size=8,
            color="333333",
            background_color="F5F5F5",
            padding=4.0,
            border=True,
            border_color="CCCCCC",
        ),
        "reference": StyleDefinition(
            font_family="Helvetica",
            font_size=9,
            line_height=1.3,
            spacing_after=2.0,
            indent=36.0,
        ),
        "footer": StyleDefinition(
            font_family="Helvetica",
            font_size=7,
            italic=True,
            color="666666",
            alignment="center",
        ),
        "header": StyleDefinition(
            font_family="Helvetica",
            font_size=8,
            color="333333",
            alignment="right",
        ),
    }
