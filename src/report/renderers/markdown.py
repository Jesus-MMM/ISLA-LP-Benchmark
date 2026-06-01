from __future__ import annotations

import os

from ..core.types import DocumentModel, ContentType
from ..rich_text import strip_tags
from .base import BaseRenderer, RenderResult


class MarkdownRenderer(BaseRenderer):
    """Renders document models to Markdown."""

    def render(self, model: DocumentModel, output_path: str) -> RenderResult:
        try:
            md = self._build_markdown(model, output_path)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md)
            return RenderResult(success=True, output_path=output_path, content=md)
        except Exception as e:
            return RenderResult(success=False, errors=[str(e)])

    def render_to_string(self, model: DocumentModel) -> str:
        return self._build_markdown(model, "")

    def _build_markdown(self, model: DocumentModel, output_path: str = "") -> str:
        parts: list[str] = []

        if model.title:
            parts.append(f"# {strip_tags(model.title)}")
            parts.append("")

        for element in model.elements:
            if not element.visible:
                continue
            md = self._render_element_md(element, output_path)
            if md:
                parts.append(md)

        return "\n".join(parts)

    def _render_element_md(self, element, output_path: str = "") -> str:
        text = strip_tags(element.content)

        if element.content_type == ContentType.TITLE:
            return f"# {text}\n"
        elif element.content_type == ContentType.SUBTITLE:
            return f"## {text}\n"
        elif element.content_type == ContentType.HEADING:
            level = element.metadata.get("level", 2)
            return f"{'#' * level} {text}\n"
        elif element.content_type == ContentType.PARAGRAPH:
            return f"{text}\n"
        elif element.content_type == ContentType.ABSTRACT:
            return f"> {text}\n"
        elif element.content_type == ContentType.SPACER:
            return ""
        elif element.content_type == ContentType.PAGE_BREAK:
            return "\n---\n"
        elif element.content_type == ContentType.IMAGE:
            caption = element.metadata.get("caption", "")
            alt = caption or "image"
            src = element.content
            if output_path:
                out_dir = os.path.dirname(os.path.abspath(output_path))
                img_abs = os.path.abspath(src)
                try:
                    rel = os.path.relpath(img_abs, out_dir)
                    src = rel.replace("\\", "/")
                except (ValueError, OSError):
                    pass
            return f"![{alt}]({src})\n"
        elif element.content_type == ContentType.TABLE:
            return self._render_table_md(element)
        elif element.content_type == ContentType.REFERENCE:
            return f"- {text}\n"
        elif element.content_type == ContentType.CAPTION:
            return f"*{text}*\n"
        elif element.content_type == ContentType.CODE_BLOCK:
            lang = element.metadata.get("language", "")
            return f"```{lang}\n{element.content}\n```\n"
        elif element.content_type == ContentType.CITATION:
            return f"[{text}]"
        elif element.content_type == ContentType.NOTE:
            return f"*{text}*\n"
        elif element.content_type == ContentType.LIST:
            items = element.metadata.get("items") or [
                line.strip() for line in element.content.split("\n") if line.strip()
            ]
            return "\n".join(f"- {strip_tags(str(i))}" for i in items) + "\n"
        return ""

    def _render_table_md(self, element) -> str:
        headers = element.metadata.get("headers", [])
        rows = element.metadata.get("rows", [])
        if not headers:
            return ""

        caption = element.metadata.get("caption", "")
        result = ""
        if caption:
            result += f"*{caption}*\n\n"

        result += "| " + " | ".join(headers) + " |\n"
        result += "| " + " | ".join("---" for _ in headers) + " |\n"
        for row in rows:
            result += "| " + " | ".join(str(c) for c in row) + " |\n"

        return result + "\n"
