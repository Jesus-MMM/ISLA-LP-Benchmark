from __future__ import annotations

import csv
import tempfile
import os

import pytest

from src.report.i18n import (
    load_translations_csv, load_locale_dir, get_text, Localizer,
    set_fallback_chain,
)
from src.report.core.exceptions import LocalizationError


EN_ES_CSV = """\
key,en,es
report.title,Network Report,Informe de Red
report.intro,Introduction,Introducción
"""

EN_CSV = """\
key,en
report.title,Network Report
report.intro,Introduction
"""

ES_CSV = """\
key,es
report.title,Informe de Red
report.intro,Introducción
"""


def _write_csv(content: str, suffix=".csv"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def test_load_translations_csv():
    path = _write_csv(EN_ES_CSV)
    try:
        locale = load_translations_csv(path)
        assert "en" in locale
        assert "es" in locale
        assert locale["en"]["report.title"] == "Network Report"
        assert locale["es"]["report.title"] == "Informe de Red"
    finally:
        os.unlink(path)


def test_load_locale_file_not_found():
    with pytest.raises(LocalizationError):
        load_translations_csv("nonexistent.csv")


def test_load_locale_dir():
    d = tempfile.mkdtemp()
    try:
        en_path = os.path.join(d, "translations.csv")
        with open(en_path, "w", encoding="utf-8") as f:
            f.write(EN_ES_CSV)

        locale = load_locale_dir(d)
        assert "en" in locale
        assert "es" in locale
        assert locale["en"]["report.title"] == "Network Report"
    finally:
        os.unlink(en_path)
        os.rmdir(d)


def test_load_locale_dir_ignores_non_translation_csv():
    d = tempfile.mkdtemp()
    try:
        not_translations = os.path.join(d, "theme.csv")
        with open(not_translations, "w", encoding="utf-8") as f:
            f.write("section,name,property,value\n")

        locale = load_locale_dir(d)
        assert locale == {}
    finally:
        os.unlink(not_translations)
        os.rmdir(d)


def test_get_text():
    locale = {"en": {"report.title": "Title"}, "es": {"report.title": "Título"}}
    assert get_text("report.title", "en", locale) == "Title"
    assert get_text("report.title", "es", locale) == "Título"


def test_get_text_fallback():
    locale = {"en": {"report.title": "Title"}}
    assert get_text("report.title", "es", locale, fallback_language="en") == "Title"


def test_get_text_missing():
    locale = {"en": {}}
    result = get_text("missing.key", "en", locale)
    assert result == "missing.key"


def test_get_text_raises():
    locale = {"en": {}}
    with pytest.raises(LocalizationError):
        get_text("missing.key", "en", locale, raise_on_missing=True)


def test_localizer_class():
    locale = {"en": {"greeting": "Hello"}}
    localizer = Localizer(locale, language="en")
    assert localizer.get("greeting") == "Hello"
    assert localizer.get("missing") == "missing"


def test_localizer_switch_language():
    locale = {"en": {"greeting": "Hello"}, "es": {"greeting": "Hola"}}
    localizer = Localizer(locale, language="en")
    assert localizer.get("greeting") == "Hello"
    localizer.switch_language("es")
    assert localizer.get("greeting") == "Hola"


def test_fallback_chain():
    set_fallback_chain(["es", "fr"])
    locale = {"en": {"other": "English"}, "es": {"key": "Espanol"}}
    assert get_text("key", "en", locale) == "Espanol"


def test_localizer_from_directory():
    d = tempfile.mkdtemp()
    try:
        csv_path = os.path.join(d, "translations.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(EN_CSV)
        localizer = Localizer({}, language="en", locale_dir=d)
        assert localizer.locale_dict["en"]["report.title"] == "Network Report"
    finally:
        os.unlink(csv_path)
        os.rmdir(d)


def test_load_skips_comments():
    csv_content = """\
key,en,es
# this is a comment
report.title,Network Report,Informe de Red
; also a comment
report.intro,Introduction,Introducción
"""
    path = _write_csv(csv_content)
    try:
        locale = load_translations_csv(path)
        assert locale["en"]["report.title"] == "Network Report"
        assert locale["en"]["report.intro"] == "Introduction"
    finally:
        os.unlink(path)
