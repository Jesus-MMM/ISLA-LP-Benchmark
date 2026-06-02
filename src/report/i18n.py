from __future__ import annotations

import csv
import os

from .core.exceptions import LocalizationError
from .core.types import LocaleDict

_LOCALE_CACHE: dict[str, LocaleDict] = {}
_FALLBACK_CHAIN: list[str] = []


def load_translations_csv(file_path: str, encoding: str = "utf-8-sig") -> LocaleDict:
    """Load translations from a Godot-style CSV file.

    CSV format (Godot-style):
        key,en,es,fr,...
        report.title,Network Performance Report,Informe de Rendimiento de Red,...

    The first column must be ``key``. Subsequent columns are language codes.
    Each row maps a translation key to its localized strings.

    Args:
        file_path: Path to the translations CSV file.
        encoding: File encoding (default: utf-8-sig for BOM support).

    Returns:
        LocaleDict mapping language codes to translation dictionaries.

    Raises:
        LocalizationError: If the file cannot be loaded.
    """
    cache_key = file_path
    if cache_key in _LOCALE_CACHE:
        return _LOCALE_CACHE[cache_key]

    if not os.path.exists(file_path):
        raise LocalizationError("locale_file", file_path,
                                 f"Translations CSV not found: {file_path}")

    result: LocaleDict = {}
    try:
        with open(file_path, encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise LocalizationError("locale_file", file_path,
                                         "Empty translations CSV file")

            languages = [lang for lang in reader.fieldnames if lang != "key"]
            for lang in languages:
                result[lang] = {}

            for row in reader:
                key = row.get("key", "").strip()
                if not key or key.startswith(("#", ";")):
                    continue
                for lang in languages:
                    value = row.get(lang, "").strip()
                    if value:
                        result[lang][key] = value

    except csv.Error as e:
        raise LocalizationError("locale_file", file_path,
                                 f"CSV parsing error: {e}") from e
    except OSError as e:
        raise LocalizationError("locale_file", file_path,
                                 f"Error reading translations CSV: {e}") from e

    _LOCALE_CACHE[cache_key] = result
    return result


def load_locale_dir(directory: str, encoding: str = "utf-8-sig") -> LocaleDict:
    """Load all translations from CSV files in a directory.

    Looks for ``translations.csv`` files in the given directory.

    Args:
        directory: Path to directory containing translation CSV files.
        encoding: File encoding.

    Returns:
        Merged LocaleDict with all loaded languages.
    """
    merged: LocaleDict = {}
    if not os.path.isdir(directory):
        return merged

    for filename in sorted(os.listdir(directory)):
        if filename == "translations.csv":
            file_path = os.path.join(directory, filename)
            try:
                locale = load_translations_csv(file_path, encoding)
                merged.update(locale)
            except LocalizationError:
                continue

    return merged


def get_text(
    key: str,
    language: str,
    locale_dict: LocaleDict,
    fallback_language: str = "en",
    raise_on_missing: bool = False,
) -> str:
    """Resolve a localization key for the given language.

    Falls back to fallback_language if the key is not found
    in the requested language.

    Args:
        key: The localization key (e.g. "report.title").
        language: Target language code.
        locale_dict: Loaded locale dictionary.
        fallback_language: Fallback language code.
        raise_on_missing: If True, raises LocalizationError on missing key.

    Returns:
        The translated string.

    Raises:
        LocalizationError: If raise_on_missing and key not found.
    """
    if language in locale_dict and key in locale_dict[language]:
        return locale_dict[language][key]

    if fallback_language in locale_dict and key in locale_dict[fallback_language]:
        return locale_dict[fallback_language][key]

    for lang_code in _FALLBACK_CHAIN:
        if lang_code in locale_dict and key in locale_dict[lang_code]:
            return locale_dict[lang_code][key]

    if raise_on_missing:
        raise LocalizationError(key, language)

    return key


def set_fallback_chain(languages: list[str]) -> None:
    """Set the fallback language resolution chain.

    Args:
        languages: Ordered list of language codes to try.
    """
    global _FALLBACK_CHAIN
    _FALLBACK_CHAIN = languages


class Localizer:
    """Convenience class for locale resolution in the report pipeline."""

    def __init__(
        self,
        locale_dict: LocaleDict,
        language: str = "en",
        fallback_language: str = "en",
        locale_dir: str | None = None,
    ) -> None:
        """Inicializa el localizador con un diccionario de traducciones y configuración de idioma."""
        self.locale_dict = locale_dict
        self.language = language
        self.fallback_language = fallback_language

        if locale_dir and not locale_dict:
            self.locale_dict = load_locale_dir(locale_dir)

    def get(self, key: str, raise_on_missing: bool = False) -> str:
        """Resolve a localization key.

        Args:
            key: The localization key.
            raise_on_missing: If True, raise on missing key.

        Returns:
            Translated string or the key itself if not found.
        """
        return get_text(
            key=key,
            language=self.language,
            locale_dict=self.locale_dict,
            fallback_language=self.fallback_language,
            raise_on_missing=raise_on_missing,
        )

    def switch_language(self, language: str) -> None:
        """Switch the current language."""
        self.language = language

    def reload(self, locale_dir: str | None = None) -> None:
        """Reload locale data."""
        global _LOCALE_CACHE
        _LOCALE_CACHE = {}
        if locale_dir:
            self.locale_dict = load_locale_dir(locale_dir)


def create_default_localizer(
    locale_dir: str,
    language: str = "en",
    fallback_language: str = "en",
) -> Localizer:
    """Create a Localizer from a locale directory.

    Args:
        locale_dir: Directory containing translation CSV files.
        language: Default language.
        fallback_language: Fallback language.

    Returns:
        Configured Localizer instance.
    """
    locale_dict = load_locale_dir(locale_dir)
    return Localizer(
        locale_dict=locale_dict,
        language=language,
        fallback_language=fallback_language,
    )
