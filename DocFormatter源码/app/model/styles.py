"""样式定义 — 行内样式、段落样式、页面样式.

设计要点:
- 所有字段都是 Optional，用 None 表示"未设置/继承"
- 排版引擎合并样式时，只有非 None 的字段才会覆盖
- font_name 与 font_name_east_asia 分离，解决跨平台中文字体问题
"""
from dataclasses import dataclass, field
from typing import Optional

from .enums import Alignment, LineSpacingRule


@dataclass
class RunStyle:
    """行内样式（文字级别）.

    作用于一个 Run（文本片段）的视觉属性。
    """
    font_name: Optional[str] = None              # 西文字体（如 "Times New Roman"）
    font_name_east_asia: Optional[str] = None    # 中文字体（如 "宋体"、"黑体"）
    font_size: Optional[float] = None            # 字号（磅，1pt = 1/72 英寸）
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    strike: Optional[bool] = None
    color: Optional[str] = None                  # 十六进制颜色，如 "#000000"
    superscript: Optional[bool] = None
    subscript: Optional[bool] = None
    highlight: Optional[str] = None              # 高亮色

    def merge_with(self, other: "RunStyle") -> "RunStyle":
        """合并两个样式：other 中非 None 的字段覆盖 self.

        用于"模板样式 > 默认样式"或"用户手动 > 模板"的合并场景。
        """
        if other is None:
            return self
        result = RunStyle()
        for attr in self.__dataclass_fields__:
            other_val = getattr(other, attr)
            self_val = getattr(self, attr)
            setattr(result, attr, other_val if other_val is not None else self_val)
        return result

    def is_empty(self) -> bool:
        """判断样式是否全部未设置."""
        return all(getattr(self, attr) is None for attr in self.__dataclass_fields__)


@dataclass
class ParagraphStyle:
    """段落样式.

    作用于整个段落的布局属性。
    """
    alignment: Optional[Alignment] = None
    line_spacing: Optional[float] = None              # 行距数值
    line_spacing_rule: Optional[LineSpacingRule] = None  # 行距规则
    space_before: Optional[float] = None              # 段前距（磅）
    space_after: Optional[float] = None               # 段后距（磅）
    first_line_indent: Optional[float] = None         # 首行缩进（磅）
    first_line_indent_chars: Optional[float] = None   # 首行缩进（字符数，导出时按字号换算）
    left_indent: Optional[float] = None               # 左缩进（磅）
    right_indent: Optional[float] = None              # 右缩进（磅）
    keep_with_next: Optional[bool] = None             # 与下段同页
    keep_together: Optional[bool] = None              # 段中不分页
    page_break_before: Optional[bool] = None          # 段前分页
    widow_control: Optional[bool] = None              # 孤行控制

    def merge_with(self, other: "ParagraphStyle") -> "ParagraphStyle":
        """合并样式，other 中非 None 的字段覆盖 self."""
        if other is None:
            return self
        result = ParagraphStyle()
        for attr in self.__dataclass_fields__:
            other_val = getattr(other, attr)
            self_val = getattr(self, attr)
            setattr(result, attr, other_val if other_val is not None else self_val)
        return result

    def is_empty(self) -> bool:
        return all(getattr(self, attr) is None for attr in self.__dataclass_fields__)


@dataclass
class PageStyle:
    """页面样式 — 纸张尺寸与页边距.

    默认值为 A4 纸张、常规边距（单位：毫米）。
    """
    width: float = 210.0              # 纸张宽度 mm
    height: float = 297.0             # 纸张高度 mm
    margin_top: float = 25.4          # 上边距 mm（1 英寸）
    margin_bottom: float = 25.4       # 下边距 mm
    margin_left: float = 31.8         # 左边距 mm
    margin_right: float = 31.8        # 右边距 mm
    header_distance: float = 15.0     # 页眉距边界 mm
    footer_distance: float = 17.5     # 页脚距边界 mm
    columns: int = 1                  # 分栏数
    orientation: str = "portrait"     # "portrait" | "landscape"


@dataclass
class TableStyle:
    """表格样式."""
    border_style: Optional[str] = None     # 边框样式（如 "single", "double"）
    border_size: Optional[float] = None    # 边框粗细（1/8 磅）
    border_color: Optional[str] = None     # 边框颜色
    cell_padding: Optional[float] = None   # 单元格内边距（磅）
    width: Optional[float] = None          # 表格总宽度（磅或百分比）
    alignment: Optional[Alignment] = None  # 表格整体对齐
