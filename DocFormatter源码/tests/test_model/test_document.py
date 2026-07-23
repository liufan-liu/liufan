"""文档模型单元测试 — 测试 Document / Paragraph / Heading / Run 等."""
import pytest
from app.model import (
    Document, Paragraph, Heading, Run, Table, Image, PageBreak,
    TOCField, DocumentList, ListItem, CodeBlock, BlockQuote,
    RunStyle, ParagraphStyle, PageStyle,
    Alignment, HeadingLevel, ListType, HeaderFooter,
)


class TestDocument:
    """Document 根节点测试."""

    @pytest.mark.p0
    def test_create_empty_document(self, empty_document):
        """M-001: 创建空文档."""
        doc = empty_document
        assert doc.title == ""
        assert doc.author == ""
        assert doc.body == []
        assert doc.page_style.width == 210.0
        assert doc.page_style.height == 297.0

    @pytest.mark.p0
    def test_add_paragraph(self, empty_document):
        """M-002: 添加段落."""
        doc = empty_document
        doc.add_paragraph("测试段落")
        assert doc.element_count() == 1
        assert isinstance(doc.body[0], Paragraph)
        assert doc.body[0].get_text() == "测试段落"
        assert len(doc.body[0].runs) == 1

    @pytest.mark.p0
    def test_add_heading(self, empty_document):
        """M-003: 添加标题."""
        doc = empty_document
        doc.add_heading("标题", level=1)
        assert doc.element_count() == 1
        assert isinstance(doc.body[0], Heading)
        assert doc.body[0].level == HeadingLevel.H1
        assert doc.body[0].get_text() == "标题"

    @pytest.mark.p0
    def test_get_headings(self, simple_document):
        """M-004: 提取标题."""
        headings = simple_document.get_headings()
        assert len(headings) == 2
        assert headings[0].level == HeadingLevel.H1
        assert headings[0].get_text() == "第一章 简介"
        assert headings[1].level == HeadingLevel.H2

    @pytest.mark.p1
    def test_word_count_chinese(self, empty_document):
        """M-005: 字数统计（纯中文）."""
        empty_document.add_paragraph("测试文档")
        assert empty_document.word_count() == 4

    @pytest.mark.p1
    def test_word_count_english(self, empty_document):
        """M-006: 字数统计（纯英文）."""
        empty_document.add_paragraph("hello world")
        assert empty_document.word_count() == 2

    @pytest.mark.p1
    def test_word_count_mixed(self, empty_document):
        """M-007: 字数统计（中英混合）."""
        empty_document.add_paragraph("测试 hello 文档")
        # 2 个中文字 + 1 个英文单词 + 2 个中文字 = 5
        assert empty_document.word_count() == 5

    @pytest.mark.p0
    def test_document_clear(self, simple_document):
        """M-010: 清空文档."""
        simple_document.header = HeaderFooter(center="test")
        simple_document.clear()
        assert simple_document.body == []
        assert simple_document.header is None

    @pytest.mark.p1
    def test_table_from_data(self):
        """M-011: 表格快速创建."""
        table = Table.from_data([
            ["A", "B"],
            ["C", "D", "E"],
        ])
        assert table.rows == 2
        assert table.cols == 3
        assert table.cells[0][0].text == "A"
        assert table.cells[1][2].text == "E"
        assert table.cells[0][2].text == ""  # 补齐

    @pytest.mark.p1
    def test_heading_style_name(self):
        """Heading 自动关联样式名."""
        h = Heading(level=HeadingLevel.H2)
        assert h.style_name == "Heading 2"

    @pytest.mark.p1
    def test_heading_level_clamped(self, empty_document):
        """标题层级应限制在 1-4."""
        empty_document.add_heading("test", level=0)
        assert empty_document.body[0].level == HeadingLevel.H1

        empty_document.add_heading("test", level=5)
        assert empty_document.body[1].level == HeadingLevel.H4


class TestStyles:
    """样式类测试."""

    @pytest.mark.p0
    def test_run_style_merge(self):
        """M-008: RunStyle 合并."""
        base = RunStyle(font_name="Arial", font_size=12, bold=True)
        override = RunStyle(font_size=14, italic=True)
        merged = base.merge_with(override)

        assert merged.font_name == "Arial"      # base 保留
        assert merged.font_size == 14            # override 覆盖
        assert merged.bold is True               # base 保留
        assert merged.italic is True             # override 新增

    @pytest.mark.p0
    def test_run_style_merge_none(self):
        """与 None 合并应返回自身."""
        style = RunStyle(font_name="Arial")
        merged = style.merge_with(None)
        assert merged is style

    @pytest.mark.p1
    def test_run_style_is_empty(self):
        """判断样式是否全部未设置."""
        empty = RunStyle()
        assert empty.is_empty() is True

        not_empty = RunStyle(font_name="Arial")
        assert not_empty.is_empty() is False

    @pytest.mark.p0
    def test_paragraph_style_merge(self):
        """ParagraphStyle 合并."""
        base = ParagraphStyle(alignment=Alignment.LEFT, line_spacing=1.5)
        override = ParagraphStyle(alignment=Alignment.CENTER)
        merged = base.merge_with(override)

        assert merged.alignment == Alignment.CENTER   # override 覆盖
        assert merged.line_spacing == 1.5              # base 保留

    @pytest.mark.p1
    def test_page_style_defaults(self):
        """PageStyle 默认值应为 A4."""
        ps = PageStyle()
        assert ps.width == 210.0
        assert ps.height == 297.0
        assert ps.orientation == "portrait"


class TestElements:
    """元素类测试."""

    @pytest.mark.p0
    def test_paragraph_get_text(self):
        """M-009: 段落纯文本拼接."""
        p = Paragraph(runs=[
            Run(text="Hello "),
            Run(text="World"),
        ])
        assert p.get_text() == "Hello World"

    @pytest.mark.p1
    def test_paragraph_clone(self):
        """段落深拷贝."""
        p = Paragraph(runs=[Run(text="test")])
        cloned = p.clone()
        assert cloned.get_text() == p.get_text()
        cloned.runs[0].text = "changed"
        assert p.runs[0].text == "test"   # 原始未变

    @pytest.mark.p1
    def test_table_from_data_padding(self):
        """Table.from_data 列数补齐."""
        table = Table.from_data([["a"], ["b", "c"]])
        assert table.cols == 2
        assert table.cells[0][1].text == ""
