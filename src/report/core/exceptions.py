

class ReportError(Exception):
    """Base exception for all report engine errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Excepción base para todos los errores del motor de informes.

        Args:
            message: Mensaje descriptivo del error.
            details: Diccionario opcional con detalles adicionales del error.
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class CSVParseError(ReportError):
    """Error parsing CSV report definition."""

    def __init__(self, message: str, row: int | None = None, file_path: str | None = None) -> None:
        """Error al analizar un archivo CSV de definición de informes.

        Args:
            message: Mensaje descriptivo del error.
            row: Número de fila donde ocurrió el error, si aplica.
            file_path: Ruta del archivo CSV donde ocurrió el error, si aplica.
        """
        details = {}
        if row is not None:
            details["row"] = row
        if file_path is not None:
            details["file"] = file_path
        super().__init__(message, details)


class LocalizationError(ReportError):
    """Error resolving localization key."""

    def __init__(self, key: str, language: str, message: str | None = None) -> None:
        """Error al resolver una clave de localización.

        Args:
            key: Clave de localización que no pudo resolverse.
            language: Idioma en el que se buscó la clave.
            message: Mensaje personalizado opcional.
        """
        details = {"key": key, "language": language}
        msg = message or f"Missing localization key '{key}' for language '{language}'"
        super().__init__(msg, details)


class TagParseError(ReportError):
    """Error parsing rich text tags."""

    def __init__(self, message: str, position: int | None = None, tag: str | None = None) -> None:
        """Error al analizar etiquetas de texto enriquecido.

        Args:
            message: Mensaje descriptivo del error.
            position: Posición dentro del texto donde ocurrió el error, si aplica.
            tag: Etiqueta que causó el error, si aplica.
        """
        details = {}
        if position is not None:
            details["position"] = position
        if tag is not None:
            details["tag"] = tag
        super().__init__(message, details)


class DataBindingError(ReportError):
    """Error resolving data binding."""

    def __init__(self, key: str, message: str | None = None) -> None:
        """Error al resolver un enlace de datos.

        Args:
            key: Clave del enlace de datos que no pudo resolverse.
            message: Mensaje personalizado opcional.
        """
        details = {"key": key}
        msg = message or f"Missing data binding key '{key}'"
        super().__init__(msg, details)


class StyleNotFoundError(ReportError):
    """Requested style not found."""

    def __init__(self, style_name: str) -> None:
        """Error cuando no se encuentra un estilo solicitado.

        Args:
            style_name: Nombre del estilo que no se encontró.
        """
        super().__init__(f"Style '{style_name}' not found", {"style": style_name})


class RenderError(ReportError):
    """Error during rendering."""

    def __init__(self, message: str, element_id: str | None = None) -> None:
        """Error durante el renderizado de un elemento.

        Args:
            message: Mensaje descriptivo del error.
            element_id: Identificador del elemento que falló al renderizar, si aplica.
        """
        details = {}
        if element_id is not None:
            details["element_id"] = element_id
        super().__init__(message, details)


class ValidationError(ReportError):
    """Report validation error."""

    def __init__(self, message: str, issues: list[str] | None = None) -> None:
        """Error de validación de un informe.

        Args:
            message: Mensaje descriptivo del error.
            issues: Lista opcional de problemas de validación encontrados.
        """
        details = {"issues": issues or []}
        super().__init__(message, details)
