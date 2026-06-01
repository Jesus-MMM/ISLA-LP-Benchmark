from __future__ import annotations

import math
import os

from fpdf import FPDF
from fpdf.enums import Align, XPos, YPos

from ..core.types import (
    DocumentModel, ReportElement, ContentType, StyleDefinition,
    PageConfig,
)
from ..core.exceptions import RenderError, StyleNotFoundError
from ..rich_text import parse_rich_text
from ..styles import get_style
from .base import BaseRenderer, RenderResult


class ReportPDF(FPDF):
    """Extended FPDF class for the report engine."""

    def __init__(self, page_config: PageConfig, styles: dict[str, StyleDefinition]):
        orientation = "P" if page_config.orientation == "portrait" else "L"
        fmt = page_config.size if page_config.size in ("letter", "legal", "a4") else "letter"
        super().__init__(orientation=orientation, format=fmt, unit="mm")
        self.page_config = page_config
        self.styles = styles
        self.set_margins(
            page_config.margin_left,
            page_config.margin_top,
            page_config.margin_right,
        )

    def header(self):
        if not self.page_config.header_enabled:
            return
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "", align=Align.R)

    def footer(self):
        if not self.page_config.footer_enabled:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, f"Page {self.page_no()}", align=Align.C)

    def write_styled_text(self, text: str, style: StyleDefinition) -> None:
        """Write text with the given style."""
        self.set_font(
            style.font_family,
            self._get_font_style(style),
            style.font_size,
        )
        color = self._parse_color(style.color)
        self.set_text_color(*color)

        if style.background_color:
            bg = self._parse_color(style.background_color)
            self.set_fill_color(*bg)

        self.set_x(self.l_margin)
        self.multi_cell(
            w=self.w - self.l_margin - self.r_margin,
            h=style.font_size * style.line_height,
            text=text,
            align=self._get_alignment(style.alignment),
        )

    def write_rich_text(self, text: str, style: StyleDefinition) -> None:
        """Parse and render rich text with inline styling."""
        parsed = parse_rich_text(text)
        if parsed.alignment:
            align = parsed.alignment
        else:
            align = style.alignment

        base_font = style.font_family
        base_size = style.font_size
        base_color = self._parse_color(style.color)
        avail_w = self.w - self.l_margin - self.r_margin

        if parsed.is_list and parsed.list_items:
            for item in parsed.list_items:
                self.set_font(base_font, "", base_size)
                self.set_text_color(*base_color)
                self.cell(5, base_size * style.line_height, "•")
                self.multi_cell(
                    w=avail_w - 5,
                    h=base_size * style.line_height,
                    text=item,
                    align=self._get_alignment(align),
                )
            return

        for span in parsed.spans:
            font_style = ""
            if span.bold:
                font_style += "B"
            if span.italic:
                font_style += "I"
            if span.underline:
                font_style += "U"

            size = span.size or base_size
            self.set_font(span.font or base_font, font_style, size)

            if span.color:
                self.set_text_color(*self._parse_color(span.color))
            else:
                self.set_text_color(*base_color)

            text = span.text
            if text:
                self.set_x(self.l_margin)
                self.multi_cell(
                    w=avail_w,
                    h=size * style.line_height,
                    text=text,
                    align=self._get_alignment(align),
                )

    def _get_font_style(self, style: StyleDefinition) -> str:
        style_str = ""
        if style.bold:
            style_str += "B"
        if style.italic:
            style_str += "I"
        if style.underline:
            style_str += "U"
        return style_str

    def _get_alignment(self, align: str) -> Align:
        mapping = {
            "left": Align.L,
            "center": Align.C,
            "right": Align.R,
            "justify": Align.J,
        }
        return mapping.get(align, Align.L)

    def _parse_color(self, color: str) -> tuple[int, int, int]:
        color = color.lstrip("#")
        if len(color) == 6:
            try:
                return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))
            except ValueError:
                return (0, 0, 0)
        return (0, 0, 0)


