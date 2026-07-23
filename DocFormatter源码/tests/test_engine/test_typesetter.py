"""排版引擎单元测试."""
import pytest
from copy import deepcopy
from app.engine.typesetter import Typesetter
from app.engine.toc_generator import TOCGenerator
from app.model.elements import (
    Paragraph, Heading, Table, TOCField, CodeBlock, DocumentList,
    Run,
)
from app.model.styles import RunStyle, ParagraphStyle
from app.model.enums import Alignment, HeadingLevel


class TestTypesetter:
    """排版引擎测试."""

    @pytest.mark.p0
    def test_apply_page_settings(self, simple_document, minimal_template):
        """E-001: 应用页面设置."""
        doc = Typesetter(minimal_template).apply(simple_document)
        assert doc.page_style.margin_top == 20
        assert doc.page_style.margin_left == 25

    @pytest.mark.p0
    def test_apply_heading_style(self, simple_document, minimal_template):
        """E-002: 应用标题样式."""
        doc = Typesetter(minimal_template).apply(simple_document)
        headings = doc.get_headings()
        h1 = headings[0]
        assert h1.runs[0].style.font_name == "Arial"
        assert h1.runs[0].style.font_size == 20
        assert h1.runs[0].style.bold is True
        assert h1.style.alignment == Alignment.CENTER

    @pytest.mark.p0
    def test_apply_paragraph_style(self, simple_document, minimal_template):
        """E-003: 应用段落样式."""
        doc = Typesetter(minimal_template).apply(simple_document)
        paras = [e for e in doc.body if isinstance(e, Paragraph) and not isinstance(e, Heading)]
        assert len(paras) >= 1
        assert paras[0].runs[0].style.font_name == "Times New Roman"
        assert paras[0].runs[0].style.font_size == 11
        assert paras[0].style.alignment == Alignment.LEFT
        assert paras[0].style.line_spacing == 1.25

    @pytest.mark.p0
    def test_first_line_indent_chars(self, simple_document, default_template):
        """E-004: 首行缩进字符数应用."""
        doc = Typesetter(default_template).apply(simple_document)
        paras = [e for e in doc.body
                 if isinstance(e, Paragraph) and not isinstance(e, Heading)]
        assert len(paras) >= 1
        assert paras[0].style.first_line_indent_chars == 2

    @pytest.mark.p0
    def test_no_overwrite_existing_style(self):
        """E-005: 模板不覆盖已有样式."""
        from app.model import Document
        doc = Document()
        # 段落已有 bold=True
        para = Paragraph(runs=[Run(text="test", style=RunStyle(bold=True))])
        doc.body.append(para)

        # 模板 bold 为 None
        template = {
            "name": "test",
            "styles": {
                "Normal": {
                    "run": {"font_size": 14},  # bold 未设置
                }
            },
        }

        typeset_doc = Typesetter(template).apply(doc)
        result_para = typeset_doc.body[0]
        # 原有 bold=True 应保留
        assert result_para.runs[0].style.bold is True
        # 模板的 font_size 应被应用
        assert result_para.runs[0].style.font_size == 14

    @pytest.mark.p0
    def test_toc_field_inserted(self, simple_document):
        """E-006: 启用 TOC 时插入目录域."""
        template = {
            "name": "test",
            "toc": {"enabled": True, "max_level": 3, "title": "目录"},
            "styles": {},
        }
        doc = Typesetter(template).apply(simple_document)
        assert isinstance(doc.body[0], TOCField)
        assert doc.body[0].title == "目录"
        assert doc.body[0].max_level == 3

    @pytest.mark.p1
    def test_header_footer(self, simple_document, default_template):
        """E-007: 页眉页脚应用."""
        doc = Typesetter(default_template).apply(simple_document)
        assert doc.footer is not None
        assert doc.footer.include_page_number is True

    @pytest.mark.p0
    def test_original_document_unchanged(self, simple_document, default_template):
        """E-008: 原始文档不被修改."""
        original_paragraph_count = len([
            e for e in simple_document.body if isinstance(e, Paragraph)
        ])
        Typesetter(default_template).apply(simple_document)
        new_paragraph_count = len([
            e for e in simple_document.body if isinstance(e, Paragraph)
        ])
        assert original_paragraph_count == new_paragraph_count

    @pytest.mark.p1
    def test_table_style_applied(self, complex_document, default_template):
        """E-009: 表格样式应用."""
        doc = Typesetter(default_template).apply(complex_document)
        tables = [e for e in doc.body if isinstance(e, Table)]
        assert len(tables) >= 1
        # 单元格字体应为模板指定的宋体
        cell = tables[0].cells[0][0]
        if cell.runs:
            assert cell.runs[0].style.font_name == "宋体"

    @pytest.mark.p1
    def test_code_block_converted(self, complex_document, default_template):
        """E-011: 代码块转为段落."""
        doc = Typesetter(default_template).apply(complex_document)
        # CodeBlock 应被转换为 Paragraph
        code_blocks = [e for e in doc.body if isinstance(e, CodeBlock)]
        assert len(code_blocks) == 0  # 已转换


class TestTOCGenerator:
    """目录生成器测试."""

    @pytest.mark.p0
    def test_generate_toc(self, simple_document):
        """E-012: 从文档生成目录."""
        gen = TOCGenerator(max_level=3)
        entries = gen.generate(simple_document)
        assert len(entries) == 2
        assert entries[0]["level"] == 1
        assert entries[0]["text"] == "第一章 简介"
        assert entries[1]["level"] == 2

    @pytest.mark.p1
    def test_generate_toc_respects_max_level(self, simple_document):
        """TOC 最大层级限制."""
        gen = TOCGenerator(max_level=1)
        entries = gen.generate(simple_document)
        assert len(entries) == 1  # 只有 H1
        assert entries[0]["level"] == 1

    @pytest.mark.p1
    def test_toc_to_text(self, simple_document):
        """TOC 文本输出."""
        gen = TOCGenerator(max_level=3, title="目录")
        text = gen.to_text(simple_document)
        assert "目录" in text
        assert "第一章 简介" in text
        assert "1.1 背景" in text

    @pytest.mark.p0
    def test_empty_document_toc(self, empty_document):
        """空文档生成空目录."""
        gen = TOCGenerator()
        entries = gen.generate(empty_document)
        assert entries == []
