"""导入器基础 — 定义导入器抽象与注册中心.

设计要点:
- BaseImporter: 所有导入器的抽象基类
- ImporterRegistry: 导入器注册中心，按文件扩展名自动分发
- ImportError: 导入过程中的统一异常类型
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Set

from app.model.document import Document


class ImportError(Exception):
    """导入失败时抛出的异常."""
    pass


class BaseImporter(ABC):
    """导入器抽象基类.

    每个子类负责一种文件格式的解析，将其转换为统一的 Document 模型。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """导入器的名称（用于日志/UI 显示）."""
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> Set[str]:
        """支持的文件扩展名集合（小写，带点，如 {'.txt', '.md'}）."""
        ...

    @property
    def supported_mime_types(self) -> Set[str]:
        """支持的 MIME 类型（可选，用于文件选择对话框）."""
        return set()

    def can_import(self, file_path: Path) -> bool:
        """判断该导入器是否能处理指定文件."""
        return file_path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def import_file(self, file_path: Path) -> Document:
        """将文件解析为 Document 对象.

        Args:
            file_path: 待导入的文件路径

        Returns:
            Document: 解析得到的文档模型

        Raises:
            ImportError: 文件不存在、格式错误、解析失败时
        """
        ...

    def _validate_file(self, file_path: Path) -> None:
        """校验文件存在且可读."""
        if not file_path.exists():
            raise ImportError(f"文件不存在: {file_path}")
        if not file_path.is_file():
            raise ImportError(f"不是文件: {file_path}")
        if not file_path.stat().st_size > 0:
            raise ImportError(f"文件为空: {file_path}")


class ImporterRegistry:
    """导入器注册中心.

    维护一个导入器列表，根据文件扩展名自动选择合适的导入器。
    """

    def __init__(self):
        self._importers: List[BaseImporter] = []

    def register(self, importer: BaseImporter) -> None:
        """注册一个导入器."""
        self._importers.append(importer)

    def unregister(self, name: str) -> None:
        """按名称移除导入器."""
        self._importers = [imp for imp in self._importers if imp.name != name]

    def get_importer(self, file_path: Path) -> Optional[BaseImporter]:
        """根据文件扩展名查找合适的导入器.

        Returns:
            匹配的导入器，如果没有找到则返回 None
        """
        for imp in self._importers:
            if imp.can_import(file_path):
                return imp
        return None

    def import_file(self, file_path: Path) -> Document:
        """导入文件，自动选择合适的导入器.

        Raises:
            ImportError: 找不到合适的导入器或导入失败
        """
        file_path = Path(file_path)
        importer = self.get_importer(file_path)
        if importer is None:
            raise ImportError(
                f"不支持的文件格式: {file_path.suffix}\n"
                f"支持的格式: {', '.join(self.all_supported_extensions())}"
            )
        return importer.import_file(file_path)

    def all_supported_extensions(self) -> Set[str]:
        """返回所有已注册导入器支持的扩展名集合."""
        exts = set()
        for imp in self._importers:
            exts.update(imp.supported_extensions)
        return exts

    def file_filter_string(self) -> str:
        """生成用于 QFileDialog 的过滤器字符串.

        格式示例: "所有支持格式 (*.txt *.md);;文本文件 (*.txt)"
        """
        all_exts = self.all_supported_extensions()
        all_wildcards = " ".join(f"*{ext}" for ext in sorted(all_exts))
        parts = [f"所有支持格式 ({all_wildcards})"]

        for imp in self._importers:
            exts = " ".join(f"*{ext}" for ext in sorted(imp.supported_extensions))
            parts.append(f"{imp.name} ({exts})")

        return ";;".join(parts)

    def list_importers(self) -> List[str]:
        """列出所有已注册导入器的名称."""
        return [imp.name for imp in self._importers]
