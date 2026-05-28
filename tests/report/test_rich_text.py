from __future__ import annotations

from src.report.rich_text import (
    parse_rich_text, strip_tags, has_tags, TextSpan, StyledText,
)


def test_plain_text():
    result = parse_rich_text("Hello world")
    assert len(result.spans) == 1
    assert result.spans[0].text == "Hello world"


def test_bold_tag():
    result = parse_rich_text("This is [bold]important[/bold] text")
    spans = result.spans
    assert spans[0].text == "This is "
    assert not spans[0].bold
    assert spans[1].text == "important"
    assert spans[1].bold
    assert spans[2].text == " text"


def test_italic_tag():
    result = parse_rich_text("This is [italic]emphasized[/italic] text")
    assert result.spans[1].italic


def test_underline_tag():
    result = parse_rich_text("[underline]underlined[/underline]")
    assert result.spans[0].underline


def test_color_tag():
    result = parse_rich_text("[color=red]red text[/color]")
    assert result.spans[0].color == "red"


def test_size_tag():
    result = parse_rich_text("[size=18]big text[/size]")
    assert result.spans[0].size == 18


def test_nested_tags():
    result = parse_rich_text("[bold]bold and [italic]italic[/italic][/bold]")
    assert len(result.spans) >= 2
    assert result.spans[1].bold
    assert result.spans[1].italic


def test_alignment_tags():
    result = parse_rich_text("[center]centered text[/center]")
    assert result.alignment == "center"


def test_list_tag():
    result = parse_rich_text("[list][item]First[/item][item]Second[/item][/list]")
    assert result.is_list
    assert len(result.list_items) >= 2


def test_strip_tags():
    result = strip_tags("[bold]Hello[/bold] [italic]World[/italic]")
    assert result == "Hello World"


def test_has_tags():
    assert has_tags("[bold]text[/bold]")
    assert not has_tags("plain text")


def test_malformed_tag_graceful():
    result = parse_rich_text("This [unknown]tag[/unknown] is left as-is")
    assert "[unknown]" in result.spans[1].text or "[unknown]" in result.spans[0].text


def test_unmatched_closing_tag():
    result = parse_rich_text("Text [/unmatched]")
    assert result.spans[0].text is not None


def test_short_form_tags():
    result = parse_rich_text("[b]bold[/b] [i]italic[/i] [u]underline[/u]")
    assert result.spans[1].bold
    assert result.spans[3].italic
    assert result.spans[5].underline


def test_short_form_strikethrough():
    result = parse_rich_text("[s]strikethrough[/s]")
    assert result.spans[0].strikethrough


def test_empty_text():
    result = parse_rich_text("")
    assert result.spans[0].text == ""


def test_superscript_subscript():
    result = parse_rich_text("E=mc[sup]2[/sup] H[sub]2[/sub]O")
    assert result.spans[1].superscript or result.spans[2].superscript
