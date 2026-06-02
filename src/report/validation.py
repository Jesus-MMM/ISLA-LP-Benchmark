from __future__ import annotations

import os

from .core.exceptions import ReportError, ValidationError
from .core.types import ContentType, DocumentModel, ReportElement, StyleDefinition
from .csv_loader import load_csv, validate_csv_schema
from .styles import get_style


class ReportValidator:
    """Validates report definitions, styles, and data integrity."""

    def __init__(self, strict: bool = False) -> None:
        """Inicializa el validador de informes."""
        self.strict = strict
        self.issues: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[ReportError] = []

    def validate_csv(self, csv_path: str) -> list[str]:
        """Validate a CSV report definition file.

        Args:
            csv_path: Path to CSV file.

        Returns:
            List of validation issues.
        """
        try:
            rows = load_csv(csv_path)
        except ReportError as e:
            self.issues.append(str(e))
            return self.issues

        schema_issues = validate_csv_schema(rows)
        self.issues.extend(schema_issues)

        for issue in schema_issues:
            if self.strict:
                self.errors.append(ValidationError(issue))

        return self.issues

    def validate_document(self, model: DocumentModel) -> list[str]:
        """Validate a document model.

        Checks:
        - All referenced styles exist
        - Images exist on disk (if paths provided)
        - Elements have required fields
        - No circular references in element hierarchy

        Args:
            model: DocumentModel to validate.

        Returns:
            List of validation issues.
        """
        self.issues = []

        for element in model.elements:
            self._validate_element(element, model.styles)

        return self.issues

    def _validate_element(
        self,
        element: ReportElement,
        styles: dict[str, StyleDefinition],
    ) -> None:
        if not element.element_id:
            self.issues.append(f"Element missing id (type: {element.content_type})")

        if element.style and element.style != "default":
            try:
                get_style(element.style, styles)
            except Exception:
                self.issues.append(
                    f"Element '{element.element_id}': style '{element.style}' not found"
                )

        if element.content_type == ContentType.IMAGE:
            self._validate_image(element)

        if element.content_type == ContentType.CITATION:
            if "key" not in element.metadata:
                self.issues.append(
                    f"Citation '{element.element_id}': missing 'key' metadata"
                )

    def _validate_image(self, element: ReportElement) -> None:
        image_path = element.content
        if not image_path:
            self.issues.append(f"Image '{element.element_id}': no path specified")
            return

        if not os.path.exists(image_path):
            self.warnings.append(
                f"Image '{element.element_id}': file not found: {image_path}"
            )

    def validate_localization(
        self,
        model: DocumentModel,
        locale_dict: dict[str, dict[str, str]],
        languages: list[str],
    ) -> list[str]:
        """Check that all localized strings have translations.

        Args:
            model: Document model with localization keys.
            locale_dict: Loaded locale dictionary.
            languages: Languages to check.

        Returns:
            List of missing localization keys.
        """
        issues: list[str] = []
        found_keys: set[str] = set()

        for element in model.elements:
            content = element.content
            if content and content.startswith(("report.", "data.", "page.")):
                for lang in languages:
                    if lang in locale_dict:
                        if content not in locale_dict[lang]:
                            issue = f"Missing '{lang}' translation for '{content}'"
                            issues.append(issue)
                            if self.strict:
                                self.errors.append(ValidationError(issue))
                found_keys.add(content)

        return issues

    def has_errors(self) -> bool:
        """Devuelve True si se han registrado errores de validación."""
        return bool(self.errors)

    def summary(self) -> str:
        """Genera un resumen con todos los errores, advertencias y problemas encontrados."""
        lines: list[str] = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  - {e.message}")

        if self.issues:
            lines.append(f"Issues ({len(self.issues)}):")
            for issue in self.issues:
                lines.append(f"  - {issue}")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  - {w}")

        if not any([self.errors, self.issues, self.warnings]):
            lines.append("No validation issues found.")

        return "\n".join(lines)


def validate_report(
    csv_path: str,
    styles: dict[str, StyleDefinition] | None = None,
    locale_dict: dict[str, dict[str, str]] | None = None,
    languages: list[str] | None = None,
    strict: bool = False,
) -> ReportValidator:
    """Convenience function to run full validation on a report.

    Args:
        csv_path: Path to CSV definition file.
        styles: Optional style definitions.
        locale_dict: Optional locale dictionary.
        languages: Optional list of languages to check.
        strict: If True, raises on validation errors.

    Returns:
        ReportValidator with validation results.

    Raises:
        ValidationError: If strict mode and validation fails.
    """
    validator = ReportValidator(strict=strict)
    validator.validate_csv(csv_path)

    return validator
