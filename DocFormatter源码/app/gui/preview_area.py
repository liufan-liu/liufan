"""文档预览区 — 用 QTextEdit 模拟 A4 页面渲染."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout
from PySide6.QtGui import (
    QFont, QTextCharFormat, QTextBlockFormat, QTextCursor,
    QColor, QPalette,
)
from PySide6.QtCore import Qt

from app.model.document import Document
from app.model.elements import (
    Paragraph, Heading, Table, Image, PageBreak,
    TOCField, Run, DocumentList, CodeBlock, BlockQuote,
)
from app.model.styles import RunStyle, ParagraphStyle
from app.model.enums import Alignment, HeadingLevel


class PreviewArea(QWidget):
    """文档预览区."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部信息栏
        self.top_bar = QLabel("  文档预览（近似效果，最终以 Word 打开为准）")
        self.top_bar.setFixedHeight(24)
        self.top_bar.setStyleSheet(
            "background-color: #e8e8e8; color: #555; font-size: 11px; "
            "border-bottom: 1px solid #ccc;"
        )
        layout.addWidget(self.top_bar)

        # 主预览区
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ccc;
                margin: 10px;
                padding: 30px 40px;
                font-size: 12pt;
                font-family: "宋体", "Songti SC", "SimSun", serif;
            }
        """)
        layout.addWidget(self.text_edit, stretch=1)

        # 底部提示栏
        self.bottom_bar = QLabel("  预览为近似效果，最终排版以 Word 打开为准")
        self.bottom_bar.setFixedHeight(22)
        self.bottom_bar.setStyleSheet(
            "background-color: #f5f5dc; color: #666; font-size: 11px; "
            "border-top: 1px solid #ccc;"
        )
        layout.addWidget(self.bottom_bar)

        self.document = None

    def set_document(self, doc: Document) -> None:
        """设置要预览的文档."""
        self.document = doc
        self._render()

    def _render(self) -> None:
        """渲染文档到 QTextEdit."""
        if not self.document:
            self.text_edit.clear()
            return

        self.text_edit.clear()
        cursor = self.text_edit.textCursor()

        for element in self.document.body:
            try:
                if isinstance(element, Heading):
                    self._render_heading(cursor, element)
                elif isinstance(element, Paragraph):
                    self._render_paragraph(cursor, element)
                elif isinstance(element, Table):
                    self._render_table(cursor, element)
                elif isinstance(element, Image):
                    self._render_image_placeholder(cursor, element)
                elif isinstance(element, PageBreak):
                    self._render_page_break(cursor)
                elif isinstance(element, TOCField):
                    self._render_toc(cursor, element)
                elif isinstance(element, DocumentList):
                    self._render_list(cursor, element)
                elif isinstance(element, CodeBlock):
                    self._render_code_block(cursor, element)
                elif isinstance(element, BlockQuote):
                    self._render_blockquote(cursor, element)
            except Exception as e:
                cursor.insertText(f"[渲染错误: {type(element).__name__}: {e}]\n")

        # 回到顶部
        cursor.movePosition(QTextCursor.Start)
        self.text_edit.setTextCursor(cursor)

    def _render_heading(self, cursor, heading: Heading) -> None:
        """渲染标题."""
        block_fmt = QTextBlockFormat()
        space_before_map = {1: 24, 2: 18, 3: 13, 4: 12}
        space_before = space_before_map.get(heading.level.value, 12)
        block_fmt.setTopMargin(space_before)

        if heading.style.alignment == Alignment.CENTER:
            block_fmt.setAlignment(Qt.AlignCenter)
        elif heading.style.alignment == Alignment.RIGHT:
            block_fmt.setAlignment(Qt.AlignRight)
        else:
            block_fmt.setAlignment(Qt.AlignLeft)

        cursor.insertBlock(block_fmt)

        size_map = {1: 22, 2: 15, 3: 13, 4: 12}
        base_size = size_map.get(heading.level.value, 12)

        for run in heading.runs:
            fmt = QTextCharFormat()
            font_size = run.style.font_size or base_size
            fmt.setFontPointSize(font_size)
            fmt.setFontWeight(700 if (run.style.bold is not False) else 400)

            font_family = run.style.font_name_east_asia or run.style.font_name or "黑体"
            fmt.setFontFamily(font_family)

            if run.style.italic:
                fmt.setFontItalic(True)
            if run.style.color:
                try:
                    fmt.setForeground(QColor(run.style.color))
                except Exception:
                    pass

            cursor.insertText(run.text, fmt)

        cursor.insertText("\n")

    def _render_paragraph(self, cursor, para: Paragraph) -> None:
        """渲染段落."""
        block_fmt = QTextBlockFormat()

        align_map = {
            Alignment.LEFT: Qt.AlignLeft,
            Alignment.CENTER: Qt.AlignCenter,
            Alignment.RIGHT: Qt.AlignRight,
            Alignment.JUSTIFY: Qt.AlignJustify,
        }
        if para.style.alignment:
            block_fmt.setAlignment(align_map.get(para.style.alignment, Qt.AlignLeft))

        # 行距：使用固定像素值
        if para.style.line_spacing:
            font_size = 12
            for r in para.runs:
                if r.style.font_size:
                    font_size = r.style.font_size
                    break
            line_height_px = max(int(font_size * para.style.line_spacing * 1.33), 18)
            block_fmt.setLineHeight(line_height_px, 0)  # 0 = FixedHeight

        if para.style.space_before:
            block_fmt.setTopMargin(para.style.space_before)
        if para.style.space_after:
            block_fmt.setBottomMargin(para.style.space_after)

        if para.style.first_line_indent:
            block_fmt.setTextIndent(para.style.first_line_indent)
        elif para.style.first_line_indent_chars:
            font_size = 12
            for r in para.runs:
                if r.style.font_size:
                    font_size = r.style.font_size
                    break
            block_fmt.setTextIndent(para.style.first_line_indent_chars * font_size)

        if para.style.left_indent:
            block_fmt.setLeftIndent(para.style.left_indent)
        if para.style.right_indent:
            block_fmt.setRightIndent(para.style.right_indent)

        cursor.insertBlock(block_fmt)

        for run in para.runs:
            fmt = self._run_to_format(run)
            cursor.insertText(run.text, fmt)

        cursor.insertText("\n")

    def _render_table(self, cursor, table: Table) -> None:
        """渲染表格（文本形式）."""
        if not table.cells:
            return

        cursor.insertBlock(QTextBlockFormat())

        if table.caption:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(10.5)
            fmt.setFontWeight(700)
            cap_fmt = QTextBlockFormat()
            cap_fmt.setAlignment(Qt.AlignCenter)
            cursor.insertBlock(cap_fmt)
            cursor.insertText(table.caption, fmt)
            cursor.insertBlock(QTextBlockFormat())

        col_widths = []
        for j in range(table.cols):
            max_w = 0
            for row in table.cells:
                if j < len(row):
                    w = len(row[j].text)
                    max_w = max(max_w, w)
            col_widths.append(min(max_w + 2, 30))

        separator = "+" + "+".join("-" * (w + 1) for w in col_widths) + "\n"

        cursor.insertText(separator)
        if table.cells:
            header_row = table.cells[0]
            line = "|"
            for j, w in enumerate(col_widths):
                cell_text = header_row[j].text if j < len(header_row) else ""
                line += " " + cell_text.ljust(w) + "|"
            cursor.insertText(line + "\n")
            cursor.insertText(separator)

            for i, row in enumerate(table.cells[1:], start=1):
                line = "|"
                for j, w in enumerate(col_widths):
                    cell_text = row[j].text if j < len(row) else ""
                    line += " " + cell_text.ljust(w) + "|"
                cursor.insertText(line + "\n")
            cursor.insertText(separator)

        cursor.insertText("\n")

    def _render_image_placeholder(self, cursor, img: Image) -> None:
        """渲染图片占位符."""
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(Qt.AlignCenter)
        cursor.insertBlock(block_fmt)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(100, 100, 200))
        fmt.setFontPointSize(10)

        size_info = ""
        if img.width or img.height:
            size_info = f" ({img.width or '?'}×{img.height or '?'} cm)"

        caption_text = f" — {img.caption}" if img.caption else ""
        cursor.insertText(f"[图片: {img.path}{size_info}{caption_text}]\n", fmt)

    def _render_page_break(self, cursor) -> None:
        """渲染分页符."""
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(Qt.AlignCenter)
        cursor.insertBlock(block_fmt)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(180, 180, 180))
        cursor.insertText("— — — 分页符 — — —\n", fmt)

    def _render_toc(self, cursor, toc: TOCField) -> None:
        """渲染目录."""
        title_fmt = QTextBlockFormat()
        title_fmt.setAlignment(Qt.AlignCenter)
        title_fmt.setBottomMargin(12)
        cursor.insertBlock(title_fmt)
        title_char = QTextCharFormat()
        title_char.setFontPointSize(16)
        title_char.setFontWeight(700)
        cursor.insertText(toc.title, title_char)

        if self.document:
            headings = self.document.get_headings()
            for h in headings:
                if h.level.value <= toc.max_level:
                    indent = (h.level.value - 1) * 20
                    fmt = QTextBlockFormat()
                    fmt.setLeftIndent(indent)
                    cursor.insertBlock(fmt)

                    char_fmt = QTextCharFormat()
                    char_fmt.setFontPointSize(12)
                    cursor.insertText(h.get_text(), char_fmt)

        cursor.insertBlock(QTextBlockFormat())
        hint_fmt = QTextCharFormat()
        hint_fmt.setForeground(QColor(150, 150, 150))
        hint_fmt.setFontPointSize(9)
        cursor.insertText("（目录内容在 Word 中打开后按 F9 更新）\n", hint_fmt)
        cursor.insertText("\n")

    def _render_list(self, cursor, lst: DocumentList) -> None:
        """渲染列表."""
        for idx, item in enumerate(lst.items, 1):
            block_fmt = QTextBlockFormat()
            indent = 20 + item.level * 15
            block_fmt.setLeftIndent(indent)

            if lst.list_type.value == "unordered":
                prefix = "•  "
            else:
                prefix = f"{idx}. "

            cursor.insertBlock(block_fmt)

            prefix_fmt = QTextCharFormat()
            prefix_fmt.setFontPointSize(12)
            cursor.insertText(prefix, prefix_fmt)

            for run in item.runs:
                fmt = self._run_to_format(run)
                cursor.insertText(run.text, fmt)

            cursor.insertText("\n")

    def _render_code_block(self, cursor, code: CodeBlock) -> None:
        """渲染代码块."""
        block_fmt = QTextBlockFormat()
        block_fmt.setLeftIndent(20)
        block_fmt.setLineHeight(14, 0)
        cursor.insertBlock(block_fmt)

        fmt = QTextCharFormat()
        fmt.setFontFamily("Courier New")
        fmt.setFontPointSize(10)
        fmt.setBackground(QColor(240, 240, 240))

        for line in code.code.split("\n"):
            cursor.insertText(line + "\n", fmt)
        cursor.insertText("\n")

    def _render_blockquote(self, cursor, quote: BlockQuote) -> None:
        """渲染引用块."""
        block_fmt = QTextBlockFormat()
        block_fmt.setLeftIndent(30)
        block_fmt.setRightIndent(30)
        cursor.insertBlock(block_fmt)

        marker_fmt = QTextCharFormat()
        marker_fmt.setForeground(QColor(150, 150, 150))
        cursor.insertText("❝ ", marker_fmt)

        for run in quote.runs:
            fmt = self._run_to_format(run)
            fmt.setForeground(QColor(80, 80, 80))
            fmt.setFontItalic(True)
            cursor.insertText(run.text, fmt)

        cursor.insertText("\n\n")

    def _run_to_format(self, run: Run) -> QTextCharFormat:
        """将 Run 转换为 QTextCharFormat."""
        fmt = QTextCharFormat()
        style = run.style

        if style.font_size:
            fmt.setFontPointSize(style.font_size)
        else:
            fmt.setFontPointSize(12)

        font_family = style.font_name_east_asia or style.font_name
        if font_family:
            fmt.setFontFamily(font_family)

        if style.bold:
            fmt.setFontWeight(700)
        if style.italic:
            fmt.setFontItalic(True)
        if style.underline:
            fmt.setFontUnderline(True)
        if style.strike:
            fmt.setFontStrikeOut(True)
        if style.color:
            try:
                fmt.setForeground(QColor(style.color))
            except Exception:
                pass

        return fmt
