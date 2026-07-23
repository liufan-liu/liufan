"""目录生成器 — 从文档中提取标题，生成目录结构."""
from typing import List

from app.model.document import Document
from app.model.elements import Heading


class TOCGenerator:
    """目录生成器.

    注意：导出的 docx 中目录的实际内容由 Word 在打开时生成（通过 TOC 域代码）。
    本类主要用于预览区显示模拟目录。
    """

    def __init__(self, max_level: int = 3, title: str = "目录"):
        self.max_level = max_level
        self.title = title

    def generate(self, doc: Document) -> List[dict]:
        """从文档中提取标题，生成目录条目.

        Returns:
            目录条目列表，每项包含 level、text、page_number 字段。
            page_number 始终为 None（需要 Word 运行时计算）。
        """
        headings = doc.get_headings()
        entries = []

        for heading in headings:
            if heading.level.value <= self.max_level:
                entries.append({
                    "level": heading.level.value,
                    "text": heading.get_text(),
                    "page_number": None,
                })

        return entries

    def to_text(self, doc: Document) -> str:
        """生成文本形式的目录（用于预览或调试）."""
        entries = self.generate(doc)
        lines = [self.title, "=" * 40]
        for entry in entries:
            indent = "  " * (entry["level"] - 1)
            lines.append(f"{indent}{entry['text']}")
        return "\n".join(lines)
