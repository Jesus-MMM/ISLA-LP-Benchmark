from __future__ import annotations

from src.report.data_binding import (
    resolve_variables, resolve_condition, DataBinder,
    bind_data_to_element, bind_data_to_model,
)
from src.report.core.types import DataContext, ReportElement, ContentType, DocumentModel


def test_resolve_variables_simple():
    data = DataContext(variables={"name": "Test", "value": 42})
    result = resolve_variables("Hello {{name}}", data)
    assert result == "Hello Test"

    result = resolve_variables("Value: {{value}}", data)
    assert result == "Value: 42"


def test_resolve_variables_missing():
    data = DataContext(variables={})
    result = resolve_variables("Hello {{name}}", data)
    assert result == "Hello {{name}}"


def test_resolve_variables_multiple():
    data = DataContext(variables={"a": "1", "b": "2"})
    result = resolve_variables("{{a}} + {{b}} = {{sum}}")
    assert result == "1 + 2 = {{sum}}"


def test_data_context_get_or_default():
    data = DataContext(variables={"key": "value"})
    assert data.get_or_default("key") == "value"
    assert data.get_or_default("missing") == ""
    assert data.get_or_default("missing", "fallback") == "fallback"


def test_bind_data_to_element():
    data = DataContext(variables={"name": "Test"})
    element = ReportElement(
        element_id="test",
        content_type=ContentType.PARAGRAPH,
        content="Hello {{name}}",
        style="body",
    )

    def localize(key):
        return key

    bound = bind_data_to_element(element, data, localize)
    assert bound.content == "Hello Test"
    assert bound.visible is True


def test_bind_data_to_element_condition():
    data = DataContext(variables={"show_section": True})
    element = ReportElement(
        element_id="test",
        content_type=ContentType.PARAGRAPH,
        content="Visible content",
        visible=False,
        condition="show_section",
    )

    def localize(key):
        return key

    bound = bind_data_to_element(element, data, localize)
    assert bound.visible is True


def test_resolve_condition_truthy():
    data = DataContext(variables={"flag": True})
    element = ReportElement(element_id="t", content_type=ContentType.PARAGRAPH, content="")
    element.condition = "flag"
    assert resolve_condition(element, data)


def test_resolve_condition_falsy():
    data = DataContext(variables={"flag": False})
    element = ReportElement(element_id="t", content_type=ContentType.PARAGRAPH, content="")
    element.condition = "flag"
    assert not resolve_condition(element, data)


def test_bind_data_to_model():
    data = DataContext(variables={"title": "My Report"})
    model = DocumentModel()
    model.add_element(ReportElement(
        element_id="t", content_type=ContentType.TITLE,
        content="Report: {{title}}", style="title",
    ))

    bound = bind_data_to_model(model, data)
    assert len(bound.elements) == 1
    assert bound.elements[0].content == "Report: My Report"


def test_data_binder_class():
    binder = DataBinder()
    binder.set_variable("name", "World")

    model = DocumentModel()
    model.add_element(ReportElement(
        element_id="g", content_type=ContentType.PARAGRAPH,
        content="Hello {{name}}", style="body",
    ))

    bound = binder.bind(model)
    assert bound.elements[0].content == "Hello World"
