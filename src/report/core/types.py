from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.report.core.exceptions import ReportError


class ContentType(str, Enum):
    """Supported content types for report elements."""
    TITLE = "title"
    SUBTITLE = "subtitle"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"
    SPACER = "spacer"
    CITATION = "citation"
    REFERENCE = "reference"
    PAGE_BREAK = "page_break"
    LIST = "list"
    CODE_BLOCK = "code_block"
    FORMULA = "formula"
    NOTE = "note"
    FOOTER = "footer"
    HEADER = "header"
    ABSTRACT = "abstract"
    CAPTION = "caption"
    DATA_BLOCK = "data_block"
    CUSTOM = "custom"


@dataclass
class StyleDefinition:
    """Defines visual styling for a report element."""
    font_family: str = "Helvetica"
    font_size: int = 10
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str = "000000"
    background_color: str | None = None
    alignment: str = "left"
    margin_top: float = 0.0
    margin_bottom: float = 0.0
    margin_left: float = 0.0
    margin_right: float = 0.0
    padding: float = 0.0
    border: bool = False
    border_color: str = "000000"
    border_width: float = 0.2
    width: float | None = None
    height: float | None = None
    indent: float = 0.0
    line_height: float = 1.5
    spacing_before: float = 0.0
    spacing_after: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StyleDefinition:
        """Crea una instancia de StyleDefinition a partir de un diccionario.

        Filtra las claves del diccionario para incluir solo aquellas
        que corresponden a campos válidos de la dataclass.

        Args:
            data: Diccionario con valores de estilo.

        Returns:
            Nueva instancia de StyleDefinition con los valores proporcionados.
        """
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class TableColumn:
    header: str
    width: float | None = None
    alignment: str = "left"
    style: str | None = None


@dataclass
class TableDefinition:
    headers: list[TableColumn] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    caption: str | None = None
    style: str = "apa_table"
    header_style: str = "apa_table_header"


@dataclass
class ImageDefinition:
    path: str
    width: float | None = None
    height: float | None = None
    caption: str | None = None
    alignment: str = "center"
    alt_text: str | None = None


@dataclass
class ChartDefinition:
    chart_type: str
    data_key: str
    width: float | None = None
    height: float | None = None
    caption: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationDefinition:
    key: str
    text: str | None = None
    authors: str = ""
    year: str = ""
    title: str = ""
    source: str = ""
    doi: str | None = None


@dataclass
class ReferenceDefinition:
    key: str
    authors: str = ""
    year: str = ""
    title: str = ""
    journal: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publisher: str | None = None
    doi: str | None = None
    url: str | None = None
    accessed_date: str | None = None


@dataclass
class PageConfig:
    width: float = 215.9
    height: float = 279.4
    margin_top: float = 15.0
    margin_bottom: float = 15.0
    margin_left: float = 15.0
    margin_right: float = 15.0
    page_numbering: bool = True
    header_enabled: bool = True
    footer_enabled: bool = True
    orientation: str = "portrait"
    size: str = "letter"


@dataclass
class ReportElement:
    """A single element in the report document model."""
    element_id: str
    content_type: ContentType
    content: str
    language: str = ""
    style: str = "default"
    visible: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list[ReportElement] = field(default_factory=list)
    condition: str | None = None
    order: int = 0

    def resolve_content(
        self,
        localization_fn: Callable[[str], str] | None = None,
        data_context: DataContext | None = None,
    ) -> str:
        """Resuelve el contenido del elemento aplicando localización y contexto de datos.

        Primero aplica la función de localización (si se proporciona) y luego
        resuelve las variables de plantilla del contexto de datos.

        Args:
            localization_fn: Función opcional para traducir/localizar el texto.
            data_context: Contexto de datos opcional para resolver variables.

        Returns:
            El contenido resuelto como cadena de texto.
        """
        text = self.content
        if localization_fn:
            text = localization_fn(text)
        if data_context:
            text = data_context.resolve(text)
        return text


