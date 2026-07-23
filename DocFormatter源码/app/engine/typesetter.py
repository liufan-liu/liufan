"""排版引擎 — 将模板样式规则应用到文档模型.

这是整个系统的核心：它读取模板规则（来自 YAML），按元素类型或样式名查找对应规则，
然后把规则合并到文档模型的各个元素上，最终得到一份"排版好"的文档。
"""
from copy import deepcopy
from typing import Optional

from app.model.document import Document, HeaderFooter
from app.model.elements import (
    Paragraph, Heading, Table, Image, PageBreak, TOCField,
    CodeBlock, BlockQuote, DocumentList, Run,
)
from app.model.styles import RunStyle, ParagraphStyle, PageStyle
from app.model.enums import Alignment, HeadingLevel
from app.templates.template_manager import TemplateManager


class Typesetter:
    """排版引擎.

    将模板的样式规则合并到 Document 模型的各个元素上。
    合并规则：模板样式 > 元素原有样式（只有未设置的字段才会被模板填充）。
    """

    def __init__(self, template_rules: dict):
        """
        Args:
            template_rules: 模板字典，结构见 default.yaml
        """
        self.rules = template_rules

    def apply(self, doc: Document) -> Document:
        """对文档应用排版规则.

        Args:
            doc: 待排版的文档（会被就地修改）

        Returns:
            排版后的文档（同一对象）
        """
        # 深拷贝避免修改原始文档
        doc = deepcopy(doc)

        # 0. 规范化：清理导入文档中的"脏"格式（从网页复制的文档常有混乱的缩进/空格）
        self._normalize_document(doc)

        # 1. 应用页面设置
        self._apply_page_style(doc)

        # 2. 应用样式到各个元素
        styles_map = self.rules.get("styles", {})
        new_body = []

        # 如果模板启用了 TOC，在正文前插入目录域
        toc_config = self.rules.get("toc", {})
        if toc_config.get("enabled", False):
            new_body.append(TOCField(
                max_level=toc_config.get("max_level", 3),
                title=toc_config.get("title", "目录"),
            ))
            if toc_config.get("page_break_after", False):
                new_body.append(PageBreak())

        # 遍历元素应用样式
        for element in doc.body:
            styled = self._apply_style_to_element(element, styles_map)
            new_body.append(styled)

        doc.body = new_body

        # 3. 设置页眉页脚
        self._apply_header_footer(doc)

        # 4. 把模板的样式定义存到文档中，供导出器参考
        doc.style_definitions = styles_map

        return doc

    def _normalize_document(self, doc: Document) -> None:
        """规范化文档：清理从网页/其他来源复制的文档中的"脏"格式.

        - 清除段落级样式（缩进、对齐、行距等），让模板完全接管
        - 合并 Runs 并去除段首/段尾空白
        - 压缩超长空格序列（>10 个空格）为段落分隔
        - 压缩多个连续空格为单个空格
        - 去除仅含空白的段落
        - 基于内容启发式识别标题（如果文档没有 Heading 元素）
        """
        import re

        # 1. 清理每个段落，可能产生多个新段落
        cleaned_body = []
        for element in doc.body:
            if isinstance(element, Paragraph) and not isinstance(element, Heading):
                # 清除段落级样式（让模板接管）
                element.style = ParagraphStyle()

                # 合并所有 runs 的文本
                full_text = "".join(r.text for r in element.runs)

                # 按超长空格序列（>=10 空格）拆分为多个段落
                # 这种模式常见于从网页复制的文档（多个段落被压扁到一起）
                parts = re.split(r" {10,}", full_text)

                for part in parts:
                    # 去除段首/段尾空白
                    part = part.strip()
                    if not part:
                        continue

                    # 压缩内部多个连续空格为单个空格
                    part = re.sub(r" {2,}", " ", part)

                    # 创建新段落
                    new_para = Paragraph(
                        runs=[Run(text=part, style=element.runs[0].style if element.runs else RunStyle())],
                        style=ParagraphStyle(),
                        style_name=element.style_name,
                    )
                    cleaned_body.append(new_para)
            else:
                cleaned_body.append(element)

        doc.body = cleaned_body

        # 2. 启发式识别标题（如果文档中没有任何 Heading）
        if not doc.get_headings():
            self._detect_headings_heuristic(doc)

    def _detect_headings_heuristic(self, doc: Document) -> None:
        """基于内容启发式识别标题.

        规则（严格）:
        - 全加粗 + 长度适中 → Heading 1
        - 字号明显大于正文（> 16pt）→ Heading 1
        - 字号略大于正文（> 13pt）→ Heading 2
        - 短文本（20-60 字符）+ 无句末标点 + 紧跟长段落 → Heading 1
        - 排除：< 10 字符的文本、含"消息/日电/讯/报道"的文本（新闻导语）
        """
        import re

        paragraphs = [e for e in doc.body
                      if isinstance(e, Paragraph) and not isinstance(e, Heading)]

        if not paragraphs:
            return

        # 统计正文的平均长度（用于判断"短"段落）
        lengths = [len(p.get_text()) for p in paragraphs if p.get_text().strip()]
        if not lengths:
            return
        avg_length = sum(lengths) / len(lengths)

        # 新闻导语关键词（这些文本即使短也不是标题）
        news_keywords = ["消息", "日电", "讯", "报道", "记者", "央广网", "新华社",
                         "人民日报", "央视", "据悉", "据了解", "通讯员"]

        for i, para in enumerate(paragraphs):
            text = para.get_text().strip()
            if not text:
                continue

            # 排除：太短（标签/分类）
            if len(text) < 10:
                continue

            # 排除：含新闻导语关键词
            if any(kw in text for kw in news_keywords):
                continue

            # 排除：太长（超过平均长度的 70% 就不太可能是标题）
            if len(text) > avg_length * 0.7 and len(text) > 60:
                continue

            # 判断是否可能是标题
            is_heading = False
            heading_level = 1

            # 规则1: 全加粗（必须所有非空 run 都加粗）
            non_empty_runs = [r for r in para.runs if r.text.strip()]
            if non_empty_runs and all(r.style.bold for r in non_empty_runs):
                is_heading = True
                heading_level = 1

            # 规则2: 字号明显大于正文（> 16pt）
            if para.runs:
                sizes = [r.style.font_size for r in para.runs if r.style.font_size]
                if sizes:
                    max_size = max(sizes)
                    if max_size > 16:
                        is_heading = True
                        heading_level = 1 if max_size > 20 else 2
                    elif max_size > 13:
                        # 字号略大 + 较短文本 → H2
                        if len(text) < 50:
                            is_heading = True
                            heading_level = 2

            # 规则3: 短文本（20-60 字符）+ 无句末标点 + 紧跟长段落
            if (not is_heading and 20 <= len(text) <= 60 and
                    i + 1 < len(paragraphs) and
                    len(paragraphs[i + 1].get_text()) > 80):
                # 不以句末标点结尾，像标题
                if text[-1] not in "。.，,！!？?；;：:、）)】」』""'":
                    is_heading = True
                    heading_level = 1

            if is_heading:
                # 将 Paragraph 转换为 Heading
                new_heading = Heading(
                    runs=para.runs,
                    style=para.style,
                    style_name=para.style_name,
                    level=HeadingLevel(heading_level),
                )
                # 替换原元素
                try:
                    idx = doc.body.index(para)
                    doc.body[idx] = new_heading
                except ValueError:
                    pass  # 已被替换或移除

    def _apply_page_style(self, doc: Document) -> None:
        """应用页面设置到文档."""
        page_rules = self.rules.get("page")
        if not page_rules:
            return
        for key, value in page_rules.items():
            if hasattr(doc.page_style, key) and value is not None:
                setattr(doc.page_style, key, value)

    def _apply_style_to_element(self, element, styles_map: dict):
        """根据元素类型查找对应的样式规则并应用."""
        if isinstance(element, Heading):
            style_name = f"Heading {element.level.value}"
            rules = styles_map.get(style_name, {})
            self._apply_rules_to_paragraph(element, rules)

        elif isinstance(element, Paragraph):
            style_name = element.style_name or "Normal"
            rules = styles_map.get(style_name, styles_map.get("Normal", {}))
            self._apply_rules_to_paragraph(element, rules)

        elif isinstance(element, BlockQuote):
            rules = styles_map.get("BlockQuote", {})
            self._apply_rules_to_paragraph_like(element, rules)

        elif isinstance(element, Table):
            rules = styles_map.get("Table", {})
            # 应用样式到表格中的每个单元格
            for row in element.cells:
                for cell in row:
                    if cell.runs:
                        para_like = _ParaProxy(cell.runs, cell.style)
                        self._apply_rules_to_paragraph(para_like, rules)
                        cell.style = para_like.style

        elif isinstance(element, DocumentList):
            rules = styles_map.get("List", {})
            for item in element.items:
                para_like = _ParaProxy(item.runs, item.style)
                self._apply_rules_to_paragraph(para_like, rules)
                item.style = para_like.style

        elif isinstance(element, CodeBlock):
            rules = styles_map.get("Code", {})
            # 代码块转换为一个段落
            code_para = Paragraph(runs=[Run(text=element.code)])
            self._apply_rules_to_paragraph(code_para, rules)
            return code_para

        return element

    def _apply_rules_to_paragraph(self, para, rules: dict) -> None:
        """将样式规则应用到段落上（包括其中的所有 Run）."""
        if not rules:
            return
        self._apply_rules_to_paragraph_like(para, rules)

    def _apply_rules_to_paragraph_like(self, para, rules: dict) -> None:
        """应用样式规则到任何具有 runs 和 style 属性的对象."""
        # Run 规则
        run_rules = rules.get("run", {})
        if run_rules:
            run_style = _dict_to_run_style(run_rules)
            for run in para.runs:
                run.style = run.style.merge_with(run_style)

        # Paragraph 规则
        para_rules = rules.get("paragraph", {})
        if para_rules:
            para_style = _dict_to_paragraph_style(para_rules)
            para.style = para.style.merge_with(para_style)

    def _apply_header_footer(self, doc: Document) -> None:
        """应用页眉页脚."""
        header_rules = self.rules.get("header")
        footer_rules = self.rules.get("footer")

        if header_rules:
            doc.header = _dict_to_header_footer(header_rules, doc.title)
        if footer_rules:
            doc.footer = _dict_to_header_footer(footer_rules, doc.title)


