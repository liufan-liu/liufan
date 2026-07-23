"""文档模型 — 统一的内部文档表示.

提供 Document、各种元素、样式类和枚举。
"""
from .enums import (
    Alignment,
    HeadingLevel,
    BreakType,
    LineSpacingRule,
    ListType,
)
from .styles import (
    RunStyle,
    ParagraphStyle,
    PageStyle,
    TableStyle,
)
from .elements import (
    Run,
    Paragraph,
    Heading,
    Table,
    TableCell,
    Image,
    PageBreak,
    TOCField,
    DocumentList,
    ListItem,
    CodeBlock,
    BlockQuote,
)
from .document import Document, HeaderFooter

__all__ = [
    # Enums
    "Alignment", "HeadingLevel", "BreakType", "LineSpacingRule", "ListType",
    # Styles
    "RunStyle", "ParagraphStyle", "PageStyle", "TableStyle",
    # Elements
    "Run", "Paragraph", "Heading", "Table", "TableCell", "Image",
    "PageBreak", "TOCField", "DocumentList", "ListItem", "CodeBlock", "BlockQuote",
    # Document
    "Document", "HeaderFooter",
]
