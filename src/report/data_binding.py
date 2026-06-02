from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from .core.types import DataContext, DocumentModel, ReportElement

VARIABLE_PATTERN = re.compile(r'\{\{(\w+(?:\.\w+)*)\}\}')
CONDITION_PATTERN = re.compile(
    r'\{\%\s*(if|unless)\s+(\w+(?:\.\w+)*)\s*\%\}'
    r'(.*?)'
    r'\{\%\s*end\s*%\}',
    re.DOTALL,
)


def resolve_variables(text: str, data: DataContext) -> str:
    """Replace {{variable}} placeholders with runtime values.

    Supports nested keys via dot notation (e.g. {{solver.name}}).

    Args:
        text: Template text with variable placeholders.
        data: Data context with variable values.

    Returns:
        Text with all variables resolved.
    """
    def _resolve(match: re.Match) -> str:
        key = match.group(1)
        value = _resolve_key(key, data.variables)
        if value is None:
            return match.group(0)
        return str(value)

    return VARIABLE_PATTERN.sub(_resolve, text)


def _resolve_key(key: str, variables: dict[str, Any]) -> Any | None:
    """Resolve a dotted key against a nested dictionary."""
    parts = key.split(".")
    current: Any = variables
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, (list, tuple)):
            try:
                index = int(part)
                current = current[index] if 0 <= index < len(current) else None
            except (ValueError, IndexError):
                return None
        else:
            return None
        if current is None:
            return None
    return current


def resolve_condition(element: ReportElement, data: DataContext) -> bool:
    """Evaluate a visibility condition on an element.

    Supports truthy/falsy checks.
    {% if variable %} shows element if variable is truthy.
    {% unless variable %} shows element if variable is falsy.
    Simple variable name checks truthiness directly.

    Args:
        element: The report element with optional condition.
        data: Data context for variable resolution.

    Returns:
        True if the element should be visible.
    """
    if not element.condition:
        return element.visible

    text = element.condition.strip()

    match = CONDITION_PATTERN.match(text)
    if match:
        keyword = match.group(1)
        var_name = match.group(2)
        condition_body = match.group(3).strip()
        value = _resolve_key(var_name, data.variables)
        is_truthy = bool(value) if value is not None else False
        if keyword == "if":
            return is_truthy if condition_body else is_truthy
        elif keyword == "unless":
            return not is_truthy if condition_body else not is_truthy
        return element.visible

    value = _resolve_key(text, data.variables)
    is_truthy = bool(value) if value is not None else False
    return is_truthy


def bind_data_to_element(
    element: ReportElement,
    data: DataContext,
    localization_fn,
) -> ReportElement:
    """Resolve all data bindings on a single element.

    Args:
        element: The report element to bind.
        data: Data context.
        localization_fn: Localization function (callable).

    Returns:
        Element with resolved content.
    """
    resolved = ReportElement(
        element_id=element.element_id,
        content_type=element.content_type,
        content=element.content,
        style=element.style,
        language=element.language,
        visible=element.visible,
        condition=element.condition,
        order=element.order,
        metadata=dict(element.metadata),
    )

    text = element.content
    if localization_fn:
        text = localization_fn(text)
    text = resolve_variables(text, data)
    resolved.content = text

    for key, value in element.metadata.items():
        if isinstance(value, str):
            resolved.metadata[key] = resolve_variables(value, data)

    resolved.visible = resolve_condition(element, data)
    return resolved


def bind_data_to_model(
    model: DocumentModel,
    data: DataContext,
    localization_fn=None,
) -> DocumentModel:
    """Resolve all data bindings in a document model.

    Args:
        model: Source document model.
        data: Data context with runtime values.
        localization_fn: Optional localization function.

    Returns:
        New DocumentModel with resolved bindings.
    """
    bound = DocumentModel(
        page_config=model.page_config,
        styles=dict(model.styles),
        metadata=dict(model.metadata),
        language=model.language,
        title=model.title,
        author=model.author,
        date=model.date,
        references=list(model.references),
        citations=list(model.citations),
    )

    for element in model.elements:
        bound_element = bind_data_to_element(element, data, localization_fn)
        if bound_element.visible:
            bound.add_element(bound_element)

    return bound


class DataBinder:
    """High-level data binding pipeline."""

    def __init__(self, data: DataContext | None = None) -> None:
        """Inicializa el binder con un contexto de datos opcional."""
        self.data = data or DataContext()

    def set_variable(self, key: str, value: Any) -> None:
        """Asigna una variable individual en el contexto de datos."""
        self.data.variables[key] = value

    def set_variables(self, variables: dict[str, Any]) -> None:
        """Asigna múltiples variables en el contexto de datos."""
        self.data.variables.update(variables)

    def set_table(self, key: str, rows: list[list[str]]) -> None:
        """Almacena una tabla en el contexto de datos bajo una clave."""
        self.data.tables[key] = rows

    def bind(
        self,
        model: DocumentModel,
        localization_fn: Callable[[str], str] | None = None,
    ) -> DocumentModel:
        """Ejecuta el enlace de datos completo sobre un modelo de documento."""
        return bind_data_to_model(model, self.data, localization_fn)
