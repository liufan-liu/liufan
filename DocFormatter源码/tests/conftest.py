"""pytest 共享 fixtures — 所有测试模块共用的测试数据."""
import sys
import tempfile
from pathlib import Path
from typing import List

import pytest

# 确保项目根目录在 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.model.document import Document, HeaderFooter
from app.model.elements import (
    Run, Paragraph, Heading, Table, Image, PageBreak,
    TOCField, CodeBlock, BlockQuote, DocumentList, ListItem,
)
from app.model.styles import RunStyle, ParagraphStyle, PageStyle
from app.model.enums import Alignment, HeadingLevel, ListType
from app.templates import TemplateManager
from app.importers.base import ImporterRegistry
from app.importers.txt_importer import TxtImporter
from app.importers.md_importer import MarkdownImporter
from app.importers.docx_importer import DocxImporter


# ===== 测试数据路径 =====

FIXTURES_DIR = Path(__file__).parent / "fixtures"
INPUTS_DIR = FIXTURES_DIR / "inputs"
EXPECTED_DIR = FIXTURES_DIR / "expected"
TEMPLATES_DIR = FIXTURES_DIR / "templates"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def inputs_dir():
    return INPUTS_DIR


# ===== 文档模型 fixtures =====

@pytest.fixture
def empty_document():
    """空文档."""
    return Document()


@pytest.fixture
def simple_document():
    """含简单标题和段落的文档."""
    doc = Document(title="测试文档", author="测试员")
    doc.add_heading("第一章 简介", level=1)
    doc.add_paragraph("这是第一段正文内容。")
    doc.add_heading("1.1 背景", level=2)
    doc.add_paragraph("这是背景介绍。")
    return doc


@pytest.fixture
def complex_document():
    """包含所有元素类型的复杂文档."""
    doc = Document(title="复杂文档")
    doc.add_heading("标题一", level=1)
    doc.add_paragraph("普通段落。")
    doc.add_heading("标题二", level=2)

    # 带样式的段落
    para = Paragraph(
        runs=[
            Run(text="粗体", style=RunStyle(bold=True)),
            Run(text="和"),
            Run(text="斜体", style=RunStyle(italic=True)),
        ],
        style=ParagraphStyle(alignment=Alignment.CENTER),
    )
    doc.body.append(para)

    # 表格
    doc.body.append(Table.from_data([
        ["姓名", "年龄", "城市"],
        ["张三", "25", "北京"],
        ["李四", "30", "上海"],
    ]))

    # 列表
    doc.body.append(DocumentList(
        items=[
            ListItem(runs=[Run(text="第一项")]),
            ListItem(runs=[Run(text="第二项")]),
        ],
        list_type=ListType.UNORDERED,
    ))

    # 代码块
    doc.body.append(CodeBlock(code="print('hello')", language="python"))

    # 引用
    doc.body.append(BlockQuote(runs=[Run(text="这是一段引用")]))

    # 分页
    doc.body.append(PageBreak())

    return doc


# ===== 样式 fixtures =====

@pytest.fixture
def default_template():
    """默认模板的规则字典."""
    tm = TemplateManager()
    return tm.get_template("通用文档")


@pytest.fixture
def minimal_template():
    """极简模板（用于测试模板应用逻辑）."""
    return {
        "name": "极简模板",
        "page": {
            "width": 210,
            "height": 297,
            "margin_top": 20,
            "margin_bottom": 20,
            "margin_left": 25,
            "margin_right": 25,
        },
        "styles": {
            "Heading 1": {
                "run": {"font_name": "Arial", "font_size": 20, "bold": True},
                "paragraph": {"alignment": "center"},
            },
            "Normal": {
                "run": {"font_name": "Times New Roman", "font_size": 11},
                "paragraph": {"alignment": "left", "line_spacing": 1.25},
            },
        },
    }


# ===== 导入器 fixtures =====

@pytest.fixture
def txt_importer():
    return TxtImporter()


@pytest.fixture
def md_importer():
    return MarkdownImporter()


@pytest.fixture
def docx_importer():
    return DocxImporter()


@pytest.fixture
def importer_registry():
    reg = ImporterRegistry()
    reg.register(TxtImporter())
    reg.register(MarkdownImporter())
    reg.register(DocxImporter())
    return reg


# ===== 临时文件 fixtures =====

@pytest.fixture
def temp_dir():
    """临时目录，测试结束后自动清理."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_txt_file(temp_dir):
    """创建临时 TXT 文件."""
    def _create(content: str, filename: str = "test.txt", encoding: str = "utf-8") -> Path:
        path = temp_dir / filename
        path.write_text(content, encoding=encoding)
        return path
    return _create


@pytest.fixture
def temp_md_file(temp_dir):
    """创建临时 MD 文件."""
    def _create(content: str, filename: str = "test.md") -> Path:
        path = temp_dir / filename
        path.write_text(content, encoding="utf-8")
        return path
    return _create


@pytest.fixture
def temp_docx_path(temp_dir):
    """临时 DOCX 输出路径."""
    return temp_dir / "output.docx"
