"""
Scientific Report Engine for ISLA LP Benchmark.

A modular, extensible, multilingual scientific report engine
where every report section is dynamically defined using CSV files
instead of hardcoded logic.

Features:
    - CSV-based report definitions
    - Rich text styling with tag system
    - APA-compliant formatting
    - Multilingual i18n support
    - Dynamic data binding
    - Pluggable rendering pipeline
    - Reusable themes and styles
"""

from .core.types import (
    ReportElement, ContentType, StyleDefinition, DocumentModel,
    DataContext, RenderContext, PageConfig, TableDefinition,
    ImageDefinition, ChartDefinition, CitationDefinition, ReferenceDefinition,
)
from .core.exceptions import (
    ReportError, CSVParseError, LocalizationError, TagParseError,
    DataBindingError, StyleNotFoundError, RenderError, ValidationError,
)

__all__ = [
    "ReportElement", "ContentType", "StyleDefinition", "DocumentModel",
    "DataContext", "RenderContext", "PageConfig",
    "TableDefinition", "ImageDefinition", "ChartDefinition",
    "CitationDefinition", "ReferenceDefinition",
    "ReportError", "CSVParseError", "LocalizationError", "TagParseError",
    "DataBindingError", "StyleNotFoundError", "RenderError", "ValidationError",
]
