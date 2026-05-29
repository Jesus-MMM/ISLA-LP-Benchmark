from __future__ import annotations

import os
from typing import Any, Optional

from .core.types import (
    DocumentModel, PageConfig, RenderContext, LocaleDict,
    StyleDefinition, ReferenceDefinition,
)
from .core.exceptions import ValidationError
from .csv_loader import load_csv, rows_to_elements
from .i18n import (
    load_locale_dir, get_text,
)
from .data_binding import DataBinder, bind_data_to_model
from .styles import (
    load_theme_dir, load_page_config_csv, create_default_styles,
)
from .validation import ReportValidator
from .renderers import PDFRenderer, HTMLRenderer, MarkdownRenderer
from .renderers.base import RenderResult


class ReportEngine:
    """Main orchestrator for the scientific report generation pipeline.

    The pipeline:
    1. Load CSV definitions
    2. Resolve localization
    3. Bind dynamic data
    4. Build document model
    5. Apply styles/themes
    6. Render to output format

    Usage:
        engine = ReportEngine(language="en")
        engine.load_csv("report.csv")
        engine.set_variable("experiment_name", "Test A")
        engine.render_pdf("output.pdf")
    """

    def __init__(
        self,
        language: str = "en",
        fallback_language: str = "en",
        locale_dir: Optional[str] = None,
        theme_dir: Optional[str] = None,
        page_config: Optional[PageConfig] = None,
    ):
        self.language = language
        self.fallback_language = fallback_language
        self.page_config = page_config or PageConfig()

        self._csv_definitions: list[dict[str, Any]] = []
        self._styles: dict[str, StyleDefinition] = create_default_styles()
        self._locale_dict: LocaleDict = {}
        self._data_binder = DataBinder()
        self._references: list[ReferenceDefinition] = []
        self._citations: list[ReferenceDefinition] = []
        self._metadata: dict[str, Any] = {}
        self._diagnostics: list[str] = []

        if locale_dir:
            self.load_locale_dir(locale_dir)

        if theme_dir:
            self.load_theme_dir(theme_dir)

    def load_locale_dir(self, directory: str) -> None:
        """Load translation files from a directory."""
        self._locale_dict = load_locale_dir(directory)

    def load_theme_dir(self, directory: str) -> None:
        """Load theme/style files from a directory."""
        loaded_styles = load_theme_dir(directory)
        self._styles.update(loaded_styles)

        page = load_page_config_csv(os.path.join(directory, "theme.csv"))
        if page:
            self.page_config = page

    def load_csv(self, csv_path: str) -> None:
        """Load report definitions from a CSV file.

        Args:
            csv_path: Path to CSV definition file.
        """
        rows = load_csv(csv_path)
        self._csv_definitions = rows

    def load_csv_string(self, csv_content: str) -> None:
        """Load report definitions from a CSV string.

        Args:
            csv_content: CSV content as string.
        """
        import csv
        import io
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = []
        for i, row in enumerate(reader, start=1):
            row_type = row.get("type", "").strip()
            if not row_type or row_type.startswith("#"):
                continue
            rows.append(row)
        self._csv_definitions = rows

    def set_variable(self, key: str, value: Any) -> None:
        """Set a runtime variable for data binding."""
        self._data_binder.set_variable(key, value)

    def set_variables(self, variables: dict[str, Any]) -> None:
        """Set multiple runtime variables at once."""
        self._data_binder.set_variables(variables)

    def set_references(self, references: list[ReferenceDefinition]) -> None:
        """Set reference list for the report."""
        self._references = references

    def add_style(self, name: str, style: StyleDefinition) -> None:
        """Add or override a style definition."""
        self._styles[name] = style

    def set_page_config(self, config: PageConfig) -> None:
        """Set page configuration."""
        self.page_config = config

    def set_metadata(self, key: str, value: Any) -> None:
        """Set report metadata."""
        self._metadata[key] = value

    def build_document_model(self) -> DocumentModel:
        """Build the document model from loaded definitions.

        Resolves localization and data bindings.

        Returns:
            Fully resolved DocumentModel.
        """
        elements = rows_to_elements(self._csv_definitions)

        model = DocumentModel(
            page_config=self.page_config,
            styles=dict(self._styles),
            metadata=dict(self._metadata),
            language=self.language,
            title=self._metadata.get("title"),
            author=self._metadata.get("author"),
            date=self._metadata.get("date"),
            references=list(self._references),
        )

        for element in elements:
            model.add_element(element)

        def _localize_fn(key: str) -> str:
            return get_text(key, self.language, self._locale_dict, self.fallback_language)

        bound_model = bind_data_to_model(model, self._data_binder.data, _localize_fn)
        return bound_model

    def render_pdf(self, output_path: str, **kwargs) -> RenderResult:
        """Render the report to PDF.

        Args:
            output_path: Output file path.
            **kwargs: Additional renderer options.

        Returns:
            RenderResult with render outcome.
        """
        model = self.build_document_model()
        context = RenderContext(
            page_config=self.page_config,
            data=self._data_binder.data,
            locale=self._locale_dict,
            current_language=self.language,
            fallback_language=self.fallback_language,
            styles=self._styles,
        )
        renderer = PDFRenderer(context)
        return renderer.render(model, output_path)

    def render_html(self, output_path: str, **kwargs) -> RenderResult:
        """Render the report to HTML.

        Args:
            output_path: Output file path.

        Returns:
            RenderResult with render outcome.
        """
        model = self.build_document_model()
        context = RenderContext(
            page_config=self.page_config,
            data=self._data_binder.data,
            locale=self._locale_dict,
            current_language=self.language,
        )
        renderer = HTMLRenderer(context)
        return renderer.render(model, output_path)

    def render_markdown(self, output_path: str, **kwargs) -> RenderResult:
        """Render the report to Markdown.

        Args:
            output_path: Output file path.

        Returns:
            RenderResult with render outcome.
        """
        model = self.build_document_model()
        context = RenderContext(
            page_config=self.page_config,
            data=self._data_binder.data,
            locale=self._locale_dict,
            current_language=self.language,
        )
        renderer = MarkdownRenderer(context)
        return renderer.render(model, output_path)

    def validate(self, strict: bool = False) -> ReportValidator:
        """Validate the current report configuration.

        Args:
            strict: If True, raises on validation errors.

        Returns:
            ReportValidator with validation results.

        Raises:
            ValidationError: If strict mode and issues found.
        """
        validator = ReportValidator(strict=strict)

        for row in self._csv_definitions:
            from .csv_loader import validate_csv_schema
            issues = validate_csv_schema([row])
            for issue in issues:
                validator.issues.append(issue)

        model = self.build_document_model()
        validator.validate_document(model)

        if self._locale_dict:
            validator.validate_localization(
                model, self._locale_dict, [self.language, self.fallback_language]
            )

        if strict and validator.has_errors():
            raise ValidationError("Validation failed", validator.issues)

        return validator

    def get_diagnostics(self) -> list[str]:
        """Return collected diagnostic information."""
        return self._diagnostics

    def clear_cache(self) -> None:
        """Clear all internal caches."""
        self._csv_definitions = []
        self._diagnostics = []
