"""健壮性与异常测试 — 验证极端场景下的容错能力."""
import pytest
import os
import stat
from pathlib import Path

from app.importers.md_importer import MarkdownImporter
from app.importers.txt_importer import TxtImporter
from app.importers.docx_importer import DocxImporter
from app.importers.base import ImportError, ImporterRegistry
from app.templates import TemplateManager, TemplateError
from app.engine import Typesetter
from app.exporter import DocxExporter, ExportError
from app.model import Document


class TestMalformedInput:
    """畸形输入测试."""

    @pytest.mark.p1
    def test_binary_as_txt(self, temp_dir):
        """二进制文件冒充 .txt."""
        f = temp_dir / "binary.txt"
        f.write_bytes(bytes(range(256)))
        # 应该能处理（latin-1 兜底）或抛出友好错误
        try:
            doc = TxtImporter().import_file(f)
            # 不应崩溃
            assert doc is not None
        except ImportError:
            pass  # 也接受

    @pytest.mark.p1
    def test_binary_as_md(self, temp_dir):
        """二进制文件冒充 .md."""
        f = temp_dir / "binary.md"
        f.write_bytes(bytes(range(256)))
        try:
            doc = MarkdownImporter().import_file(f)
            assert doc is not None
        except (ImportError, UnicodeDecodeError):
            pass

    @pytest.mark.p1
    def test_invalid_docx(self, temp_dir):
        """损坏的 docx 文件."""
        f = temp_dir / "corrupt.docx"
        f.write_bytes(b"PK\x03\x04" + b"\x00" * 100)  # 假 ZIP 头
        with pytest.raises(ImportError):
            DocxImporter().import_file(f)

    @pytest.mark.p1
    def test_html_inside_md(self, temp_dir):
        """Markdown 中嵌入非法 HTML."""
        f = temp_dir / "mixed.md"
        f.write_text("# 标题\n\n<script>alert('xss')</script>\n\n正文", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        # 不应崩溃
        assert doc.element_count() >= 1

    @pytest.mark.p1
    def test_extremely_long_line(self, temp_dir):
        """超长单行（100,000 字符）."""
        f = temp_dir / "long_line.txt"
        long_text = "A" * 100000
        f.write_text(long_text, encoding="utf-8")
        doc = TxtImporter().import_file(f)
        assert doc.element_count() == 1
        assert len(doc.body[0].get_text()) == 100000

    @pytest.mark.p1
    def test_nested_emphasis(self, temp_dir):
        """极端嵌套的强调语法."""
        f = temp_dir / "nested.md"
        f.write_text("***~~**~~***text", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        assert doc.element_count() >= 1

    @pytest.mark.p1
    def test_malformed_table(self, temp_dir):
        """列数不一致的表格."""
        f = temp_dir / "bad_table.md"
        f.write_text("""| A | B |
|---|---|
| 1 | 2 | 3 |
| 4 |""", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        # 应能解析，不崩溃
        assert doc.element_count() >= 1

    @pytest.mark.p2
    def test_null_bytes(self, temp_dir):
        """含 NULL 字符的文本."""
        f = temp_dir / "null.txt"
        f.write_bytes(b"Hello\x00World\x00\n\nTest")
        try:
            doc = TxtImporter().import_file(f)
            assert doc is not None
        except ImportError:
            pass

    @pytest.mark.p2
    def test_mixed_line_endings(self, temp_dir):
        """混合换行符（CRLF + LF + CR）."""
        f = temp_dir / "mixed_endings.txt"
        f.write_bytes(b"Line1\r\nLine2\nLine3\rLine4\n\nNewPara")
        doc = TxtImporter().import_file(f)
        assert doc.element_count() >= 2


class TestPermissionAndPath:
    """权限与路径测试."""

    @pytest.mark.p1
    def test_read_only_directory(self, temp_dir):
        """导出到只读目录."""
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

        doc = Document()
        doc.add_paragraph("test")
        output = readonly_dir / "output.docx"

        try:
            with pytest.raises((ExportError, PermissionError, OSError)):
                DocxExporter().export(doc, output)
        finally:
            # 恢复权限以便清理
            readonly_dir.chmod(stat.S_IRWXU)

    @pytest.mark.p1
    def test_unicode_path(self, temp_dir):
        """Unicode 路径（含中文、日文、emoji）."""
        weird_dir = temp_dir / "测试_テスト_🎉"
        weird_dir.mkdir()
        output = weird_dir / "文档_ドキュメント.docx"

        doc = Document()
        doc.add_paragraph("测试内容")
        DocxExporter().export(doc, output)
        assert output.exists()

    @pytest.mark.p1
    def test_deeply_nested_path(self, temp_dir):
        """深层嵌套路径（50 层目录）."""
        deep = temp_dir
        for i in range(50):
            deep = deep / f"d{i}"
        deep.mkdir(parents=True)

        output = deep / "output.docx"
        doc = Document()
        doc.add_paragraph("test")
        DocxExporter().export(doc, output)
        assert output.exists()


class TestTemplateEdgeCases:
    """模板边界情况测试."""

    @pytest.mark.p1
    def test_template_with_extra_unknown_fields(self, temp_dir):
        """模板含未知字段应被忽略."""
        user_dir = temp_dir / "user"
        tm = TemplateManager(user_dir=user_dir)
        yaml_content = """name: "扩展模板"
unknown_field: "value"
page:
  width: 210
  height: 297
  unknown_page_field: 42
styles:
  Normal:
    run:
      font_name: "Arial"
    unknown_style_type:
      something: "else"
"""
        name = tm.add_user_template(yaml_content)
        tpl = tm.get_template(name)
        assert tpl is not None
        assert tpl["name"] == "扩展模板"

    @pytest.mark.p1
    def test_template_with_null_styles(self, temp_dir):
        """模板样式值为 null."""
        user_dir = temp_dir / "user"
        tm = TemplateManager(user_dir=user_dir)
        yaml_content = """name: "Null样式"
styles:
  Normal:
    run:
      font_name: null
      font_size: null
    paragraph:
      alignment: null
"""
        name = tm.add_user_template(yaml_content)
        tpl = tm.get_template(name)
        doc = Document()
        doc.add_paragraph("test")
        # 不应崩溃
        Typesetter(tpl).apply(doc)

    @pytest.mark.p1
    def test_apply_template_to_empty_doc(self):
        """对空文档应用模板."""
        doc = Document()
        tpl = TemplateManager().get_template("通用文档")
        result = Typesetter(tpl).apply(doc)
        assert result.element_count() == 0

    @pytest.mark.p1
    def test_export_empty_document(self, temp_dir):
        """导出完全空的文档."""
        doc = Document()
        output = temp_dir / "empty.docx"
        DocxExporter().export(doc, output)
        assert output.exists()


class TestSpecialCharacters:
    """特殊字符测试."""

    @pytest.mark.p1
    def test_emoji_in_content(self, temp_dir):
        """内容含 emoji."""
        f = temp_dir / "emoji.md"
        f.write_text("# 🎉 开始\n\n😊👍🚀\n\n结束 ✅", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        tpl = TemplateManager().get_template("通用文档")
        doc = Typesetter(tpl).apply(doc)
        output = temp_dir / "emoji.docx"
        DocxExporter().export(doc, output)
        assert output.exists()

    @pytest.mark.p1
    def test_math_symbols(self, temp_dir):
        """数学符号."""
        f = temp_dir / "math.md"
        f.write_text("公式: ∑∫∞≤≥≠≈±×÷√∂∇", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        output = temp_dir / "math.docx"
        DocxExporter().export(doc, output)
        assert output.exists()

    @pytest.mark.p1
    def test_rtl_content(self, temp_dir):
        """右到左文字（阿拉伯语、希伯来语）."""
        f = temp_dir / "rtl.md"
        f.write_text("# عربي\n\nمرحبا بالعالم\n\nעברית", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        assert doc.element_count() >= 1

    @pytest.mark.p1
    def test_zero_width_chars(self, temp_dir):
        """零宽字符."""
        f = temp_dir / "zero.md"
        # 零宽空格、零宽连接符等
        f.write_text("abc​def‌ghi‍jkl", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        assert doc.element_count() >= 1

    @pytest.mark.p1
    def test_private_use_unicode(self, temp_dir):
        """私有区 Unicode 字符."""
        f = temp_dir / "pua.md"
        # 私有区字符 U+E000 - U+F8FF
        f.write_text("Test: ", encoding="utf-8")
        doc = MarkdownImporter().import_file(f)
        assert doc.element_count() >= 1


class TestConcurrencySafety:
    """并发安全测试（同一进程内顺序调用）."""

    @pytest.mark.p1
    def test_multiple_importers_share_state(self, temp_dir):
        """多个导入器并行使用不相互干扰."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("TXT 内容", encoding="utf-8")

        md_file = temp_dir / "test.md"
        md_file.write_text("# MD 内容", encoding="utf-8")

        # 顺序调用不同导入器
        doc1 = TxtImporter().import_file(txt_file)
        doc2 = MarkdownImporter().import_file(md_file)
        doc3 = TxtImporter().import_file(txt_file)

        # 每个文档应独立
        assert doc1.body[0].get_text() == "TXT 内容"
        assert doc2.body[0].get_text() == "MD 内容"
        assert doc3.body[0].get_text() == "TXT 内容"

    @pytest.mark.p1
    def test_template_manager_reuse(self, temp_dir):
        """重复使用 TemplateManager 不产生副作用."""
        tm = TemplateManager()
        tpl1 = tm.get_template("通用文档")
        tpl2 = tm.get_template("通用文档")
        # 应该返回相同内容
        assert tpl1["name"] == tpl2["name"]
        assert tpl1["styles"] == tpl2["styles"]
