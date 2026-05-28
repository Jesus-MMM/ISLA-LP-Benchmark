from __future__ import annotations

import json
import os
from typing import Any, Optional

from .core.types import StyleDefinition, PageConfig
from .core.exceptions import StyleNotFoundError


_STYLE_CACHE: dict[str, dict[str, StyleDefinition]] = {}


def load_theme(file_path: str) -> dict[str, StyleDefinition]:
    """Load a theme definition from a JSON file.

    Expected JSON structure:
    {
        "name": "apa",
        "page": {
            "width": 215.9,
            "height": 279.4,
            "margin_top": 25.4,
            ...
        },
        "styles": {
            "title": {
                "font_family": "Helvetica",
                "font_size": 24,
                "bold": true,
                "alignment": "center",
                ...
            },
            "heading": {...},
            ...
        }
    }

    Args:
        file_path: Path to the theme JSON file.

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

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise StyleNotFoundError(f"Cannot load theme: {e}") from e

    styles: dict[str, StyleDefinition] = {}
    raw_styles = data.get("styles", {})

    for name, style_data in raw_styles.items():
        if isinstance(style_data, dict):
            styles[name] = StyleDefinition.from_dict(style_data)

    _STYLE_CACHE[cache_key] = styles
    return styles


def load_theme_dir(directory: str) -> dict[str, StyleDefinition]:
    """Load all theme files from a directory.

    Args:
        directory: Path to directory containing theme JSON files.

    Returns:
        Merged styles from all themes.
    """
    merged: dict[str, StyleDefinition] = {}
    if not os.path.isdir(directory):
        return merged

    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            try:
                styles = load_theme(file_path)
                merged.update(styles)
            except StyleNotFoundError:
                continue

    return merged


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
            merged_dict = {**base_dict, **{k: v for k, v in override_dict.items() if v is not None}}
            merged[name] = StyleDefinition(**merged_dict)
        else:
            merged[name] = override_style

    return merged


def load_page_config(file_path: str) -> Optional[PageConfig]:
    """Load page configuration from a theme file.

    Args:
        file_path: Path to theme JSON file.

    Returns:
        PageConfig if available, None otherwise.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    page_data = data.get("page")
    if not page_data:
        return None

    return PageConfig(**{k: v for k, v in page_data.items()
                         if k in PageConfig.__dataclass_fields__})


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
