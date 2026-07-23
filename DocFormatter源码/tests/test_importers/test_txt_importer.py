"""TXT 导入器单元测试."""
import pytest
from pathlib import Path
from app.importers.txt_importer import TxtImporter
from app.importers.base import ImportError
from app.model.elements import Paragraph, Heading


class TestTxtImporter:
    """TXT 导入器测试."""

    @pytest.mark.p0
    def test_can_import_txt(self, txt_importer):
        """识别 .txt 扩展名."""
        assert txt_importer.can_import(Path("test.txt")) is True
        assert txt_importer.can_import(Path("test.TXT")) is True
        assert txt_importer.can_import(Path("test.md")) is False

    @pytest.mark.p0
    def test_import_simple_text(self, temp_txt_file, txt_importer):
        """T-001: 普通文本按空行分段."""
        f = temp_txt_file("第一段\n\n第二段\n\n第三段")
        doc = txt_importer.import_file(f)
        assert doc.element_count() == 3
        assert all(isinstance(e, Paragraph) for e in doc.body)
        assert doc.body[0].get_text() == "第一段"
        assert doc.body[1].get_text() == "第二段"
        assert doc.body[2].get_text() == "第三段"

    @pytest.mark.p0
    def test_import_chinese_chapter_heading(self, temp_txt_file, txt_importer):
        """T-002: '第X章' 识别为 H1."""
        f = temp_txt_file("第一章 简介\n\n正文内容")
        doc = txt_importer.import_file(f)
        assert isinstance(doc.body[0], Heading)
        assert doc.body[0].level.value == 1

    @pytest.mark.p0
    def test_import_numeric_heading(self, temp_txt_file, txt_importer):
        """T-003: '1.1 xxx' 识别为 H2."""
        f = temp_txt_file("1.1 功能特点\n\n正文内容")
        doc = txt_importer.import_file(f)
        assert isinstance(doc.body[0], Heading)
        assert doc.body[0].level.value == 2

    @pytest.mark.p0
    def test_import_multi_level_headings(self, temp_txt_file, txt_importer):
        """T-010: 多级标题混合识别."""
        content = """第一章 总论

1.1 背景

1.1.1 详细背景

第二章 方法"""
        f = temp_txt_file(content)
        doc = txt_importer.import_file(f)
        headings = [e for e in doc.body if isinstance(e, Heading)]
        assert len(headings) == 4
        assert headings[0].level.value == 1  # 第一章
        assert headings[1].level.value == 2  # 1.1
        assert headings[2].level.value == 3  # 1.1.1
        assert headings[3].level.value == 1  # 第二章

    @pytest.mark.p1
    def test_import_all_uppercase_heading(self, temp_txt_file, txt_importer):
        """T-004: 全大写英文短文本识别为 H1."""
        f = temp_txt_file("INTRODUCTION\n\nThis is the content.")
        doc = txt_importer.import_file(f)
        assert isinstance(doc.body[0], Heading)

    @pytest.mark.p1
    def test_import_utf8_encoding(self, temp_txt_file, txt_importer):
        """T-005: UTF-8 编码正常解析."""
        f = temp_txt_file("中文测试 English 日本語", encoding="utf-8")
        doc = txt_importer.import_file(f)
        assert "中文测试" in doc.body[0].get_text()

    @pytest.mark.p1
    def test_import_gbk_encoding(self, temp_txt_file, txt_importer):
        """T-006: GBK 编码正常解析."""
        f = temp_txt_file("这是GBK编码的文本", encoding="gbk")
        doc = txt_importer.import_file(f)
        assert "GBK编码" in doc.body[0].get_text()

    @pytest.mark.p0
    def test_import_empty_file_raises(self, temp_dir, txt_importer):
        """T-008: 空文件抛出 ImportError."""
        empty = temp_dir / "empty.txt"
        empty.write_bytes(b"")
        with pytest.raises(ImportError, match="文件为空"):
            txt_importer.import_file(empty)

    @pytest.mark.p0
    def test_import_nonexistent_file_raises(self, txt_importer):
        """T-009: 不存在文件抛出 ImportError."""
        with pytest.raises(ImportError, match="不存在"):
            txt_importer.import_file(Path("/nonexistent/file.txt"))

    @pytest.mark.p1
    def test_document_title_from_filename(self, temp_txt_file, txt_importer):
        """文档标题应为文件名（无扩展名）."""
        f = temp_txt_file("content", filename="我的文档.txt")
        doc = txt_importer.import_file(f)
        assert doc.title == "我的文档"

    @pytest.mark.p1
    def test_single_newline_joins_paragraph(self, temp_txt_file, txt_importer):
        """单个换行符应合并为同一段落."""
        f = temp_txt_file("第一行\n第二行\n\n新段落")
        doc = txt_importer.import_file(f)
        assert doc.element_count() == 2
        assert "第一行" in doc.body[0].get_text()
        assert "第二行" in doc.body[0].get_text()


class TestImporterRegistry:
    """导入器注册中心测试."""

    @pytest.mark.p0
    def test_register_importer(self, importer_registry):
        """R-001: 注册导入器."""
        assert "文本文件" in importer_registry.list_importers()
        assert "Markdown" in importer_registry.list_importers()

    @pytest.mark.p0
    def test_auto_select_txt(self, importer_registry, temp_txt_file):
        """R-002: .txt 文件自动选择 TxtImporter."""
        f = temp_txt_file("test")
        imp = importer_registry.get_importer(f)
        assert isinstance(imp, TxtImporter)

    @pytest.mark.p0
    def test_unsupported_format_raises(self, importer_registry, temp_dir):
        """R-003: 不支持格式抛出 ImportError."""
        f = temp_dir / "test.pdf"
        f.write_text("content")
        with pytest.raises(ImportError, match="不支持"):
            importer_registry.import_file(f)

    @pytest.mark.p1
    def test_file_filter_string(self, importer_registry):
        """R-004: 过滤器字符串包含所有扩展名."""
        fs = importer_registry.file_filter_string()
        assert "*.txt" in fs
        assert "*.md" in fs
