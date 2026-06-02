from __future__ import annotations

import os
import tempfile

from src.report.core.types import ContentType, DocumentModel, ReportElement
from src.report.validation import ReportValidator, validate_report

SAMPLE_CSV = """type,id,content,style,language,visible,order
title,main,Test,title,en,true,1
paragraph,p1,Body text,body,en,true,2
"""


def test_validator_empty():
    validator = ReportValidator()
    model = DocumentModel()
    issues = validator.validate_document(model)
    assert len(issues) == 0


def test_validator_missing_element_id():
    validator = ReportValidator()
    model = DocumentModel()
    model.add_element(ReportElement(
        element_id="", content_type=ContentType.PARAGRAPH, content="text", style="body",
    ))
    issues = validator.validate_document(model)
    assert any("missing id" in i.lower() for i in issues)


def test_validator_csv():
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(SAMPLE_CSV)
    f.close()
    try:
        validator = ReportValidator()
        issues = validator.validate_csv(f.name)
        assert len(issues) == 0
    finally:
        os.unlink(f.name)


def test_validate_report_convenience():
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(SAMPLE_CSV)
    f.close()
    try:
        validator = validate_report(f.name)
        assert validator is not None
    finally:
        os.unlink(f.name)


def test_validator_summary_no_issues():
    validator = ReportValidator()
    summary = validator.summary()
    assert "No validation issues found" in summary
