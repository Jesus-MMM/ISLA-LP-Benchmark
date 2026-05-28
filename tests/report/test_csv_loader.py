from __future__ import annotations

import tempfile
import os

import pytest

from src.report.csv_loader import (
    load_csv, rows_to_elements, load_report_definition,
    validate_csv_schema, parse_metadata,
)
from src.report.core.types import ContentType
from src.report.core.exceptions import CSVParseError


SAMPLE_CSV = """type,id,content,style,language,visible,order,metadata
title,main_title,report.title,apa_title,en,true,1,
paragraph,intro,report.introduction,body,en,true,2,
image,diagram_1,assets/network.png,image_large,en,true,3,caption=network_caption
table,results_table,data.results,apa_table,en,true,4,
page_break,pb1,,default,en,true,5,
heading,section1,report.section1,heading,en,true,6,
"""


def test_load_csv_basic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_CSV)
        tmp_path = f.name

    try:
        rows = load_csv(tmp_path)
        assert len(rows) == 6
        assert rows[0]["type"] == "title"
        assert rows[0]["id"] == "main_title"
        assert rows[0]["content"] == "report.title"
        assert rows[0]["style"] == "apa_title"
        assert rows[0]["visible"] is True
        assert rows[0]["order"] == 1
    finally:
        os.unlink(tmp_path)


def test_load_csv_comment_lines():
    csv_with_comments = """type,id,content,style,language,visible
# comment line
title,main,title,style,en,true
; also comment
paragraph,p1,text,body,en,true
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_with_comments)
        tmp_path = f.name

    try:
        rows = load_csv(tmp_path)
        assert len(rows) == 2
        assert rows[0]["type"] == "title"
        assert rows[1]["type"] == "paragraph"
    finally:
        os.unlink(tmp_path)


def test_load_csv_file_not_found():
    with pytest.raises(CSVParseError, match="not found"):
        load_csv("nonexistent_file.csv")


def test_parse_metadata_empty():
    assert parse_metadata("") == {}
    assert parse_metadata(None) == {}
    assert parse_metadata("  ") == {}


def test_parse_metadata_key_value():
    result = parse_metadata("caption=network_caption,width=500")
    assert result == {"caption": "network_caption", "width": "500"}


def test_parse_metadata_boolean():
    result = parse_metadata("center, border=true")
    assert result.get("center") is True
    assert result.get("border") == "true"


def test_rows_to_elements():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_CSV)
        tmp_path = f.name

    try:
        rows = load_csv(tmp_path)
        elements = rows_to_elements(rows)
        assert len(elements) == 6
        assert elements[0].content_type == ContentType.TITLE
        assert elements[0].element_id == "main_title"
        assert elements[1].content_type == ContentType.PARAGRAPH
        assert elements[2].content_type == ContentType.IMAGE
        assert elements[3].content_type == ContentType.TABLE
        assert elements[4].content_type == ContentType.PAGE_BREAK
        assert elements[5].content_type == ContentType.HEADING
    finally:
        os.unlink(tmp_path)


def test_rows_to_elements_ordering():
    csv = """type,id,content,style,language,visible,order
paragraph,p2,,body,en,true,2
paragraph,p1,,body,en,true,1
paragraph,p3,,body,en,true,3
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv)
        tmp_path = f.name

    try:
        rows = load_csv(tmp_path)
        elements = rows_to_elements(rows)
        assert [e.element_id for e in elements] == ["p1", "p2", "p3"]
    finally:
        os.unlink(tmp_path)


def test_validate_csv_schema():
    csv = """type,id,content,style,language,visible
unknown_type,test,content,style,en,true
title,,title,style,en,true
title,dup,content,style,en,true
title,dup,content,style,en,true
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv)
        tmp_path = f.name

    try:
        rows = load_csv(tmp_path)
        issues = validate_csv_schema(rows)
        assert len(issues) >= 3
    finally:
        os.unlink(tmp_path)


def test_load_report_definition():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_CSV)
        tmp_path = f.name

    try:
        model = load_report_definition(tmp_path)
        assert len(model.elements) == 6
        assert model.page_config is not None
    finally:
        os.unlink(tmp_path)
