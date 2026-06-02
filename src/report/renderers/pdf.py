from __future__ import annotations

import os

from fpdf import FPDF
from fpdf.enums import Align, XPos, YPos

from ..core.exceptions import RenderError, StyleNotFoundError
from ..core.types import (
    ContentType,
    DocumentModel,
    PageConfig,
    ReportElement,
    StyleDefinition,
)
from ..rich_text import parse_rich_text
from ..styles import get_style
from .base import BaseRenderer, RenderResult


class ReportPDF(FPDF):
    """Extended FPDF class for the report engine."""

    def __init__(self, page_config: PageConfig, styles: dict[str, StyleDefinition]) -> None:
        """Inicializa el documento PDF con la configuración de página y estilos dados.

        Args:
            page_config: Configuración de página (orientación, tamaño, márgenes).
            styles: Diccionario de definiciones de estilo.
        """
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

    def header(self) -> None:
        """Genera el encabezado de cada página del PDF."""
        if not self.page_config.header_enabled:
            return
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "", align=Align.R)

    def footer(self) -> None:
        """Genera el pie de página de cada página del PDF con el número de página."""
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

    # ------------------------------------------------------------------ #
    #  Table-specific constants                                           #
    # ------------------------------------------------------------------ #
    _TABLE_MIN_FONT_SIZE = 5.0       # Minimum font size for table body (pt)
    _TABLE_COMPACT_PADDING = 1.5     # Cell internal padding (mm)
    _TABLE_LINE_HEIGHT_FACTOR = 1.1  # Line height multiplier for table rows
    _TABLE_MAX_COL_PCT = 0.40       # Max fraction of page a single column may occupy
    _TABLE_MIN_COL_MM = 8           # Absolute minimum column width (mm)

    # ------------------------------------------------------------------ #
    #  Main render pipeline                                               #
    # ------------------------------------------------------------------ #

    def render(self, model: DocumentModel, output_path: str) -> RenderResult:
        """
        Renderiza el modelo de documento a PDF.

        Args:
            model: Modelo del documento a renderizar.
            output_path: Ruta de salida para el archivo PDF.

        Returns:
            Resultado del renderizado.
        """
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

    # ------------------------------------------------------------------ #
    #  Element dispatch                                                   #
    # ------------------------------------------------------------------ #

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

        if element.content_type == ContentType.TITLE or element.content_type == ContentType.SUBTITLE or element.content_type == ContentType.HEADING:
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

        elif element.content_type == ContentType.CAPTION or element.content_type == ContentType.NOTE:
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

    # ------------------------------------------------------------------ #
    #  Image rendering                                                    #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    #  Word-boundary text wrapping  (NEVER breaks words)                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _wrap_text_at_words(
        pdf: ReportPDF,
        text: str,
        max_width: float,
        font_family: str,
        font_style: str,
        font_size: float,
    ) -> list[str]:
        """Wrap *text* so that it fits within *max_width*, breaking ONLY at
        word boundaries.  A word is never split across two lines.

        Returns a list of lines.
        """
        pdf.set_font(font_family, font_style, font_size)

        # Guard: if max_width is impossibly small, return the text as-is
        # (the caller will handle overflow at a higher level).
        if max_width <= 0:
            return [str(text)]

        paragraphs = str(text).split("\n")
        all_lines: list[str] = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                all_lines.append("")
                continue

            words = para.split()
            if not words:
                all_lines.append("")
                continue

            current_line = words[0]
            for word in words[1:]:
                candidate = f"{current_line} {word}"
                if pdf.get_string_width(candidate) <= max_width:
                    current_line = candidate
                else:
                    # Current line is full — flush it and start a new one.
                    all_lines.append(current_line)
                    current_line = word
            all_lines.append(current_line)

        return all_lines if all_lines else [""]

    # ------------------------------------------------------------------ #
    #  Auto-fit table font size                                           #
    # ------------------------------------------------------------------ #

    def _auto_fit_table(
        self,
        pdf: ReportPDF,
        headers: list[str],
        rows: list[list[str]],
        body_style: StyleDefinition,
        header_style: StyleDefinition,
        available_w: float,
        padding: float,
    ) -> tuple[float, float, list[float]]:
        """Find the smallest font size that lets every column be at least as
        wide as its longest word, and return the column widths.

        Returns ``(body_font_size, header_font_size, col_widths)``.
        """
        n = len(headers)
        if n == 0:
            return body_style.font_size, header_style.font_size, []

        base_body = body_style.font_size
        base_hdr = header_style.font_size
        hdr_ratio = base_hdr / base_body if base_body > 0 else 1.0
        min_fs = self._TABLE_MIN_FONT_SIZE

        # --- Step 1: measure the longest word per column at base font size ---
        body_word_w = [0.0] * n
        pdf.set_font(body_style.font_family, "", base_body)
        for row in rows:
            for i, cell in enumerate(row):
                if i < n:
                    words = str(cell).split()
                    if words:
                        body_word_w[i] = max(
                            body_word_w[i],
                            max(pdf.get_string_width(w) for w in words),
                        )

        hdr_word_w = [0.0] * n
        pdf.set_font(
            header_style.font_family,
            pdf._get_font_style(header_style),
            base_hdr,
        )
        for i, h in enumerate(headers):
            if i < n:
                words = str(h).split()
                if words:
                    hdr_word_w[i] = max(
                        hdr_word_w[i],
                        max(pdf.get_string_width(w) for w in words),
                    )

        # Normalise header widths to body-font-size equivalent
        if base_hdr > 0 and base_body > 0:
            scale_hdr_to_body = base_body / base_hdr
            hdr_word_w_body = [w * scale_hdr_to_body for w in hdr_word_w]
        else:
            hdr_word_w_body = hdr_word_w

        # Per-column: longest word across header + body (in body-size units)
        min_word_w = [max(bw, hw) for bw, hw in zip(body_word_w, hdr_word_w_body)]

        # --- Step 2: compute the font size that makes the table fit ---
        padding_total = n * 2 * padding
        content_w_at_base = sum(min_word_w)

        if content_w_at_base + padding_total <= available_w:
            body_fs = base_body
        else:
            available_for_content = available_w - padding_total
            if available_for_content <= 0 or content_w_at_base <= 0:
                body_fs = min_fs
            else:
                body_fs = max(min_fs, base_body * (available_for_content / content_w_at_base))

        hdr_fs = max(min_fs, body_fs * hdr_ratio)

        # --- Step 3: build column widths at the determined font size ---
        fs_ratio = body_fs / base_body if base_body > 0 else 1.0
        col_widths = [w * fs_ratio + 2 * padding for w in min_word_w]

        # Re-check header widths at actual header font size
        pdf.set_font(
            header_style.font_family,
            pdf._get_font_style(header_style),
            hdr_fs,
        )
        for i, h in enumerate(headers):
            if i < n:
                words = str(h).split()
                if words:
                    hw = max(pdf.get_string_width(w) for w in words) + 2 * padding
                    col_widths[i] = max(col_widths[i], hw)

        # Enforce absolute minimum column width
        for i in range(n):
            col_widths[i] = max(col_widths[i], self._TABLE_MIN_COL_MM)

        # Cap individual columns
        max_col = available_w * self._TABLE_MAX_COL_PCT
        for i in range(n):
            col_widths[i] = min(col_widths[i], max_col)

        # Scale down if still too wide
        total = sum(col_widths)
        if total > available_w:
            scale = available_w / total
            col_widths = [w * scale for w in col_widths]

        # Add a small breathing factor (up to 12 % extra) only if room exists
        total = sum(col_widths)
        if total < available_w and total > 0:
            extra = min(available_w - total, total * 0.12)
            col_widths = [w + extra * (w / total) for w in col_widths]

        return body_fs, hdr_fs, col_widths

    # ------------------------------------------------------------------ #
    #  Table rendering (compact, word-safe)                               #
    # ------------------------------------------------------------------ #

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

        # ---- Caption ----
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
        padding = self._TABLE_COMPACT_PADDING

        n = len(headers)

        # ---- Auto-fit font size & column widths ----
        body_fs, hdr_fs, col_widths = self._auto_fit_table(
            pdf, headers, rows, style, header_style, available_w, padding,
        )

        line_h_body = body_fs * self._TABLE_LINE_HEIGHT_FACTOR
        line_h_hdr = hdr_fs * self._TABLE_LINE_HEIGHT_FACTOR
        border_color = pdf._parse_color(style.border_color)
        border_width = style.border_width
        row_bg_color = pdf._parse_color("fafafa")
        body_color = pdf._parse_color(style.color)

        pdf.ln(style.spacing_before)

        # ---- Pre-calculate header line layout (word-safe) ----
        header_lines_list: list[list[str]] = []
        for i, h in enumerate(headers):
            if i < n:
                inner_w = max(1, col_widths[i] - 2 * padding)
                lines = self._wrap_text_at_words(
                    pdf, str(h), inner_w,
                    header_style.font_family,
                    pdf._get_font_style(header_style),
                    hdr_fs,
                )
                header_lines_list.append(lines)
            else:
                header_lines_list.append([])

        header_max_lines = max((len(hl) for hl in header_lines_list), default=1)
        header_h = line_h_hdr * header_max_lines + padding * 2

        # ---- Pre-calculate body row heights (word-safe) ----
        body_lines_list: list[list[list[str]]] = []
        row_heights: list[float] = []
        for row in rows:
            row_lines: list[list[str]] = []
            max_lines = 1
            for i, cell_text in enumerate(row):
                if i < n:
                    inner_w = max(1, col_widths[i] - 2 * padding)
                    lines = self._wrap_text_at_words(
                        pdf, str(cell_text), inner_w,
                        style.font_family, "", body_fs,
                    )
                    row_lines.append(lines)
                    max_lines = max(max_lines, len(lines))
                else:
                    row_lines.append([])
            body_lines_list.append(row_lines)
            row_heights.append(line_h_body * max_lines + padding * 2)

        # ================================================================ #
        #  RENDER HEADER                                                    #
        # ================================================================ #
        x0 = pdf.l_margin
        y0 = pdf.get_y()
        if y0 + header_h > pdf.h - pdf.b_margin:
            pdf.add_page()
            y0 = pdf.get_y()

        # Header background fill
        h_bg = (
            pdf._parse_color(header_style.background_color)
            if header_style.background_color
            else None
        )
        if h_bg:
            pdf.set_fill_color(*h_bg)
            for i in range(n):
                pdf.rect(
                    x0 + sum(col_widths[:i]), y0,
                    col_widths[i], header_h,
                    style="F",
                )

        # Header text (line by line, word-safe)
        pdf.set_font(
            header_style.font_family,
            pdf._get_font_style(header_style),
            hdr_fs,
        )
        header_color = pdf._parse_color(header_style.color)
        pdf.set_text_color(*header_color)
        for i in range(n):
            if i < len(headers):
                lines = header_lines_list[i] if i < len(header_lines_list) else [str(headers[i])]
                for j, line in enumerate(lines):
                    pdf.set_xy(
                        x0 + sum(col_widths[:i]),
                        y0 + padding + j * line_h_hdr,
                    )
                    pdf.cell(col_widths[i], line_h_hdr, line, border=0, align=Align.C)

        # Header cell borders
        pdf.set_draw_color(*border_color)
        pdf.set_line_width(border_width)
        for i in range(n):
            pdf.rect(
                x0 + sum(col_widths[:i]), y0,
                col_widths[i], header_h,
            )

        pdf.set_xy(x0, y0 + header_h)

        # ================================================================ #
        #  RENDER BODY ROWS                                                 #
        # ================================================================ #
        for r, row in enumerate(rows):
            y0 = pdf.get_y()
            rh = row_heights[r]

            if y0 + rh > pdf.h - pdf.b_margin:
                pdf.add_page()
                y0 = pdf.get_y()

            # Zebra stripe background
            use_bg = r % 2 == 0
            if use_bg:
                pdf.set_fill_color(*row_bg_color)
                for i in range(n):
                    pdf.rect(
                        x0 + sum(col_widths[:i]), y0,
                        col_widths[i], rh,
                        style="F",
                    )

            # Cell text (line by line, word-safe)
            pdf.set_font(style.font_family, "", body_fs)
            pdf.set_text_color(*body_color)
            row_lines = body_lines_list[r] if r < len(body_lines_list) else []
            for i in range(n):
                if i < len(row_lines) and row_lines[i]:
                    lines = row_lines[i]
                    for j, line in enumerate(lines):
                        pdf.set_xy(
                            x0 + sum(col_widths[:i]),
                            y0 + padding + j * line_h_body,
                        )
                        pdf.cell(col_widths[i], line_h_body, line, border=0, align=Align.C)

            # Cell borders
            pdf.set_draw_color(*border_color)
            pdf.set_line_width(border_width)
            for i in range(n):
                pdf.rect(
                    x0 + sum(col_widths[:i]), y0,
                    col_widths[i], rh,
                )

            pdf.set_xy(x0, y0 + rh)

        pdf.ln(style.spacing_after)

    # ------------------------------------------------------------------ #
    #  Code block rendering                                               #
    # ------------------------------------------------------------------ #

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