class _ParaProxy:
    """用于对非 Paragraph 对象（如 TableCell）应用段落样式的代理."""

    def __init__(self, runs, style):
        self.runs = runs
        self.style = style


def _dict_to_run_style(d: dict) -> RunStyle:
    """将字典转换为 RunStyle 对象."""
    return RunStyle(
        font_name=d.get("font_name"),
        font_name_east_asia=d.get("font_name_east_asia"),
        font_size=_float(d.get("font_size")),
        bold=d.get("bold"),
        italic=d.get("italic"),
        underline=d.get("underline"),
        strike=d.get("strike"),
        color=d.get("color"),
        superscript=d.get("superscript"),
        subscript=d.get("subscript"),
        highlight=d.get("highlight"),
    )


def _dict_to_paragraph_style(d: dict) -> ParagraphStyle:
    """将字典转换为 ParagraphStyle 对象."""
    alignment = None
    if d.get("alignment"):
        try:
            alignment = Alignment(d["alignment"])
        except ValueError:
            alignment = None

    return ParagraphStyle(
        alignment=alignment,
        line_spacing=_float(d.get("line_spacing")),
        space_before=_float(d.get("space_before")),
        space_after=_float(d.get("space_after")),
        first_line_indent=_float(d.get("first_line_indent")),
        first_line_indent_chars=_float(d.get("first_line_indent_chars")),
        left_indent=_float(d.get("left_indent")),
        right_indent=_float(d.get("right_indent")),
        keep_with_next=d.get("keep_with_next"),
        keep_together=d.get("keep_together"),
        page_break_before=d.get("page_break_before"),
        widow_control=d.get("widow_control"),
    )


def _dict_to_header_footer(d: dict, doc_title: str = "") -> HeaderFooter:
    """将字典转换为 HeaderFooter 对象."""
    def _substitute(s):
        if not s:
            return ""
        return s.replace("{title}", doc_title).replace("{page_number}", "")

    hf = HeaderFooter(
        left=_substitute(d.get("left", "")),
        center=_substitute(d.get("center", "")),
        right=_substitute(d.get("right", "")),
    )
    # 检查是否包含页码占位符
    for key in ("left", "center", "right"):
        if d.get(key) and "{page_number}" in d[key]:
            hf.include_page_number = True
        if d.get(key) and "{title}" in d[key]:
            hf.include_title = True

    # 页眉页脚的字体
    if d.get("font_name") or d.get("font_size"):
        hf.style = ParagraphStyle()
        run_style = RunStyle(
            font_name=d.get("font_name"),
            font_size=_float(d.get("font_size")),
        )
        # 存到 style 的一个字段里，导出时提取
        hf._run_style = run_style
    return hf


def _float(val) -> Optional[float]:
    """安全转换为 float."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
