from __future__ import annotations

from src.report.apa import (
    create_apa_document, format_apa_reference, format_apa_citation,
    build_apa_table_caption, build_apa_figure_caption, APA_STYLES,
    APA_PAGE_CONFIG,
)
from src.report.core.types import ReferenceDefinition, ContentType


def test_create_apa_document():
    model = create_apa_document(
        title="Test Report",
        author="John Doe",
        institution="University",
        abstract="This is an abstract.",
    )
    assert model.title == "Test Report"
    assert model.author == "John Doe"
    assert len(model.elements) > 0
    titles = [e for e in model.elements if e.content_type == ContentType.TITLE]
    assert len(titles) == 1
    assert titles[0].content == "Test Report"


def test_format_apa_reference():
    ref = ReferenceDefinition(
        key="test2024",
        authors="Smith, J.",
        year="2024",
        title="A study on optimization",
        journal="Journal of OR",
        volume="10",
        issue="2",
        pages="100-120",
        doi="10.1234/test",
    )
    formatted = format_apa_reference(ref)
    assert "Smith, J." in formatted
    assert "2024" in formatted
    assert "A study on optimization" in formatted or "_A study on optimization_" in formatted
    assert "10.1234/test" in formatted or "doi.org/10.1234/test" in formatted


def test_format_apa_citation():
    refs = [
        ReferenceDefinition(key="smith2024", authors="Smith, J.", year="2024"),
        ReferenceDefinition(key="doe2023", authors="Doe, J.", year="2023"),
    ]
    citation = format_apa_citation("smith2024", refs)
    assert "Smith" in citation
    assert "2024" in citation


def test_format_apa_citation_missing():
    citation = format_apa_citation("unknown", [])
    assert "unknown" in citation


def test_build_apa_table_caption():
    caption = build_apa_table_caption(1, "Test results")
    assert "Table 1" in caption
    assert "Test results" in caption


def test_build_apa_figure_caption():
    caption = build_apa_figure_caption(3, "Performance curves")
    assert "Figure 3" in caption
    assert "Performance curves" in caption


def test_apa_styles_exist():
    assert "apa_title" in APA_STYLES
    assert "apa_body" in APA_STYLES
    assert "apa_heading" in APA_STYLES
    assert "apa_table" in APA_STYLES
    assert "apa_reference" in APA_STYLES


def test_apa_page_config():
    assert APA_PAGE_CONFIG.margin_top == 25.4
    assert APA_PAGE_CONFIG.margin_bottom == 25.4
    assert APA_PAGE_CONFIG.size == "letter"
