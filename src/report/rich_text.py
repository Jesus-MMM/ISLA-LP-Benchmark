from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .core.exceptions import TagParseError


@dataclass
class TextSpan:
    """A styled text span produced by the tag parser."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[str] = None
    size: Optional[int] = None
    alignment: Optional[str] = None
    font: Optional[str] = None
    strikethrough: bool = False
    superscript: bool = False
    subscript: bool = False


@dataclass
class StyledText:
    """Result of parsing rich text tags."""
    spans: list[TextSpan] = field(default_factory=list)
    alignment: Optional[str] = None
    is_list: bool = False
    list_items: list[str] = field(default_factory=list)
    raw_text: str = ""


TAG_PATTERN = re.compile(r'\[/?(\w+)(?:=([^\]]*))?\]')
VALID_TAGS = {
    "b", "bold",
    "i", "italic",
    "u", "underline",
    "s", "strikethrough",
    "sup", "superscript",
    "sub", "subscript",
    "color",
    "size",
    "font",
    "center",
    "right",
    "left",
    "justify",
    "list",
    "item",
}

CLOSING_TAGS = {
    "b", "bold", "i", "italic", "u", "underline",
    "s", "strikethrough", "sup", "superscript", "sub", "subscript",
    "color", "size", "font",
}

SELF_CLOSING_ALIGNMENT = {"center", "right", "left", "justify"}


def parse_rich_text(text: str, strict: bool = False) -> StyledText:
    """Parse rich text tags into a structured StyledText object.

    Supports nested tags. Malformed tags are handled gracefully
    (left as-is) unless strict mode is enabled.

    Args:
        text: The raw text containing [tags].
        strict: If True, raise TagParseError on malformed tags.

    Returns:
        A StyledText with resolved spans.

    Raises:
        TagParseError: If strict mode and malformed tags found.
    """
    if not text:
        return StyledText(spans=[TextSpan(text="")], raw_text="")

    result = StyledText(raw_text=text)
    stack: list[dict] = []
    pos = 0
    current_span = TextSpan(text="")
    alignment: Optional[str] = None

    def _push_span():
        nonlocal current_span
        if current_span.text or current_span.bold or current_span.italic:
            result.spans.append(current_span)
        current_span = TextSpan(text="")

    def _apply_tags(span: TextSpan, tags: list[dict]) -> TextSpan:
        for tag in reversed(tags):
            tagname = tag["name"]
            if tagname in ("b", "bold"):
                span.bold = True
            elif tagname in ("i", "italic"):
                span.italic = True
            elif tagname in ("u", "underline"):
                span.underline = True
            elif tagname in ("s", "strikethrough"):
                span.strikethrough = True
            elif tagname in ("sup", "superscript"):
                span.superscript = True
            elif tagname in ("sub", "subscript"):
                span.subscript = True
            elif tagname == "color":
                span.color = tag.get("value")
            elif tagname == "size":
                try:
                    span.size = int(tag["value"])
                except (ValueError, TypeError):
                    pass
            elif tagname == "font":
                span.font = tag.get("value")
        return span

    while pos < len(text):
        match = TAG_PATTERN.search(text, pos)
        if not match:
            remaining = text[pos:]
            if remaining:
                current_span.text += remaining
            pos = len(text)
            continue

        if match.start() > pos:
            current_span.text += text[pos:match.start()]

        tag_text = match.group(0)
        is_closing = tag_text.startswith("[/")
        tag_name = match.group(1).lower()
        tag_value = match.group(2)

        if tag_name in ("/b", "/bold", "/i", "/italic", "/u", "/underline",
                         "/s", "/strikethrough", "/sup", "/superscript",
                         "/sub", "/subscript", "/color", "/size", "/font"):
            is_closing = True
            tag_name = tag_name[1:]

        if tag_name not in VALID_TAGS:
            current_span.text += tag_text
            pos = match.end()
            continue

        if is_closing:
            if tag_name == "item":
                _push_span()
                current_span = TextSpan(text="__ITEM_SEP__")
                _push_span()
                current_span = TextSpan(text="")
                pos = match.end()
                continue
            if tag_name == "list":
                _push_span()
                pos = match.end()
                continue
            if tag_name not in CLOSING_TAGS:
                current_span.text += tag_text
                pos = match.end()
                continue

            found = False
            for j in range(len(stack) - 1, -1, -1):
                if stack[j]["name"] == tag_name:
                    _push_span()
                    current_span.text = ""
                    stack.pop(j)
                    current_span = _apply_tags(TextSpan(text=""), stack)
                    found = True
                    break
            if not found and strict:
                raise TagParseError(f"Unmatched closing tag '[/{tag_name}]'",
                                     position=match.start(), tag=tag_name)
            if not found:
                current_span.text += tag_text
        else:
            if tag_name in CLOSING_TAGS:
                _push_span()
                current_span = TextSpan(text="")
                stack.append({"name": tag_name, "value": tag_value})
                current_span = _apply_tags(TextSpan(text=""), stack)
            elif tag_name in SELF_CLOSING_ALIGNMENT:
                alignment = tag_name
            elif tag_name == "item":
                _push_span()
                result.is_list = True
                current_span = TextSpan(text="")
                pos = match.end()
                continue
            elif tag_name == "list":
                _push_span()
                result.is_list = True
                pos = match.end()
                continue

        pos = match.end()

    _push_span()

    if result.is_list:
        list_items = _extract_list_items(result.spans)
        if list_items:
            result.list_items = list_items
            result.spans = []

    result.alignment = alignment
    return result


def _extract_list_items(spans: list[TextSpan]) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for span in spans:
        text = span.text
        if text == "__ITEM_SEP__":
            if current:
                items.append(" ".join(current))
                current = []
            continue
        if not text.strip():
            continue
        current.append(text.strip())
    if current:
        items.append(" ".join(current))
    return items


def strip_tags(text: str) -> str:
    """Remove all rich text tags from a string."""
    return TAG_PATTERN.sub("", text)


def has_tags(text: str) -> bool:
    """Check if a string contains rich text tags."""
    return bool(TAG_PATTERN.search(text))


def render_to_ansi(text: str) -> str:
    """Convert rich text tags to ANSI escape codes for terminal display."""
    ansi_map = {
        "bold": "\033[1m",
        "/bold": "\033[22m",
        "b": "\033[1m",
        "/b": "\033[22m",
        "italic": "\033[3m",
        "/italic": "\033[23m",
        "i": "\033[3m",
        "/i": "\033[23m",
        "underline": "\033[4m",
        "/underline": "\033[24m",
        "u": "\033[4m",
        "/u": "\033[24m",
    }

    result = text
    for tag, ansi in ansi_map.items():
        result = result.replace(f"[{tag}]", ansi)
    result = TAG_PATTERN.sub("", result)
    result += "\033[0m"
    return result
