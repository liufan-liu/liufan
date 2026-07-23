"""文档模型根节点 — 统一的内部文档表示.

所有导入器将输入文件转换为 Document 对象，
排版引擎在 Document 上应用样式规则，
导出器将 Document 写为具体格式（如 .docx）。
"""
from dataclasses import dataclass, field
from typing import List, Optional

from .elements import BodyElement, Heading
from .styles import PageStyle, ParagraphStyle


@dataclass
class HeaderFooter:
    """页眉或页脚的内容.

    left/center/right: 三个区域的文本内容
    include_page_number: 是否包含页码（占位符 {page_number}）
    include_title: 是否包含文档标题（占位符 {title}）
    style: 页眉页脚的段落样式
    """
    left: str = ""
    center: str = ""
    right: str = ""
    include_page_number: bool = False
    include_title: bool = False
    style: ParagraphStyle = field(default_factory=ParagraphStyle)

    def is_empty(self) -> bool:
        """判断是否为空."""
        return not (self.left or self.center or self.right or
                    self.include_page_number or self.include_title)


@dataclass
class Document:
    """统一文档模型 — 所有导入/导出操作的中间表示.

    这是一个"中立"的文档表示，不包含任何具体格式（如 docx、html）的细节。
    排版引擎在此之上应用模板规则，导出器将其转换为具体格式。
    """
    # 元信息
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: List[str] = field(default_factory=list)

    # 页面设置
    page_style: PageStyle = field(default_factory=PageStyle)

    # 页眉页脚
    header: Optional[HeaderFooter] = None
    footer: Optional[HeaderFooter] = None

    # 文档体（有序元素列表）
    body: List[BodyElement] = field(default_factory=list)

    # 样式定义表（样式名 -> 样式规则 dict）
    # 由排版引擎在应用模板时填充，也可由用户手动覆盖
    style_definitions: dict = field(default_factory=dict)

    # ---- 辅助方法 ----

    def get_headings(self) -> List[Heading]:
        """提取所有标题元素，用于生成目录或文档结构树."""
        return [elem for elem in self.body if isinstance(elem, Heading)]

    def get_paragraphs(self) -> list:
        """提取所有段落（包括标题，因为 Heading 继承 Paragraph）."""
        from .elements import Paragraph
        return [elem for elem in self.body if isinstance(elem, Paragraph)]

    def add_paragraph(self, text: str, style_name: str = "Normal") -> None:
        """快捷方法：添加一个纯文本段落."""
        from .elements import Paragraph, Run
        self.body.append(Paragraph(
            runs=[Run(text=text)],
            style_name=style_name,
        ))

    def add_heading(self, text: str, level: int = 1) -> None:
        """快捷方法：添加一个标题."""
        from .elements import Heading as HeadingClass, Run
        from .enums import HeadingLevel
        self.body.append(HeadingClass(
            runs=[Run(text=text)],
            level=HeadingLevel(min(max(level, 1), 4)),
        ))

    def clear(self) -> None:
        """清空文档内容（保留页面设置和元信息）."""
        self.body.clear()
        self.header = None
        self.footer = None

    def element_count(self) -> int:
        """返回文档体中的元素数量."""
        return len(self.body)

    def word_count(self) -> int:
        """估算文档字数（中文按字符，英文按单词）."""
        from .elements import Paragraph, Table
        count = 0
        for elem in self.body:
            if isinstance(elem, Paragraph):
                text = elem.get_text()
                count += _count_text(text)
            elif isinstance(elem, Table):
                for row in elem.cells:
                    for cell in row:
                        count += _count_text(cell.text)
        return count


def _count_text(text: str) -> int:
    """统计文本长度（中文算 1，英文单词算 1）."""
    import re
    # 中文字符
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    # 英文单词
    english_words = len(re.findall(r"[a-zA-Z]+", text))
    return chinese_chars + english_words