class PDFRenderer(BaseRenderer):
    """Renders document models to PDF using fpdf2."""

    def render(self, model: DocumentModel, output_path: str) -> RenderResult:
        result = RenderResult(success=False, output_path=output_path)
        try:
            model = self.pre_render(model)
            pdf = self._build_pdf(model)
            pdf.output(output_path)
            result.success = True
            result.pages = pdf.pages_count if hasattr(pdf, 'pages_count') else 0
            result = self.post_render(model, result)
        except RenderError:
            raise
        except Exception as e:
            result.errors.append(str(e))
            raise RenderError(f"PDF rendering failed: {e}") from e
        return result

    def _build_pdf(self, model: DocumentModel) -> ReportPDF:
        styles = {**model.styles}
        all_styles = {**styles}

        pdf = ReportPDF(model.page_config, all_styles)
        pdf.set_auto_page_break(auto=True, margin=model.page_config.margin_bottom)

        elements = [e for e in model.elements if e.visible]
        needs_page = True
        for element in elements:
            if needs_page:
                pdf.add_page()
                needs_page = False
            self._render_element(pdf, element, all_styles, model)
            if element.content_type == ContentType.PAGE_BREAK:
                needs_page = True

        return pdf

    def _render_element(
        self,
        pdf: ReportPDF,
        element: ReportElement,
        styles: dict[str, StyleDefinition],
        model: DocumentModel,
    ) -> None:
        try:
            style = get_style(element.style, styles)
        except StyleNotFoundError:
            style = get_style("default", styles)

        if element.content_type == ContentType.TITLE:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.SUBTITLE:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.HEADING:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.PARAGRAPH:
            pdf.ln(style.spacing_before)
            if element.metadata.get("rich_text", True):
                pdf.write_rich_text(element.content, style)
            else:
                pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.ABSTRACT:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.SPACER:
            height = float(element.metadata.get("height", 5))
            pdf.ln(height)

        elif element.content_type == ContentType.PAGE_BREAK:
            pass

        elif element.content_type == ContentType.IMAGE:
            self._render_image(pdf, element, style, styles)

        elif element.content_type == ContentType.TABLE:
            self._render_table(pdf, element, style, styles)

        elif element.content_type == ContentType.CITATION:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(f"[{element.content}]", style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.REFERENCE:
            pdf.ln(style.spacing_before)
            if style.indent:
                pdf.set_x(pdf.get_x() + style.indent)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.CAPTION:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.NOTE:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.CODE_BLOCK:
            self._render_code_block(pdf, element, style)

        elif element.content_type == ContentType.LIST:
            list_items = element.metadata.get("items") or [
                line.strip() for line in element.content.split("\n") if line.strip()
            ]
            if not list_items:
                return
            pdf.ln(style.spacing_before)
            bullet = "-"
            avail_w = pdf.w - pdf.l_margin - pdf.r_margin
            for item in list_items:
                item_text = str(item)
                lines = item_text.split("\n")
                for li, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    if li == 0:
                        pdf.set_x(pdf.l_margin)
                        pdf.cell(5, style.font_size * style.line_height, bullet)
                        pdf.multi_cell(w=avail_w - 5, h=style.font_size * style.line_height, text=line)
                    else:
                        pdf.set_x(pdf.l_margin + 5)
                        pdf.multi_cell(w=avail_w - 5, h=style.font_size * style.line_height, text=line)
            pdf.ln(style.spacing_after)

        elif element.content_type == ContentType.CUSTOM:
            pass

        elif element.content_type == ContentType.DATA_BLOCK:
            pdf.ln(style.spacing_before)
            pdf.write_styled_text(element.content, style)
            pdf.ln(style.spacing_after)

    def _render_image(
        self,
        pdf: ReportPDF,
        element: ReportElement,
        style: StyleDefinition,
        styles: dict[str, StyleDefinition],
    ) -> None:
        image_path = element.content
        if not os.path.exists(image_path):
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 5, f"[Image not found: {image_path}]")
            self.context.add_warning(f"Image not found: {image_path}")
            return

        caption = element.metadata.get("caption", "")
        width = element.metadata.get("width")
        height = element.metadata.get("height")

        if width:
            width = float(width)
        else:
            page_w = pdf.page_config.width
            margin_l = pdf.page_config.margin_left
            margin_r = pdf.page_config.margin_right
            width = page_w - margin_l - margin_r - 20

        pdf.ln(style.spacing_before)
        if style.alignment == "center":
            pdf.set_x(pdf.l_margin + (pdf.w - pdf.l_margin - pdf.r_margin - width) / 2)

        try:
            pdf.image(image_path, w=width, h=float(height) if height else 0)
        except Exception as e:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 5, f"[Image error: {e}]")
            self.context.add_warning(f"Image render error: {e}")

        if caption:
            caption_style = get_style("caption", styles)
            pdf.ln(caption_style.spacing_before)
            pdf.write_styled_text(caption, caption_style)

        pdf.ln(style.spacing_after)

    def _measure_col_widths(
        self,
        pdf: ReportPDF,
        headers: list[str],
        rows: list[list[str]],
        header_style: StyleDefinition,
        body_style: StyleDefinition,
        padding: float,
    ) -> list[float]:
        n = len(headers)
        widths = [0.0] * n
        pdf.set_font(header_style.font_family, pdf._get_font_style(header_style), header_style.font_size)
        for i, h in enumerate(headers):
            widths[i] = max(widths[i], pdf.get_string_width(str(h)))
        pdf.set_font(body_style.font_family, "", body_style.font_size)
        for row in rows:
            for i, cell in enumerate(row):
                if i < n:
                    widths[i] = max(widths[i], pdf.get_string_width(str(cell)))
        widths = [w + padding * 2 for w in widths]
        return widths

    def _render_table(
        self,
        pdf: ReportPDF,
        element: ReportElement,
        style: StyleDefinition,
        styles: dict[str, StyleDefinition],
    ) -> None:
        headers = element.metadata.get("headers", [])
        rows = element.metadata.get("rows", [])
        caption = element.metadata.get("caption", "")

        if not headers and not rows:
            return

        if caption:
            caption_style = get_style("caption", styles)
            pdf.ln(caption_style.spacing_before)
            pdf.write_styled_text(caption, caption_style)

        header_style_name = element.metadata.get("header_style", "apa_table_header")
        header_style = get_style(header_style_name, styles)

        page_w = pdf.page_config.width
        margin_l = pdf.page_config.margin_left
        margin_r = pdf.page_config.margin_right
        available_w = page_w - margin_l - margin_r
        padding = style.padding or 4

        col_widths = self._measure_col_widths(pdf, headers, rows, header_style, style, padding)
        total = sum(col_widths)
        if total > available_w:
            scale = available_w / total
            col_widths = [w * scale for w in col_widths]
        elif total < available_w:
            extra = (available_w - total) / len(col_widths)
            col_widths = [w + extra for w in col_widths]

        pdf.ln(style.spacing_before)
        pdf.set_draw_color(*pdf._parse_color(style.border_color))
        pdf.set_line_width(style.border_width)

        # -- draw headers (single line) --
        pdf.set_font(
            header_style.font_family,
            pdf._get_font_style(header_style),
            header_style.font_size,
        )
        header_color = pdf._parse_color(header_style.color)
        pdf.set_text_color(*header_color)
        h_bg = pdf._parse_color(header_style.background_color) if header_style.background_color else None
        if h_bg:
            pdf.set_fill_color(*h_bg)
        header_h = header_style.font_size * (header_style.line_height or 1.2) + padding
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], header_h, str(header), border=1, align=Align.C, fill=h_bg is not None)
        pdf.ln()

        # -- draw body rows with dynamic wrapping --
        body_style = style
        body_font_size = body_style.font_size
        line_h = body_font_size * (body_style.line_height or 1.2)
        row_bg_color = (250, 250, 250)

        for r, row in enumerate(rows):
            pdf.set_font(body_style.font_family, "", body_font_size)
            body_color = pdf._parse_color(body_style.color)
            pdf.set_text_color(*body_color)

            # 1) calculate how many wrapped lines each cell needs
            max_lines = 1
            for i, cell in enumerate(row):
                if i >= len(col_widths):
                    break
                cw = col_widths[i] - padding
                if cw <= 1:
                    cw = col_widths[i] * 0.8
                str_w = pdf.get_string_width(str(cell))
                if str_w > 1 and cw > 0:
                    lines = max(1, math.ceil(str_w / cw))
                    max_lines = max(max_lines, lines)

            row_h = max_lines * line_h + padding
            y_start = pdf.get_y()
            x_start = margin_l

            # 2) page break if this row does not fit
            if y_start + row_h > pdf.h - pdf.b_margin:
                pdf.add_page()
                y_start = pdf.get_y()

            use_bg = r % 2 == 0

            # 3) draw each cell
            for i, cell in enumerate(row):
                if i >= len(col_widths):
                    break
                cw = col_widths[i]
                cx = x_start + sum(col_widths[:i])

                # background & border
                rect_style = "DF" if use_bg else "D"
                if use_bg:
                    pdf.set_fill_color(*row_bg_color)
                pdf.rect(cx, y_start, cw, row_h, style=rect_style)

                # text with wrapping
                text_w = cw - padding
                if text_w < 4:
                    text_w = cw * 0.85
                pdf.set_xy(cx + padding / 2, y_start + padding / 2)
                pdf.multi_cell(
                    w=text_w,
                    h=line_h,
                    text=str(cell),
                    border=0,
                    align=Align.L,
                    new_x=XPos.RIGHT,
                    new_y=YPos.TOP,
                )

            # 4) advance to next row
            pdf.set_xy(x_start, y_start + row_h)

        pdf.ln(style.spacing_after)

    def _render_code_block(
        self,
        pdf: ReportPDF,
        element: ReportElement,
        style: StyleDefinition,
    ) -> None:
        pdf.ln(style.spacing_before)
        has_bg = bool(style.background_color)
        if has_bg:
            pdf.set_fill_color(*pdf._parse_color(style.background_color))
        pdf.set_font(style.font_family, "", style.font_size)
        pdf.set_text_color(*pdf._parse_color(style.color))

        indent = pdf.l_margin + style.indent
        block_w = pdf.w - pdf.r_margin - indent
        line_h = style.font_size * 1.4
        for line in element.content.split("\n"):
            pdf.set_x(indent)
            pdf.cell(block_w, line_h, line, fill=has_bg, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(style.spacing_after)
