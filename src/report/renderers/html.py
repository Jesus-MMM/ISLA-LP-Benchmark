from __future__ import annotations

import os
from html import escape

from src.utils.logging import get_logger
from ..core.types import DocumentModel, ContentType, StyleDefinition
from ..rich_text import parse_rich_text
from .base import BaseRenderer, RenderResult

logger = get_logger(__name__)


class HTMLRenderer(BaseRenderer):
    """Renders document models to HTML."""

    def render(self, model: DocumentModel, output_path: str) -> RenderResult:
        """Renderiza un modelo de documento a HTML y lo escribe en un archivo.

        Args:
            model: Modelo del documento a renderizar.
            output_path: Ruta del archivo de salida.

        Returns:
            RenderResult con el resultado de la renderización.
        """
        try:
            html = self._build_html(model, output_path)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            return RenderResult(success=True, output_path=output_path, content=html)
        except Exception as e:
            return RenderResult(success=False, errors=[str(e)])

    def render_to_string(self, model: DocumentModel) -> str:
        """Renderiza un modelo de documento a HTML y devuelve el resultado como cadena.

        Args:
            model: Modelo del documento a renderizar.

        Returns:
            Cadena con el contenido HTML generado.
        """
        return self._build_html(model, "")

    def _build_html(self, model: DocumentModel, output_path: str = "") -> str:
        parts: list[str] = []
        parts.append("<!DOCTYPE html>")
        parts.append('<html lang="{}">'.format(model.language))
        parts.append("<head>")
        parts.append('<meta charset="UTF-8">')
        title = escape(model.title or "Report")
        parts.append(f"<title>{title}</title>")
        parts.append(self._build_styles(model.styles))
        parts.append("</head>")
        parts.append("<body>")

        for element in model.elements:
            if not element.visible:
                continue
            html = self._render_element_html(element, model.styles, output_path)
            if html:
                parts.append(html)

        parts.append("</body>")
        parts.append("</html>")
        return "\n".join(parts)

    def _build_styles(self, styles: dict[str, StyleDefinition]) -> str:
        css_parts: list[str] = []
        css_parts.append("<style>")
        css_parts.append("""
body { font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 2.0;
       margin: 1in; color: #000; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; }
th, td { border: 1px solid #000; padding: 4px 8px; text-align: center; }
th { font-weight: bold; }
img { max-width: 100%; height: auto; }
h1 { font-size: 24pt; text-align: center; font-weight: bold; }
h2 { font-size: 14pt; text-align: center; font-weight: bold; }
h3 { font-size: 12pt; font-weight: bold; }
.apa-abstract { margin: 20px 0; }
.apa-reference { padding-left: 36pt; text-indent: -36pt; }
.caption { font-style: italic; font-size: 10pt; text-align: center; }
""")
        css_parts.append("</style>")
        return "\n".join(css_parts)

    def _render_element_html(
        self,
        element,
        styles: dict[str, StyleDefinition],
        output_path: str = "",
    ) -> str:
        content = escape(element.content)

        if element.content_type == ContentType.TITLE:
            return f"<h1>{content}</h1>"
        elif element.content_type == ContentType.SUBTITLE:
            return f"<h2 style='font-style: italic;'>{content}</h2>"
        elif element.content_type == ContentType.HEADING:
            return f"<h2>{content}</h2>"
        elif element.content_type == ContentType.PARAGRAPH:
            rich = parse_rich_text(element.content)
            if rich.is_list and rich.list_items:
                items = "\n".join(f"<li>{escape(i)}</li>" for i in rich.list_items)
                return f"<ul>\n{items}\n</ul>"
            return f"<p>{content}</p>"
        elif element.content_type == ContentType.ABSTRACT:
            return f'<div class="apa-abstract"><p>{content}</p></div>'
        elif element.content_type == ContentType.SPACER:
            height = element.metadata.get("height", 5)
            return f'<div style="height: {height}mm;"></div>'
        elif element.content_type == ContentType.PAGE_BREAK:
            return '<div style="page-break-after: always;"></div>'
        elif element.content_type == ContentType.IMAGE:
            caption = element.metadata.get("caption", "")
            caption_html = ""
            if caption:
                caption_html = f'<p class="caption">{escape(caption)}</p>'
            src = element.content
            if output_path:
                out_dir = os.path.dirname(os.path.abspath(output_path))
                img_abs = os.path.abspath(src)
                try:
                    rel = os.path.relpath(img_abs, out_dir)
                    src = rel.replace("\\", "/")
                except (ValueError, OSError):
                    logger.warning("Could not compute relative path for image: %s", src)
            return f'<div style="text-align: center;"><img src="{escape(src)}" alt="{escape(caption)}"/>{caption_html}</div>'
        elif element.content_type == ContentType.TABLE:
            return self._render_table_html(element)
        elif element.content_type == ContentType.REFERENCE:
            return f'<p class="apa-reference">{content}</p>'
        elif element.content_type == ContentType.CAPTION:
            return f'<p class="caption">{content}</p>'
        elif element.content_type == ContentType.NOTE:
            return f'<p style="font-size: 8pt; color: #555; font-style: italic;">{content}</p>'
        elif element.content_type == ContentType.CODE_BLOCK:
            return f'<pre style="background: #f5f5f5; border: 1px solid #ccc; padding: 4px; font-size: 9pt;">{content}</pre>'
        elif element.content_type == ContentType.LIST:
            items = element.metadata.get("items") or [
                line.strip() for line in element.content.split("\n") if line.strip()
            ]
            lis = "\n".join(f"<li>{escape(i)}</li>" for i in items)
            return f"<ul>\n{lis}\n</ul>\n"
        elif element.content_type == ContentType.CITATION:
            return f'<span class="citation">[{content}]</span>'
        return ""

    def _render_table_html(self, element) -> str:
        headers = element.metadata.get("headers", [])
        rows = element.metadata.get("rows", [])
        if not headers and not rows:
            return ""

        caption = element.metadata.get("caption", "")
        caption_html = f'<p class="caption">{escape(caption)}</p>' if caption else ""

        thead = ""
        if headers:
            thead = "<thead><tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr></thead>"

        tbody = ""
        if rows:
            tbody = "<tbody>"
            for row in rows:
                tbody += "<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>"
            tbody += "</tbody>"

        return f"{caption_html}<table>{thead}{tbody}</table>"