LocaleDict = dict[str, dict[str, str]]


@dataclass
class DataContext:
    """Runtime data for template variable resolution."""
    variables: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, list[list[str]]] = field(default_factory=dict)
    charts: dict[str, ChartDefinition] = field(default_factory=dict)
    images: dict[str, ImageDefinition] = field(default_factory=dict)
    citations: dict[str, CitationDefinition] = field(default_factory=dict)
    references: dict[str, ReferenceDefinition] = field(default_factory=dict)

    def resolve(self, text: str) -> str:
        """Resuelve variables de plantilla en el texto dado.

        Reemplaza los marcadores {{variable}} con sus valores
        correspondientes del diccionario de variables.

        Args:
            text: Texto que puede contener marcadores de variable.

        Returns:
            Texto con las variables resueltas.
        """
        import re
        def _replace(match):
            key = match.group(1).strip()
            value = self.variables.get(key)
            if value is None:
                return f"{{{{{key}}}}}"
            return str(value)
        return re.sub(r'\{\{(\w+)\}\}', _replace, text)

    def get_or_default(self, key: str, default: Any = "") -> Any:
        """Obtiene el valor de una variable o un valor por defecto.

        Args:
            key: Clave de la variable a buscar.
            default: Valor por defecto si la clave no existe.

        Returns:
            Valor de la variable o el valor por defecto.
        """
        return self.variables.get(key, default)


@dataclass
class RenderContext:
    """Context passed through the rendering pipeline."""
    page_config: PageConfig = field(default_factory=PageConfig)
    data: DataContext = field(default_factory=DataContext)
    locale: LocaleDict = field(default_factory=dict)
    current_language: str = "en"
    fallback_language: str = "en"
    styles: dict[str, StyleDefinition] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[ReportError] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        """Añade un mensaje de advertencia al contexto de renderizado.

        Args:
            message: Mensaje de advertencia.
        """
        self.warnings.append(message)

    def add_error(self, error: ReportError) -> None:
        """Añade un error al contexto de renderizado.

        Args:
            error: Instancia de ReportError.
        """
        self.errors.append(error)

    def add_diagnostic(self, message: str) -> None:
        """Añade un mensaje de diagnóstico al contexto de renderizado.

        Args:
            message: Mensaje de diagnóstico.
        """
        self.diagnostics.append(message)


@dataclass
class DocumentModel:
    """Intermediate document model representing the entire report."""
    elements: list[ReportElement] = field(default_factory=list)
    page_config: PageConfig = field(default_factory=PageConfig)
    styles: dict[str, StyleDefinition] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    language: str = "en"
    title: str | None = None
    author: str | None = None
    date: str | None = None
    references: list[ReferenceDefinition] = field(default_factory=list)
    citations: list[CitationDefinition] = field(default_factory=list)

    def add_element(self, element: ReportElement) -> None:
        """Añade un elemento al modelo de documento.

        Args:
            element: Elemento del reporte a añadir.
        """
        self.elements.append(element)

    def get_elements_by_type(self, content_type: ContentType) -> list[ReportElement]:
        """Obtiene todos los elementos del tipo de contenido especificado.

        Args:
            content_type: Tipo de contenido a filtrar.

        Returns:
            Lista de elementos que coinciden con el tipo.
        """
        return [e for e in self.elements if e.content_type == content_type]

    def get_element_by_id(self, element_id: str) -> ReportElement | None:
        """Busca un elemento por su identificador único.

        Args:
            element_id: Identificador del elemento.

        Returns:
            El elemento encontrado o None si no existe.
        """
        for e in self.elements:
            if e.element_id == element_id:
                return e
        return None

    def remove_element(self, element_id: str) -> None:
        """Elimina un elemento del modelo de documento por su identificador.

        Args:
            element_id: Identificador del elemento a eliminar.
        """
        self.elements = [e for e in self.elements if e.element_id != element_id]
