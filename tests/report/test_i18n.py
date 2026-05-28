from __future__ import annotations

import json
import tempfile
import os

import pytest

from src.report.i18n import (
    load_locale, load_locale_dir, get_text, Localizer,
    set_fallback_chain,
)
from src.report.core.exceptions import LocalizationError


EN_LOCALE = {
    "language": "en",
    "translations": {
        "report.title": "Network Report",
        "report.intro": "Introduction",
    },
}

ES_LOCALE = {
    "language": "es",
    "translations": {
        "report.title": "Informe de Red",
        "report.intro": "Introducción",
    },
}


def _write_locale(data, suffix=".json"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    json.dump(data, f)
    f.close()
    return f.name


def test_load_locale():
    path = _write_locale(EN_LOCALE)
    try:
        locale = load_locale(path)
        assert "en" in locale
        assert locale["en"]["report.title"] == "Network Report"
    finally:
        os.unlink(path)


def test_load_locale_file_not_found():
    with pytest.raises(LocalizationError):
        load_locale("nonexistent.json")


def test_load_locale_dir():
    d = tempfile.mkdtemp()
    try:
        en_path = os.path.join(d, "en.json")
        with open(en_path, "w", encoding="utf-8") as f:
            json.dump(EN_LOCALE, f)
        es_path = os.path.join(d, "es.json")
        with open(es_path, "w", encoding="utf-8") as f:
            json.dump(ES_LOCALE, f)

        locale = load_locale_dir(d)
        assert "en" in locale
        assert "es" in locale
    finally:
        os.unlink(en_path)
        os.unlink(es_path)
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
