"""Markdown 导入器单元测试."""
import pytest
from pathlib import Path
from app.importers.md_importer import MarkdownImporter
from app.model.elements import (
    Heading, Paragraph, Table, Image, PageBreak,
    CodeBlock, BlockQuote, DocumentList,
)
from app.model.enums import HeadingLevel, ListType


class TestMarkdownImporter:
    """Markdown 导入器测试."""

    @pytest.mark.p0
    def test_can_import_md(self, md_importer):
        """识别 .md 和 .markdown 扩展名."""
        assert md_importer.can_import(Path("test.md")) is True
        assert md_importer.can_import(Path("test.markdown")) is True
        assert md_importer.can_import(Path("test.txt")) is False

    @pytest.mark.p0
    def test_import_headings(self, temp_md_file, md_importer):
        """MD-001: 各级标题正确识别."""
        f = temp_md_file("# H1\n## H2\n### H3\n#### H4")
        doc = md_importer.import_file(f)
        headings = [e for e in doc.body if isinstance(e, Heading)]
        assert len(headings) == 4
        assert headings[0].level == HeadingLevel.H1
        assert headings[1].level == HeadingLevel.H2
        assert headings[2].level == HeadingLevel.H3
        assert headings[3].level == HeadingLevel.H4

    @pytest.mark.p0
    def test_import_paragraph(self, temp_md_file, md_importer):
        """MD-002: 普通段落."""
        f = temp_md_file("这是普通段落。")
        doc = md_importer.import_file(f)
        assert len(doc.body) >= 1
        assert isinstance(doc.body[0], Paragraph)
        assert "普通段落" in doc.body[0].get_text()

    @pytest.mark.p0
    def test_import_bold(self, temp_md_file, md_importer):
        """MD-003: 粗体识别."""
        f = temp_md_file("这是 **加粗文本** 内容")
        doc = md_importer.import_file(f)
        para = doc.body[0]
        bold_runs = [r for r in para.runs if r.style.bold]
        assert len(bold_runs) >= 1
        assert "加粗文本" in bold_runs[0].text

    @pytest.mark.p0
    def test_import_italic(self, temp_md_file, md_importer):
        """MD-004: 斜体识别."""
        f = temp_md_file("这是 *斜体文本* 内容")
        doc = md_importer.import_file(f)
        para = doc.body[0]
        italic_runs = [r for r in para.runs if r.style.italic]
        assert len(italic_runs) >= 1
        assert "斜体文本" in italic_runs[0].text

    @pytest.mark.p1
    def test_import_inline_code(self, temp_md_file, md_importer):
        """MD-005: 行内代码."""
        f = temp_md_file("使用 `print()` 函数")
        doc = md_importer.import_file(f)
        para = doc.body[0]
        code_runs = [r for r in para.runs if r.style.font_name == "Courier New"]
        assert len(code_runs) >= 1
        assert "print()" in code_runs[0].text

    @pytest.mark.p0
    def test_import_unordered_list(self, temp_md_file, md_importer):
        """MD-006: 无序列表."""
        f = temp_md_file("- 第一项\n- 第二项\n- 第三项")
        doc = md_importer.import_file(f)
        lists = [e for e in doc.body if isinstance(e, DocumentList)]
        assert len(lists) >= 1
        assert lists[0].list_type == ListType.UNORDERED
        assert len(lists[0].items) == 3

    @pytest.mark.p0
    def test_import_ordered_list(self, temp_md_file, md_importer):
        """MD-007: 有序列表."""
        f = temp_md_file("1. 第一项\n2. 第二项")
        doc = md_importer.import_file(f)
        lists = [e for e in doc.body if isinstance(e, DocumentList)]
        assert len(lists) >= 1
        assert lists[0].list_type == ListType.ORDERED

    @pytest.mark.p0
    def test_import_table(self, temp_md_file, md_importer):
        """MD-008: 表格解析."""
        md = """| 列1 | 列2 | 列3 |
|------|------|------|
| A | B | C |
| D | E | F |"""
        f = temp_md_file(md)
        doc = md_importer.import_file(f)
        tables = [e for e in doc.body if isinstance(e, Table)]
        assert len(tables) == 1
        assert tables[0].rows == 3   # header + 2 data rows
        assert tables[0].cols == 3

    @pytest.mark.p0
    def test_import_code_block(self, temp_md_file, md_importer):
        """MD-009: 代码块."""
        md = "```python\nprint('hello')\nx = 42\n```"
        f = temp_md_file(md)
        doc = md_importer.import_file(f)
        codes = [e for e in doc.body if isinstance(e, CodeBlock)]
        assert len(codes) == 1
        assert codes[0].language == "python"
        assert "print('hello')" in codes[0].code

    @pytest.mark.p1
    def test_import_blockquote(self, temp_md_file, md_importer):
        """MD-010: 引用块."""
        f = temp_md_file("> 这是引用\n> 多行引用")
        doc = md_importer.import_file(f)
        quotes = [e for e in doc.body if isinstance(e, BlockQuote)]
        assert len(quotes) >= 1
        assert "引用" in quotes[0].runs[0].text

    @pytest.mark.p1
    def test_import_horizontal_rule(self, temp_md_file, md_importer):
        """MD-012: 分隔线 → 分页符."""
        f = temp_md_file("上方内容\n\n---\n\n下方内容")
        doc = md_importer.import_file(f)
        page_breaks = [e for e in doc.body if isinstance(e, PageBreak)]
        assert len(page_breaks) >= 1

    @pytest.mark.p0
    def test_import_complex_markdown(self, temp_md_file, md_importer):
        """MD-014: 复杂 Markdown（所有语法混合）."""
        md = """# 标题

这是**加粗**和*斜体*段落。

## 列表

- 项目一
- 项目二

## 表格

| A | B |
|---|---|
| 1 | 2 |

> 引用

```python
code
```

---

结束"""
        f = temp_md_file(md)
        doc = md_importer.import_file(f)

        # 验证各元素都存在
        assert any(isinstance(e, Heading) for e in doc.body)
        assert any(isinstance(e, Paragraph) for e in doc.body)
        assert any(isinstance(e, DocumentList) for e in doc.body)
        assert any(isinstance(e, Table) for e in doc.body)
        assert any(isinstance(e, BlockQuote) for e in doc.body)
        assert any(isinstance(e, CodeBlock) for e in doc.body)
        assert any(isinstance(e, PageBreak) for e in doc.body)

    @pytest.mark.p1
    def test_import_preserves_heading_order(self, temp_md_file, md_importer):
        """标题后跟列表，再跟标题 — 不能丢失第二个标题."""
        md = """## 第一部分

- 项目

## 第二部分

内容"""
        f = temp_md_file(md)
        doc = md_importer.import_file(f)
        headings = [e for e in doc.body if isinstance(e, Heading)]
        assert len(headings) == 2
        assert headings[0].get_text() == "第一部分"
        assert headings[1].get_text() == "第二部分"
