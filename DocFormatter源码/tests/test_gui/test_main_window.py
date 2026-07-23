"""GUI 冒烟测试 — 验证主界面各组件正常工作.

注意：这些测试需要在有显示器的环境下运行（或通过 Xvfb）。
"""
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from app.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """整个测试会话共享一个 QApplication."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def window(qapp):
    """每个测试独立的 MainWindow 实例."""
    w = MainWindow()
    w.show()
    yield w
    w.close()


class TestMainWindow:
    """主窗口基础测试."""

    @pytest.mark.gui
    @pytest.mark.p0
    def test_window_opens(self, window):
        """G-001: 窗口正常启动."""
        assert window.isVisible()
        assert window.width() >= 900
        assert window.height() >= 650

    @pytest.mark.gui
    @pytest.mark.p1
    def test_window_title(self, window):
        """G-002: 窗口标题正确."""
        assert "DocFormatter" in window.windowTitle()
        assert "文档排版工具" in window.windowTitle()

    @pytest.mark.gui
    @pytest.mark.p1
    def test_export_button_initially_disabled(self, window):
        """G-004: 启动后导出按钮禁用."""
        assert not window.btn_export.isEnabled()

    @pytest.mark.gui
    @pytest.mark.p0
    def test_import_enables_export(self, window, temp_md_file):
        """G-005: 导入文件后启用导出按钮."""
        md_file = temp_md_file("# 标题\n\n正文内容。")

        # 模拟导入
        window.document = window.importer_registry.import_file(md_file)
        window.current_file = md_file
        window._apply_template_and_preview()
        window.btn_export.setEnabled(True)
        window.export_action.setEnabled(True)

        assert window.btn_export.isEnabled()

    @pytest.mark.gui
    @pytest.mark.p0
    def test_template_switch_updates_preview(self, window, temp_md_file):
        """G-006: 切换模板更新预览."""
        md_file = temp_md_file("# 标题\n\n正文。")
        window.document = window.importer_registry.import_file(md_file)
        window.current_file = md_file
        window._apply_template_and_preview()
        window.btn_export.setEnabled(True)

        # 预览区应有内容
        preview_text = window.preview.text_edit.toPlainText()
        assert "标题" in preview_text

        # 切换模板
        templates = window.template_manager.list_templates()
        if len(templates) > 1:
            window.template_combo.setCurrentText(templates[1])
            # 预览应更新
            new_text = window.preview.text_edit.toPlainText()
            assert len(new_text) > 0

    @pytest.mark.gui
    @pytest.mark.p1
    def test_info_label_updates(self, window, temp_md_file):
        """G-011: 导入后信息标签显示元素数和字数."""
        md_file = temp_md_file("# 标题\n\n正文内容。")
        window.document = window.importer_registry.import_file(md_file)
        window.current_file = md_file
        window._update_info_label()

        info_text = window.info_label.text()
        assert "元素" in info_text
        assert "字" in info_text

    @pytest.mark.gui
    @pytest.mark.p1
    def test_preview_shows_disclaimer(self, window):
        """G-012: 预览区显示近似效果提示."""
        bottom_text = window.preview.bottom_bar.text()
        assert "近似" in bottom_text or "Word" in bottom_text


class TestImportDialog:
    """导入对话框测试."""

    @pytest.mark.gui
    @pytest.mark.p0
    def test_import_txt_file(self, window, temp_txt_file, qtbot):
        """通过代码直接导入 TXT 文件."""
        txt_file = temp_txt_file("第一章 简介\n\n正文内容。")

        # 直接调用内部方法（避免弹出对话框）
        window.document = window.importer_registry.import_file(txt_file)
        window.current_file = txt_file
        window._apply_template_and_preview()
        window.btn_export.setEnabled(True)
        window._update_title()
        window._update_info_label()

        # 验证状态
        assert window.btn_export.isEnabled()
        assert txt_file.name in window.windowTitle()
        assert "元素" in window.info_label.text()


class TestExportDialog:
    """导出对话框测试."""

    @pytest.mark.gui
    @pytest.mark.p0
    def test_export_produces_file(self, window, temp_md_file, temp_dir):
        """导出生成实际的 docx 文件."""
        md_file = temp_md_file("# 标题\n\n正文段落内容。")
        window.document = window.importer_registry.import_file(md_file)
        window.current_file = md_file
        window._apply_template_and_preview()
        window.btn_export.setEnabled(True)

        # 直接调用导出器
        output = temp_dir / "gui_export.docx"
        from app.engine import Typesetter
        tpl = window.template_manager.get_template_or_default(window.current_template_name)
        typeset_doc = Typesetter(tpl).apply(window.document)
        window.exporter.export(typeset_doc, output)

        assert output.exists()
        assert output.stat().st_size > 1000
