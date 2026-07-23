"""模板管理器 — 加载、切换、合并样式模板.

设计要点:
- 模板以 YAML 文件形式存储，支持内置模板和用户自定义模板
- 启动时扫描 builtin/ 和 user/ 目录
- 提供模板合并功能（模板样式 > 文档原有样式）
- 支持运行时动态添加用户模板
- 支持 PyInstaller 打包后的资源路径
"""
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class TemplateError(Exception):
    """模板相关异常."""
    pass


class TemplateManager:
    """模板管理器."""

    def __init__(self, builtin_dir: Optional[Path] = None, user_dir: Optional[Path] = None):
        """初始化模板管理器.

        Args:
            builtin_dir: 内置模板目录，默认为本模块同级 builtin/
            user_dir: 用户模板目录，默认为本模块同级 user/
        """
        # 支持 PyInstaller 打包后的路径
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后，资源在 _MEIPASS 目录
            # --add-data "app/templates/builtin:app/templates/builtin" 会将文件放在 _MEIPASS/app/templates/builtin
            base = Path(sys._MEIPASS) / "app" / "templates"
        else:
            base = Path(__file__).parent

        self.builtin_dir = builtin_dir or (base / "builtin")
        self.user_dir = user_dir or (base / "user")
        self._templates: Dict[str, dict] = {}
        self._load_all()

    def _load_all(self) -> None:
        """扫描并加载所有模板."""
        for tpl_dir in [self.builtin_dir, self.user_dir]:
            if not tpl_dir.exists():
                continue
            for yaml_file in tpl_dir.glob("*.yaml"):
                try:
                    tpl = self._load_template(yaml_file)
                    if tpl:
                        self._templates[tpl["name"]] = tpl
                except Exception as e:
                    print(f"[TemplateManager] 加载模板失败 {yaml_file}: {e}")

    def _load_template(self, path: Path) -> Optional[dict]:
        """加载单个 YAML 模板文件."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            return None
        if "name" not in data:
            data["name"] = path.stem
        if "description" not in data:
            data["description"] = ""
        if "styles" not in data:
            data["styles"] = {}
        data["_source_path"] = str(path)
        return data

    def list_templates(self) -> List[str]:
        """列出所有可用模板的名称."""
        return list(self._templates.keys())

    def get_template(self, name: str) -> Optional[dict]:
        """按名称获取模板.

        Returns:
            模板字典，如果不存在返回 None
        """
        return self._templates.get(name)

    def get_template_or_default(self, name: Optional[str] = None) -> dict:
        """获取指定模板，如果名称为空或不存在则返回默认模板."""
        if name and name in self._templates:
            return self._templates[name]
        if "通用文档" in self._templates:
            return self._templates["通用文档"]
        # 最后兜底：返回第一个
        if self._templates:
            return next(iter(self._templates.values()))
        raise TemplateError("没有任何可用模板")

    def add_user_template(self, yaml_content: str) -> str:
        """添加用户自定义模板.

        Args:
            yaml_content: YAML 格式的模板内容

        Returns:
            模板名称

        Raises:
            TemplateError: YAML 格式错误或无 name 字段
        """
        try:
            tpl = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise TemplateError(f"YAML 格式错误: {e}")

        if not isinstance(tpl, dict) or "name" not in tpl:
            raise TemplateError("模板必须包含 'name' 字段")

        name = tpl["name"]
        # 保存到用户模板目录
        self.user_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "_ -" else "_" for c in name)
        out_path = self.user_dir / f"{safe_name}.yaml"
        out_path.write_text(yaml_content, encoding="utf-8")

        tpl["_source_path"] = str(out_path)
        self._templates[name] = tpl
        return name

    def remove_user_template(self, name: str) -> bool:
        """删除用户自定义模板（不能删除内置模板）."""
        tpl = self._templates.get(name)
        if not tpl:
            return False
        source = tpl.get("_source_path")
        if not source or not source.startswith(str(self.user_dir)):
            raise TemplateError(f"不能删除内置模板: {name}")
        Path(source).unlink(missing_ok=True)
        del self._templates[name]
        return True

    def get_style_rules(self, template_name: str, style_name: str) -> dict:
        """获取模板中指定样式名的规则.

        Returns:
            样式规则字典，结构如:
            {
                "run": {"font_name": ..., "font_size": ...},
                "paragraph": {"alignment": ..., "line_spacing": ...}
            }
            如果不存在返回空字典
        """
        tpl = self.get_template(template_name)
        if not tpl:
            return {}
        return tpl.get("styles", {}).get(style_name, {})

    def reload(self) -> None:
        """重新加载所有模板（用于模板文件变更后）."""
        self._templates.clear()
        self._load_all()


def merge_style_rules(base: dict, override: dict) -> dict:
    """合并两个样式规则字典，override 中的非 None 字段覆盖 base.

    支持嵌套的 "run" 和 "paragraph" 子字典。
    """
    result = {}
    all_keys = set(base.keys()) | set(override.keys())
    for key in all_keys:
        base_val = base.get(key)
        over_val = override.get(key)
        if isinstance(base_val, dict) and isinstance(over_val, dict):
            result[key] = merge_style_rules(base_val, over_val)
        elif over_val is not None:
            result[key] = over_val
        elif base_val is not None:
            result[key] = base_val
    return result
