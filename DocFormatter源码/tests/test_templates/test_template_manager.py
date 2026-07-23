"""模板系统单元测试."""
import pytest
from app.templates import TemplateManager, TemplateError
from app.templates.template_manager import merge_style_rules


class TestTemplateManager:
    """模板管理器测试."""

    @pytest.mark.p0
    def test_load_builtin_template(self):
        """PL-001: 启动时加载内置模板."""
        tm = TemplateManager()
        templates = tm.list_templates()
        assert "通用文档" in templates

    @pytest.mark.p0
    def test_get_template(self):
        """PL-002: 按名称获取模板."""
        tm = TemplateManager()
        tpl = tm.get_template("通用文档")
        assert tpl is not None
        assert tpl["name"] == "通用文档"
        assert "page" in tpl
        assert "styles" in tpl

    @pytest.mark.p0
    def test_list_templates(self):
        """PL-003: 模板列表非空."""
        tm = TemplateManager()
        assert len(tm.list_templates()) >= 1

    @pytest.mark.p1
    def test_get_nonexistent_template(self):
        """PL-004: 不存在的模板返回 None."""
        tm = TemplateManager()
        assert tm.get_template("不存在的模板") is None

    @pytest.mark.p0
    def test_get_template_or_default(self):
        """PL-005: 默认模板获取."""
        tm = TemplateManager()
        tpl = tm.get_template_or_default(None)
        assert tpl is not None
        assert tpl["name"] == "通用文档"

    @pytest.mark.p0
    def test_get_style_rules(self):
        """PL-006: 获取样式规则."""
        tm = TemplateManager()
        rules = tm.get_style_rules("通用文档", "Normal")
        assert "run" in rules
        assert "paragraph" in rules
        assert rules["run"]["font_name"] == "宋体"
        assert rules["run"]["font_size"] == 12

    @pytest.mark.p1
    def test_add_user_template(self, temp_dir):
        """PL-007: 添加用户模板."""
        user_dir = temp_dir / "user"
        tm = TemplateManager(user_dir=user_dir)
        yaml_content = """name: "测试模板"
description: "用于测试"
styles:
  Normal:
    run:
      font_name: "Arial"
      font_size: 11
"""
        name = tm.add_user_template(yaml_content)
        assert name == "测试模板"
        assert tm.get_template("测试模板") is not None
        # 验证已保存到文件
        assert (user_dir / "测试模板.yaml").exists()

    @pytest.mark.p1
    def test_remove_user_template(self, temp_dir):
        """PL-008: 删除用户模板."""
        user_dir = temp_dir / "user"
        tm = TemplateManager(user_dir=user_dir)
        yaml_content = 'name: "可删除模板"\nstyles: {}'
        tm.add_user_template(yaml_content)
        assert tm.remove_user_template("可删除模板") is True
        assert tm.get_template("可删除模板") is None

    @pytest.mark.p1
    def test_cannot_remove_builtin_template(self):
        """PL-009: 不能删除内置模板."""
        tm = TemplateManager()
        with pytest.raises(TemplateError, match="内置"):
            tm.remove_user_template("通用文档")

    @pytest.mark.p1
    def test_invalid_yaml_raises(self, temp_dir):
        """PL-010: 无效 YAML 抛出 TemplateError."""
        tm = TemplateManager(user_dir=temp_dir)
        with pytest.raises(TemplateError, match="YAML"):
            tm.add_user_template("invalid: [yaml: broken")

    @pytest.mark.p1
    def test_yaml_without_name_raises(self, temp_dir):
        """模板必须有 name 字段."""
        tm = TemplateManager(user_dir=temp_dir)
        with pytest.raises(TemplateError, match="name"):
            tm.add_user_template("styles: {}")


class TestMergeStyleRules:
    """样式规则合并测试."""

    @pytest.mark.p0
    def test_merge_flat_dicts(self):
        """PL-011: 扁平字典合并."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge_style_rules(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    @pytest.mark.p0
    def test_merge_nested_dicts(self):
        """嵌套字典递归合并."""
        base = {"run": {"font_name": "Arial", "font_size": 12}}
        override = {"run": {"font_size": 14, "bold": True}}
        result = merge_style_rules(base, override)
        assert result["run"]["font_name"] == "Arial"
        assert result["run"]["font_size"] == 14
        assert result["run"]["bold"] is True

    @pytest.mark.p1
    def test_merge_none_values(self):
        """None 值不覆盖已有值."""
        base = {"run": {"font_name": "Arial"}}
        override = {"run": {"font_name": None, "font_size": 14}}
        result = merge_style_rules(base, override)
        assert result["run"]["font_name"] == "Arial"  # None 不覆盖

    @pytest.mark.p1
    def test_merge_empty_dicts(self):
        """空字典合并."""
        assert merge_style_rules({}, {}) == {}
        assert merge_style_rules({"a": 1}, {}) == {"a": 1}
        assert merge_style_rules({}, {"a": 1}) == {"a": 1}
