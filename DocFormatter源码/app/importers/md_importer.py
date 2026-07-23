"""Markdown 导入器 — 将 .md 文件解析为 Document 模型.

使用 markdown-it-py 解析 Markdown，支持 CommonMark 规范 + GFM 扩展（表格、任务列表等）。
"""
import re
from pathlib import Path
from typing import List, Optional, Tuple

from markdown_it import MarkdownIt

from app.importers.base import BaseImporter, ImportError
from app.model.document import Document
from app.model.elements import (
    Run, Paragraph, Heading, Table, TableCell, Image, PageBreak,
    CodeBlock, BlockQuote, DocumentList, ListItem,
)
from app.model.styles import RunStyle, ParagraphStyle
from app.model.enums import HeadingLevel, Alignment, ListType


class MarkdownImporter(BaseImporter):

    @property
    def name(self) -> str:
        return "Markdown"

    @property
    def supported_extensions(self) -> set:
        return {".md", ".markdown"}

    def import_file(self, file_path: Path) -> Document:
        self._validate_file(file_path)

        text = file_path.read_text(encoding="utf-8")
        doc = Document()
        doc.title = file_path.stem

        # 启用表格等扩展语法
        md = MarkdownIt("commonmark", {"html": True})
        try:
            from mdit_py_plugins.front_matter import front_matter_plugin
            front_matter_plugin(md)
        except ImportError:
            pass

        try:
            from mdit_py_plugins.footnote import footnote_plugin
            footnote_plugin(md)
        except ImportError:
            pass

        # 启用表格（GFM 扩展）
        md.enable("table")

        tokens = md.parse(text)
        self._process_tokens(tokens, doc)

        return doc

    def _process_tokens(self, tokens: list, doc: Document) -> None:
        """遍历 token 流构建文档模型."""
        i = 0
        while i < len(tokens):
            token = tokens[i]
            ttype = token.type

            # 标题
            if ttype == "heading_open":
                level = int(token.tag[1])
                i += 1  # inline token
                inline_token = tokens[i]
                runs = self._parse_inline(inline_token)
                heading = Heading(
                    runs=runs,
                    level=HeadingLevel(min(max(level, 1), 4)),
                )
                doc.body.append(heading)
                # i 当前在 inline token，下面 i += 1 后到达 heading_close
                # 再加 1 跳过 heading_close，所以这里直接 i += 1 并用 continue
                i += 1  # 现在 i 指向 heading_close
                i += 1  # 跳过 heading_close
                continue

            # 段落
            elif ttype == "paragraph_open":
                i += 1  # inline token
                inline_token = tokens[i]
                runs = self._parse_inline(inline_token)
                if runs:
                    doc.body.append(Paragraph(runs=runs))
                i += 1  # paragraph_close
                i += 1  # 跳过 paragraph_close
                continue

            # 代码块
            elif ttype == "fence" or ttype == "code_block":
                code = token.content.rstrip("\n")
                language = token.info if ttype == "fence" else None
                doc.body.append(CodeBlock(code=code, language=language))
                i += 1
                continue

            # 表格
            elif ttype == "table_open":
                table, next_i = self._parse_table(tokens, i)
                doc.body.append(table)
                i = next_i
                continue

            # 图片（独立段落形式）
            elif ttype == "image":
                img = Image(
                    path=token.attrGet("src") or "",
                    caption=token.attrGet("alt") or token.content or None,
                )
                doc.body.append(img)
                i += 1
                continue

            # 水平分隔线 → 分页符
            elif ttype == "hr":
                doc.body.append(PageBreak())
                i += 1
                continue

            # 有序/无序列表
            elif ttype == "bullet_list_open":
                lst, next_i = self._parse_list(tokens, i, ordered=False)
                doc.body.append(lst)
                i = next_i
                continue

            elif ttype == "ordered_list_open":
                lst, next_i = self._parse_list(tokens, i, ordered=True)
                doc.body.append(lst)
                i = next_i
                continue

            # 引用块
            elif ttype == "blockquote_open":
                quote, next_i = self._parse_blockquote(tokens, i)
                doc.body.append(quote)
                i = next_i
                continue

            # HTML 块（检查是否包含 <img> 标签）
            elif ttype == "html_block":
                img = self._try_parse_html_image(token.content)
                if img:
                    doc.body.append(img)
                i += 1
                continue

            i += 1

    def _parse_inline(self, token) -> List[Run]:
        """解析 inline token 为 Run 列表.

        追踪 bold/italic/strikethrough/code 等状态。
        """
        runs: List[Run] = []
        bold = False
        italic = False
        strike = False
        code = False

        if token.children is None:
            if token.content:
                runs.append(Run(text=token.content))
            return runs

        for child in token.children:
            ctype = child.type

            if ctype == "text":
                runs.append(Run(
                    text=child.content,
                    style=RunStyle(
                        bold=bold or None,
                        italic=italic or None,
                        strike=strike or None,
                    ),
                ))
            elif ctype == "softbreak":
                runs.append(Run(text="\n"))
            elif ctype == "hardbreak":
                runs.append(Run(text="\n"))
            elif ctype == "strong_open":
                bold = True
            elif ctype == "strong_close":
                bold = False
            elif ctype == "em_open":
                italic = True
            elif ctype == "em_close":
                italic = False
            elif ctype == "s_open":
                strike = True
            elif ctype == "s_close":
                strike = False
            elif ctype == "code_inline":
                runs.append(Run(
                    text=child.content,
                    style=RunStyle(font_name="Courier New"),
                ))
            elif ctype == "image":
                # 内联图片作为文本占位符
                src = child.attrGet("src") or ""
                alt = child.content or ""
                runs.append(Run(text=f"[图片: {alt or src}]"))

        return runs

    def _parse_table(self, tokens: list, start_idx: int) -> Tuple[Table, int]:
        """解析表格 tokens.

        Returns: (Table, 下一个 token 索引)
        """
        rows_data: List[List[TableCell]] = []
        current_row: List[TableCell] = []
        current_cell_content: List[Run] = []
        in_thead = False
        i = start_idx + 1  # 跳过 table_open

        while i < len(tokens):
            token = tokens[i]
            ttype = token.type

            if ttype == "table_close":
                # 最后一个单元格
                if current_cell_content:
                    current_row.append(TableCell(
                        text="".join(r.text for r in current_cell_content),
                        runs=current_cell_content,
                    ))
                if current_row:
                    rows_data.append(current_row)
                i += 1
                break

            elif ttype == "thead_open":
                in_thead = True
            elif ttype == "thead_close":
                in_thead = False
            elif ttype == "tbody_open" or ttype == "tbody_close":
                pass
            elif ttype == "tr_open":
                current_row = []
            elif ttype == "tr_close":
                if current_cell_content:
                    current_row.append(TableCell(
                        text="".join(r.text for r in current_cell_content),
                        runs=current_cell_content,
                    ))
                    current_cell_content = []
                rows_data.append(current_row)
                current_row = []  # 重置，避免在 table_close 处重复添加
            elif ttype in ("th_open", "td_open"):
                current_cell_content = []
            elif ttype in ("th_close", "td_close"):
                current_row.append(TableCell(
                    text="".join(r.text for r in current_cell_content),
                    runs=current_cell_content,
                ))
                current_cell_content = []
            elif ttype == "inline":
                if token.children:
                    current_cell_content.extend(self._parse_inline(token))
                elif token.content:
                    current_cell_content.append(Run(text=token.content))

            i += 1

        rows = len(rows_data)
        cols = max(len(row) for row in rows_data) if rows_data else 0
        table = Table(rows=rows, cols=cols, cells=rows_data)
        return table, i

    def _parse_list(self, tokens: list, start_idx: int, ordered: bool) -> Tuple[DocumentList, int]:
        """解析列表 tokens.

        Returns: (DocumentList, 下一个 token 索引)
        """
        list_type = ListType.ORDERED if ordered else ListType.UNORDERED
        items: List[ListItem] = []
        current_runs: List[Run] = []
        level = 0
        list_open_count = 0
        i = start_idx + 1

        while i < len(tokens):
            token = tokens[i]
            ttype = token.type

            if ttype in ("bullet_list_close", "ordered_list_close"):
                list_open_count -= 1
                if list_open_count < 0:
                    # 当前列表结束
                    if current_runs:
                        items.append(ListItem(
                            runs=current_runs,
                            list_type=list_type,
                            level=level,
                        ))
                    i += 1
                    break

            elif ttype in ("bullet_list_open", "ordered_list_open"):
                list_open_count += 1
                level += 1

            elif ttype == "list_item_open":
                current_runs = []

            elif ttype == "list_item_close":
                if current_runs:
                    items.append(ListItem(
                        runs=current_runs,
                        list_type=list_type,
                        level=max(0, level - 1),
                    ))
                    current_runs = []

            elif ttype == "paragraph_open":
                pass
            elif ttype == "paragraph_close":
                pass
            elif ttype == "inline":
                current_runs.extend(self._parse_inline(token))

            i += 1

        return DocumentList(items=items, list_type=list_type), i

    def _parse_blockquote(self, tokens: list, start_idx: int) -> Tuple[BlockQuote, int]:
        """解析引用块 tokens.

        Returns: (BlockQuote, 下一个 token 索引)
        """
        runs: List[Run] = []
        depth = 0
        i = start_idx + 1

        while i < len(tokens):
            token = tokens[i]
            ttype = token.type

            if ttype == "blockquote_open":
                depth += 1
            elif ttype == "blockquote_close":
                depth -= 1
                if depth < 0:
                    i += 1
                    break
            elif ttype == "paragraph_open":
                if runs:
                    runs.append(Run(text="\n"))
            elif ttype == "inline":
                runs.extend(self._parse_inline(token))

            i += 1

        return BlockQuote(runs=runs), i

    def _try_parse_html_image(self, html: str) -> Optional[Image]:
        """尝试从 HTML 块中提取 <img> 标签."""
        match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', html, re.IGNORECASE)
        if match:
            src = match.group(1)
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', html, re.IGNORECASE)
            alt = alt_match.group(1) if alt_match else None
            return Image(path=src, caption=alt)
        return None
