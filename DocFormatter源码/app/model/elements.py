"""文档元素 — 文档模型中可出现在文档体内的所有元素类型.

设计要点:
- 所有元素都是数据类（dataclass），便于序列化/反序列化
- Run 是文本片段，Paragraph 由多个 Run 组成（相同样式的一段文字）
- Heading 继承 Paragraph，增加层级属性
- BodyElement 类型别名表示文档体中所有可能的元素类型
"""
from dataclasses import dataclass, field
from typing import List, Optional, Union

from .styles import RunStyle, ParagraphStyle, TableStyle
from .enums import HeadingLevel, Alignment, ListType


@dataclass
class Run:
    """文本片段 — 相同样式的一段连续文字.

    一个段落可包含多个 Run，比如 "这是 加粗文本 普通文字" 就是 3 个 Run。
    """
    text: str
    style: RunStyle = field(default_factory=RunStyle)

    def clone(self) -> "Run":
        from copy import deepcopy
        return deepcopy(self)


@dataclass
class Paragraph:
    """段落 — 文档的基本组成单元.

    runs: 段落内的文本片段列表
    style: 段落本身的样式（对齐、行距、缩进等）
    style_name: 关联的样式名（如 "Normal"、"BlockQuote"），用于从模板查找样式规则
    """
    runs: List[Run] = field(default_factory=list)
    style: ParagraphStyle = field(default_factory=ParagraphStyle)
    style_name: Optional[str] = None

    def get_text(self) -> str:
        """获取段落的纯文本内容."""
        return "".join(run.text for run in self.runs)

    def clone(self) -> "Paragraph":
        from copy import deepcopy
        return deepcopy(self)


@dataclass
class Heading(Paragraph):
    """标题 — 继承段落，增加层级属性.

    level: 标题层级（H1-H4）
    """
    level: HeadingLevel = HeadingLevel.H1

    @property
    def style_name(self) -> Optional[str]:
        """标题自动关联 "Heading N" 样式名."""
        return f"Heading {self.level.value}"

    @style_name.setter
    def style_name(self, value: Optional[str]):
        """允许外部设置（但通常由 level 自动生成）."""
        pass


@dataclass
class TableCell:
    """表格单元格."""
    text: str = ""
    runs: List[Run] = field(default_factory=list)
    style: ParagraphStyle = field(default_factory=ParagraphStyle)
    row_span: int = 1           # 纵向合并单元格数
    col_span: int = 1           # 横向合并单元格数
    shading: Optional[str] = None  # 背景颜色（十六进制）


@dataclass
class Table:
    """表格.

    使用二维 cell 矩阵表示，cell 可以是 TableCell。
    """
    rows: int = 0
    cols: int = 0
    cells: List[List[TableCell]] = field(default_factory=list)
    style: TableStyle = field(default_factory=TableStyle)
    caption: Optional[str] = None   # 表格标题

    @classmethod
    def from_data(cls, data: List[List[str]], caption: Optional[str] = None) -> "Table":
        """从纯二维字符串数组快速创建表格."""
        rows = len(data)
        cols = max(len(row) for row in data) if data else 0
        cells = []
        for row in data:
            row_cells = []
            for cell_text in row:
                row_cells.append(TableCell(text=cell_text))
            # 补齐不足列
            while len(row_cells) < cols:
                row_cells.append(TableCell(text=""))
            cells.append(row_cells)
        return cls(rows=rows, cols=cols, cells=cells, caption=caption)


@dataclass
class Image:
    """图片.

    path: 图片文件路径（绝对或相对）
    width/height: 显示尺寸（单位 cm，None 表示保持原始尺寸）
    caption: 图片题注
    alignment: 图片对齐方式
    """
    path: str = ""
    width: Optional[float] = None
    height: Optional[float] = None
    caption: Optional[str] = None
    alignment: Alignment = Alignment.CENTER


@dataclass
class PageBreak:
    """分页符."""
    pass


@dataclass
class TOCField:
    """目录域 — 导出时在 docx 中插入 TOC 域代码.

    max_level: 目录包含的标题最大层级（1-4）
    title: 目录标题（如 "目录"、"目  录"）
    """
    max_level: int = 3
    title: str = "目录"


@dataclass
class ListItem:
    """列表项."""
    runs: List[Run] = field(default_factory=list)
    style: ParagraphStyle = field(default_factory=ParagraphStyle)
    list_type: ListType = ListType.UNORDERED
    level: int = 0   # 嵌套层级（0 为顶层）


@dataclass
class DocumentList:
    """列表（有序/无序）.

    重命名以避免与 typing.List 冲突。
    """
    items: List[ListItem] = field(default_factory=list)
    list_type: ListType = ListType.UNORDERED


@dataclass
class CodeBlock:
    """代码块 — 以等宽字体、无缩进、单倍行距显示.

    导出时通常转换为带灰色底纹的段落。
    """
    code: str = ""
    language: Optional[str] = None


@dataclass
class BlockQuote:
    """引用块 — 通常用楷体、缩进显示."""
    runs: List[Run] = field(default_factory=list)
    style: ParagraphStyle = field(default_factory=ParagraphStyle)


# 文档体中所有可能的元素类型
BodyElement = Union[
    Paragraph,
    Heading,
    Table,
    Image,
    PageBreak,
    TOCField,
    DocumentList,
    CodeBlock,
    BlockQuote,
]
