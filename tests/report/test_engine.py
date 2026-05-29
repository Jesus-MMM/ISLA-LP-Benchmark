from __future__ import annotations

import os

from src.report.engine import ReportEngine
from src.report.core.types import PageConfig, ContentType


SAMPLE_CSV = """type,id,content,style,language,visible,order
title,main_title,Test Report,title,en,true,1
paragraph,intro,This is a [bold]test[/bold] paragraph.,body,en,true,2
page_break,pb1,,default,en,true,3
heading,section1,Section One,heading,en,true,4
paragraph,p1,Some content here.,body,en,true,5
"""


def test_engine_basic():
    engine = ReportEngine(language="en")
    engine.load_csv_string(SAMPLE_CSV)
    model = engine.build_document_model()
    assert len(model.elements) == 5
    assert model.elements[0].content_type == ContentType.TITLE
    assert model.elements[0].content == "Test Report"


def test_engine_with_variables():
    engine = ReportEngine(language="en")
    csv = """type,id,content,style,language,visible,order
title,main,{{title}},title,en,true,1
paragraph,p1,Hello {{name}},body,en,true,2
"""
    engine.load_csv_string(csv)
    engine.set_variable("title", "Dynamic Title")
    engine.set_variable("name", "World")

    model = engine.build_document_model()
    assert model.elements[0].content == "Dynamic Title"
    assert model.elements[1].content == "Hello World"


def test_engine_render_pdf(tmp_path):
    engine = ReportEngine(language="en")
    engine.load_csv_string(SAMPLE_CSV)

    output_path = os.path.join(tmp_path, "test_output.pdf")
    result = engine.render_pdf(output_path)
    assert result.success
    assert os.path.exists(output_path)


def test_engine_render_html(tmp_path):
    engine = ReportEngine(language="en")
    engine.load_csv_string(SAMPLE_CSV)

    output_path = os.path.join(tmp_path, "test_output.html")
    result = engine.render_html(output_path)
    assert result.success
    assert os.path.exists(output_path)

    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert "Test Report" in content


def test_engine_render_markdown(tmp_path):
    engine = ReportEngine(language="en")
    engine.load_csv_string(SAMPLE_CSV)

    output_path = os.path.join(tmp_path, "test_output.md")
    result = engine.render_markdown(output_path)
    assert result.success
    assert os.path.exists(output_path)

    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert "# Test Report" in content


def test_engine_with_localization(tmp_path):
    locale_dir = os.path.join(tmp_path, "locales")
    os.makedirs(locale_dir)

    with open(os.path.join(locale_dir, "translations.csv"), "w", encoding="utf-8") as f:
        f.write("""\
key,en
report.title,Localized Report
report.intro,Introduction text
""")

    csv = """type,id,content,style,language,visible,order
title,main,report.title,title,en,true,1
paragraph,intro,report.intro,body,en,true,2
"""
    engine = ReportEngine(language="en", locale_dir=locale_dir)
    engine.load_csv_string(csv)

    model = engine.build_document_model()
    assert model.elements[0].content == "Localized Report"
    assert model.elements[1].content == "Introduction text"


def test_engine_validate():
    engine = ReportEngine(language="en")
    engine.load_csv_string(SAMPLE_CSV)
    validator = engine.validate()
    assert validator is not None


def test_engine_empty():
    engine = ReportEngine()
    model = engine.build_document_model()
    assert len(model.elements) == 0


def test_engine_set_page_config():
    config = PageConfig(width=200, height=300, margin_top=10)
    engine = ReportEngine(page_config=config)
    assert engine.page_config.width == 200
    assert engine.page_config.height == 300
    assert engine.page_config.margin_top == 10
