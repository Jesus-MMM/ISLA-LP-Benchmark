from __future__ import annotations

import tempfile
import os

from src.report.styles import (
    create_default_styles, get_style, merge_styles, load_styles_csv,
)
from src.report.core.types import StyleDefinition
from src.report.core.exceptions import StyleNotFoundError


THEME_CSV = """\
section,name,property,value
style,custom_style,font_family,Courier
style,custom_style,font_size,8
style,custom_style,color,333333
"""


def _write_csv(content: str, suffix=".csv"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def test_create_default_styles():
    styles = create_default_styles()
    assert "default" in styles
    assert "title" in styles
    assert "heading" in styles
    assert "body" in styles
    assert "apa_table" in styles
    assert styles["title"].font_size == 24
    assert styles["title"].bold is True
    assert styles["body"].font_size == 10


def test_get_style_existing():
    styles = create_default_styles()
    style = get_style("title", styles)
    assert style.font_size == 24


def test_get_style_fallback():
    styles = {"default": StyleDefinition(font_size=12)}
    style = get_style("nonexistent", styles)
    assert style.font_size == 12


def test_get_style_no_default():
    style = get_style("nonexistent", {})
    assert isinstance(style, StyleDefinition)


def test_merge_styles():
    base = {
        "heading": StyleDefinition(font_size=14, bold=True, color="000000"),
    }
    override = {
        "heading": StyleDefinition(font_size=16, italic=True, bold=False),
    }
    merged = merge_styles(base, override)
    assert merged["heading"].font_size == 16
    assert merged["heading"].bold is False
    assert merged["heading"].italic is True
    assert merged["heading"].color == "000000"


def test_style_from_dict():
    style = StyleDefinition.from_dict({
        "font_family": "Times",
        "font_size": 12,
        "bold": True,
        "nonexistent_field": "ignored",
    })
    assert style.font_family == "Times"
    assert style.font_size == 12
    assert style.bold is True
    assert not hasattr(style, "nonexistent_field")


def test_load_styles_csv():
    path = _write_csv(THEME_CSV)
    try:
        styles = load_styles_csv(path)
        assert "custom_style" in styles
        assert styles["custom_style"].font_family == "Courier"
        assert styles["custom_style"].font_size == 8
    finally:
        os.unlink(path)


def test_load_styles_csv_not_found():
    import pytest
    with pytest.raises(StyleNotFoundError):
        load_styles_csv("nonexistent.csv")


def test_load_styles_csv_empty():
    path = _write_csv("section,name,property,value\n")
    try:
        styles = load_styles_csv(path)
        assert styles == {}
    finally:
        os.unlink(path)


def test_load_styles_csv_skips_page_section():
    path = _write_csv("""\
section,name,property,value
page,,width,215.9
style,test_style,font_family,Times
""")
    try:
        styles = load_styles_csv(path)
        assert "test_style" in styles
        assert styles["test_style"].font_family == "Times"
        assert len(styles) == 1
    finally:
        os.unlink(path)


def test_default_style_values():
    style = StyleDefinition()
    assert style.font_family == "Helvetica"
    assert style.font_size == 10
    assert style.bold is False
    assert style.italic is False
    assert style.color == "000000"


def test_load_styles_multiple_styles():
    path = _write_csv("""\
section,name,property,value
style,alpha,font_family,Arial
style,alpha,font_size,12
style,alpha,bold,true
style,beta,font_family,Courier
style,beta,font_size,10
style,beta,italic,true
""")
    try:
        styles = load_styles_csv(path)
        assert "alpha" in styles
        assert "beta" in styles
        assert styles["alpha"].font_family == "Arial"
        assert styles["alpha"].font_size == 12
        assert styles["alpha"].bold is True
        assert styles["beta"].font_family == "Courier"
        assert styles["beta"].italic is True
    finally:
        os.unlink(path)
