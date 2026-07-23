"""枚举类型定义 — 文档模型的基础常量."""
from enum import Enum


class Alignment(Enum):
    """水平对齐方式."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class HeadingLevel(Enum):
    """标题层级（H1-H4，对应 Word 的 Heading 1-4）."""
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4


class BreakType(Enum):
    """分隔符类型."""
    PAGE = "page"           # 分页符
    SECTION = "section"     # 分节符
    LINE = "line"           # 换行符


class LineSpacingRule(Enum):
    """行距规则."""
    SINGLE = "single"           # 单倍行距
    ONE_AND_HALF = "1.5"        # 1.5 倍
    DOUBLE = "double"           # 双倍
    MULTIPLE = "multiple"       # 多倍（自定义倍数）
    EXACT = "exact"             # 固定值（磅）
    AT_LEAST = "at_least"       # 最小值（磅）


class ListType(Enum):
    """列表类型."""
    ORDERED = "ordered"
    UNORDERED = "unordered"
