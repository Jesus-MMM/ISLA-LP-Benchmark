from __future__ import annotations

from dataclasses import dataclass

from .core.types import (
    ContentType,
    DocumentModel,
    PageConfig,
    ReferenceDefinition,
    ReportElement,
    StyleDefinition,
)


@dataclass
class APAConfig:
    """APA formatting configuration."""
    title_page: bool = True
    abstract_page: bool = True
    running_header: str = ""
    page_number_start: int = 1
    line_spacing: float = 2.0
    paragraph_indent: float = 12.7
    font_family: str = "Times"
    font_size: int = 12
    margin_top: float = 25.4
    margin_bottom: float = 25.4
    margin_left: float = 25.4
    margin_right: float = 25.4
    table_font_size: int = 10
    figure_font_size: int = 10
    title_font_size: int = 24
    heading_font_size: int = 14
    subheading_font_size: int = 12


APA_PAGE_CONFIG = PageConfig(
    width=215.9,
    height=279.4,
    margin_top=25.4,
    margin_bottom=25.4,
    margin_left=25.4,
    margin_right=25.4,
    page_numbering=True,
    header_enabled=True,
    footer_enabled=False,
    orientation="portrait",
    size="letter",
)

APA_STYLES: dict[str, StyleDefinition] = {
    "apa_title": StyleDefinition(
        font_family="Times",
        font_size=24,
        bold=True,
        alignment="center",
        spacing_before=20.0,
        spacing_after=10.0,
    ),
    "apa_abstract": StyleDefinition(
        font_family="Times",
        font_size=12,
        alignment="left",
        line_height=2.0,
    ),
    "apa_heading": StyleDefinition(
        font_family="Times",
        font_size=14,
        bold=True,
        alignment="center",
        spacing_before=12.0,
        spacing_after=6.0,
    ),
    "apa_subheading": StyleDefinition(
        font_family="Times",
        font_size=12,
        bold=True,
        alignment="left",
        spacing_before=6.0,
        spacing_after=3.0,
    ),
    "apa_body": StyleDefinition(
        font_family="Times",
        font_size=12,
        alignment="left",
        line_height=2.0,
        indent=12.7,
    ),
    "apa_table": StyleDefinition(
        font_family="Times",
        font_size=10,
        border=True,
        border_width=0.5,
        padding=3.0,
    ),
    "apa_table_header": StyleDefinition(
        font_family="Times",
        font_size=10,
        bold=True,
        border=True,
        border_width=0.5,
        padding=3.0,
    ),
    "apa_figure_caption": StyleDefinition(
        font_family="Times",
        font_size=10,
        italic=True,
        alignment="left",
        spacing_before=4.0,
        spacing_after=6.0,
    ),
    "apa_table_caption": StyleDefinition(
        font_family="Times",
        font_size=10,
        italic=True,
        alignment="left",
        spacing_before=4.0,
        spacing_after=4.0,
    ),
    "apa_reference": StyleDefinition(
        font_family="Times",
        font_size=12,
        alignment="left",
        line_height=2.0,
        indent=12.7,
        spacing_before=0.0,
        spacing_after=0.0,
    ),
    "apa_footer": StyleDefinition(
        font_family="Times",
        font_size=12,
        alignment="center",
    ),
}


