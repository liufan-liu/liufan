"""TXT 导入器 — 将纯文本文件解析为 Document 模型.

规则:
- 按双换行符分割段落
- 空行视为段落分隔
- 自动识别简单标题格式:
  - 全是大写英文的行 → 标题（可选）
  - 以数字编号开头的行（如 "1. xxx", "第一章 xxx"）→ 标题
- 支持多种编码: UTF-8, GBK, GB2312, UTF-16 等
"""
import re
from pathlib import Path
from typing import List, Optional

from app.importers.base import BaseImporter, ImportError
from app.model.document import Document
from app.model.elements import Paragraph, Run, Heading
from app.model.enums import HeadingLevel


class TxtImporter(BaseImporter):

    @property
    def name(self) -> str:
        return "文本文件"

    @property
    def supported_extensions(self) -> set:
        return {".txt", ".text"}

    def import_file(self, file_path: Path) -> Document:
        self._validate_file(file_path)

        text = self._read_with_encoding(file_path)
        doc = Document()
        doc.title = file_path.stem  # 用文件名作为文档标题

        paragraphs = self._split_paragraphs(text)
        for para_text in paragraphs:
            element = self._parse_paragraph(para_text)
            doc.body.append(element)

        return doc

    def _read_with_encoding(self, file_path: Path) -> str:
        """尝试多种编码读取文件."""
        encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "big5", "utf-16", "latin-1"]
        content = file_path.read_bytes()

        # 检查 BOM
        if content.startswith(b"\xef\xbb\xbf"):
            return content.decode("utf-8-sig")
        if content.startswith(b"\xff\xfe"):
            return content.decode("utf-16-le")
        if content.startswith(b"\xfe\xff"):
            return content.decode("utf-16-be")

        for enc in encodings:
            try:
                return content.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue

        raise ImportError(f"无法识别文件编码: {file_path}")

    def _split_paragraphs(self, text: str) -> List[str]:
        """按空行分割段落.

        - 连续两个换行符 = 段落分隔
        - 单个换行符 = 段落内换行（保留为空格或保留为换行）
        """
        # 统一换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 按双换行分割
        raw_paras = re.split(r"\n\s*\n", text)

        result = []
        for para in raw_paras:
            # 将段落内的单个换行替换为空格（或保留）
            cleaned = " ".join(para.strip().split())
            if cleaned:
                result.append(cleaned)

        return result

    def _parse_paragraph(self, text: str) -> Paragraph:
        """解析一段文本，判断是否为标题."""
        heading_level = self._detect_heading(text)

        if heading_level is not None:
            return Heading(
                runs=[Run(text=text.strip())],
                level=HeadingLevel(heading_level),
            )
        else:
            return Paragraph(runs=[Run(text=text)])

    def _detect_heading(self, text: str) -> Optional[int]:
        """检测文本是否为标题格式.

        识别规则:
        - "第X章"、"第X节" → Heading 1/2
        - "1."、"1.1"、"1.1.1" → 根据层级编号
        - 全大写英文短文本 → Heading 1
        """
        text = text.strip()

        # 中文 "第X章" 格式
        if re.match(r"^第[一二三四五六七八九十百千\d]+章", text):
            return 1
        if re.match(r"^第[一二三四五六七八九十百千\d]+节", text):
            return 2

        # 数字编号 "1. xxx", "1.1 xxx", "1.1.1 xxx"
        # 支持带或不带末尾点号两种格式
        m = re.match(r"^(\d+(?:\.\d+)*)(?:\.\s+|\s+)(.+)", text)
        if m:
            level_str = m.group(1)
            level = level_str.count(".") + 1
            if 1 <= level <= 4:
                return level

        # 全大写英文短文本（少于 100 字符）
        if (text.isupper() and len(text) < 100 and
                re.match(r"^[A-Z0-9\s\-_:.,]+$", text)):
            return 1

        return None