def create_apa_document(
    title: str,
    author: str = "",
    institution: str = "",
    running_header: str = "",
    abstract: str | None = None,
    references: list[ReferenceDefinition] | None = None,
) -> DocumentModel:
    """Create a DocumentModel pre-configured for APA format.

    Args:
        title: Report title.
        author: Author name.
        institution: Institutional affiliation.
        running_header: Running header text.
        abstract: Optional abstract text.
        references: Optional list of references.

    Returns:
        APA-configured DocumentModel.
    """
    model = DocumentModel(
        page_config=APA_PAGE_CONFIG,
        styles=APA_STYLES,
        title=title,
        author=author,
        date="",
        language="en",
    )

    model.add_element(ReportElement(
        element_id="apa_title_page_spacer",
        content_type=ContentType.SPACER,
        content="",
        style="default",
        order=0,
    ))

    model.add_element(ReportElement(
        element_id="apa_title",
        content_type=ContentType.TITLE,
        content=title,
        style="apa_title",
        order=1,
    ))

    if author:
        model.add_element(ReportElement(
            element_id="apa_author",
            content_type=ContentType.SUBTITLE,
            content=author,
            style="apa_title",
            order=2,
        ))

    if institution:
        model.add_element(ReportElement(
            element_id="apa_institution",
            content_type=ContentType.PARAGRAPH,
            content=institution,
            style="apa_title",
            order=3,
        ))

    model.add_element(ReportElement(
        element_id="apa_title_page_break",
        content_type=ContentType.PAGE_BREAK,
        content="",
        style="default",
        order=4,
    ))

    if abstract:
        model.add_element(ReportElement(
            element_id="apa_abstract_heading",
            content_type=ContentType.HEADING,
            content="Abstract",
            style="apa_heading",
            order=5,
        ))
        model.add_element(ReportElement(
            element_id="apa_abstract_body",
            content_type=ContentType.ABSTRACT,
            content=abstract,
            style="apa_abstract",
            order=6,
        ))

    if references:
        model.add_element(ReportElement(
            element_id="apa_references_heading",
            content_type=ContentType.HEADING,
            content="References",
            style="apa_heading",
            order=1000,
        ))
        for i, ref in enumerate(references):
            model.add_element(ReportElement(
                element_id=f"apa_ref_{i}",
                content_type=ContentType.REFERENCE,
                content=format_apa_reference(ref),
                style="apa_reference",
                order=1001 + i,
            ))

    return model


def format_apa_reference(ref: ReferenceDefinition) -> str:
    """Format a reference in APA 7th edition style.

    Args:
        ref: Reference definition.

    Returns:
        APA-formatted reference string.
    """
    parts: list[str] = []

    if ref.authors:
        parts.append(ref.authors)

    if ref.year:
        parts.append(f"({ref.year}).")

    if ref.title:
        title = ref.title
        parts.append(f"_{title}_.")

    if ref.journal:
        journal = ref.journal
        journal_parts = [journal]
        if ref.volume:
            vol = ref.volume
            if ref.issue:
                journal_parts.append(f"_{vol}({ref.issue})_")
            else:
                journal_parts.append(f"_{vol}_")
        if ref.pages:
            journal_parts.append(ref.pages)
        parts.append(" ".join(journal_parts))

    if ref.publisher:
        parts.append(ref.publisher)

    if ref.doi:
        parts.append(f"https://doi.org/{ref.doi}")
    elif ref.url:
        parts.append(ref.url)

    return " ".join(parts)


def format_apa_citation(key: str, citations: list[ReferenceDefinition]) -> str:
    """Generate APA in-text citation.

    Args:
        key: Citation key.
        citations: List of available references.

    Returns:
        APA-formatted citation string.
    """
    for ref in citations:
        if ref.key == key:
            author_part = ref.authors.split(",")[0] if ref.authors else "Unknown"
            year_part = ref.year if ref.year else "n.d."
            return f"({author_part}, {year_part})"

    return f"({key})"


def build_apa_table_caption(table_number: int, caption: str) -> str:
    """Build an APA-formatted table caption.

    Args:
        table_number: Sequential table number.
        caption: Caption text.

    Returns:
        Formatted caption.
    """
    return f"Table {table_number}\n{caption}"


def build_apa_figure_caption(figure_number: int, caption: str) -> str:
    """Build an APA-formatted figure caption.

    Args:
        figure_number: Sequential figure number.
        caption: Caption text.

    Returns:
        Formatted caption.
    """
    return f"Figure {figure_number}\n{caption}"
