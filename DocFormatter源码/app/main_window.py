"""主窗口 — DocFormatter 应用的核心界面.

布局:
- 顶部：工具栏（导入/导出/模板选择）
- 中间：预览区（QTextEdit 模拟 A4 页面）
- 底部：状态栏
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFileDialog,
    QMessageBox, QApplication, QSplitter, QLabel, QComboBox,
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QAction, QFont

from app.importers.base import ImporterRegistry, ImportError
from app.importers.txt_importer import TxtImporter
from app.importers.md_importer import MarkdownImporter
from app.importers.docx_importer import DocxImporter
from app.engine import Typesetter
from app.exporter import DocxExporter, ExportError
from app.templates import TemplateManager
from app.model.document import Document
from app.gui.preview_area import PreviewArea


class MainWindow(QMainWindow):
    """DocFormatter 主窗口."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocFormatter — 文档排版工具")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        # 核心组件
        self.document: Document = Document()
        self.current_file: Path = None
        self.importer_registry = ImporterRegistry()
        self.template_manager = TemplateManager()
        self.current_template_name: str = "通用文档"
        self.exporter = DocxExporter()

        # 注册导入器
        self.importer_registry.register(TxtImporter())
        self.importer_registry.register(MarkdownImporter())
        self.importer_registry.register(DocxImporter())

        self._setup_ui()
        self._setup_menus()
        self._update_title()

    def _setup_ui(self) -> None:
        """搭建界面."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # --- 顶部工具栏 ---
        toolbar_widget = QWidget()
        toolbar_layout = QVBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(4)

        # 第一行：按钮
        btn_row = QWidget()
        btn_layout = QVBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # 按钮行
        from PySide6.QtWidgets import QHBoxLayout
        btn_hlayout = QHBoxLayout()
        btn_hlayout.setSpacing(8)

        self.btn_import = QPushButton_styled("📂 导入文件")
        self.btn_import.clicked.connect(self._on_import)
        btn_hlayout.addWidget(self.btn_import)

        self.btn_export = QPushButton_styled("💾 导出 DOCX")
        self.btn_export.clicked.connect(self._on_export)
        self.btn_export.setEnabled(False)
        btn_hlayout.addWidget(self.btn_export)

        btn_hlayout.addSpacing(20)

        # 模板选择
        btn_hlayout.addWidget(QLabel("样式模板:"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(180)
        self._refresh_template_combo()
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        btn_hlayout.addWidget(self.template_combo)

        btn_hlayout.addStretch()

        # 文档信息
        self.info_label = QLabel("未加载文档")
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        btn_hlayout.addWidget(self.info_label)

        btn_layout.addLayout(btn_hlayout)
        toolbar_layout.addWidget(btn_row)
        layout.addWidget(toolbar_widget)

        # --- 中间预览区 ---
        self.preview = PreviewArea()
        layout.addWidget(self.preview, stretch=1)

        # --- 底部状态栏 ---
        self.statusBar().showMessage("就绪 — 请导入文件开始排版")

    def _setup_menus(self) -> None:
        """搭建菜单栏."""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        import_action = QAction("导入文件(&I)...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._on_import)
        file_menu.addAction(import_action)

        export_action = QAction("导出 DOCX(&E)...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export)
        self.export_action = export_action
        file_menu.addAction(export_action)
        export_action.setEnabled(False)

        file_menu.addSeparator()

        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _refresh_template_combo(self) -> None:
        """刷新模板下拉框."""
        self.template_combo.clear()
        templates = self.template_manager.list_templates()
        self.template_combo.addItems(templates)
        if self.current_template_name in templates:
            self.template_combo.setCurrentText(self.current_template_name)

    # ---- 事件处理 ----

    def _on_import(self) -> None:
        """导入文件."""
        file_filter = self.importer_registry.file_filter_string()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入文档", "", file_filter
        )
        if not file_path:
            return

        try:
            path = Path(file_path)
            self.document = self.importer_registry.import_file(path)
            self.current_file = path
            self._apply_template_and_preview()
            self.btn_export.setEnabled(True)
            self.export_action.setEnabled(True)
            self._update_title()
            self._update_info_label()
            self.statusBar().showMessage(f"已导入: {path.name}  ({self.document.element_count()} 个元素)")
        except ImportError as e:
            QMessageBox.critical(self, "导入失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"未知错误: {e}")

    def _on_export(self) -> None:
        """导出 DOCX."""
        if self.document.element_count() == 0:
            QMessageBox.warning(self, "导出失败", "文档为空，请先导入文件")
            return

        default_name = ""
        if self.current_file:
            default_name = self.current_file.stem + "_排版稿.docx"
        else:
            default_name = "output.docx"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 DOCX", default_name, "Word 文档 (*.docx)"
        )
        if not file_path:
            return

        try:
            # 应用模板并导出
            tpl = self.template_manager.get_template_or_default(self.current_template_name)
            typesetter = Typesetter(tpl)
            typeset_doc = typesetter.apply(self.document)

            output_path = Path(file_path)
            self.exporter.export(typeset_doc, output_path)
            self.statusBar().showMessage(f"已导出: {output_path.name}  ({output_path.stat().st_size:,} 字节)")

            # 导出成功提示
            path_str = str(output_path)
            msg = (
                "文件已保存到:\n" + path_str + "\n\n"
                "建议在 Word 或 WPS 中打开确认最终效果。\n"
                '如包含目录，请在 Word 中右键目录选择"更新域"生成。'
            )
            QMessageBox.information(self, "导出成功", msg)
        except ExportError as e:
            QMessageBox.critical(self, "导出失败", str(e))
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"未知错误: {e}")

    def _on_template_changed(self, template_name: str) -> None:
        """切换模板."""
        self.current_template_name = template_name
        if self.document.element_count() > 0:
            self._apply_template_and_preview()
            self.statusBar().showMessage(f"已切换模板: {template_name}")

    def _apply_template_and_preview(self) -> None:
        """应用当前模板并刷新预览."""
        tpl = self.template_manager.get_template_or_default(self.current_template_name)
        typesetter = Typesetter(tpl)
        typeset_doc = typesetter.apply(self.document)
        self.preview.set_document(typeset_doc)

    def _update_title(self) -> None:
        """更新窗口标题."""
        if self.current_file:
            self.setWindowTitle(f"DocFormatter — {self.current_file.name}")
        else:
            self.setWindowTitle("DocFormatter — 文档排版工具")

    def _update_info_label(self) -> None:
        """更新文档信息标签."""
        wc = self.document.word_count()
        ec = self.document.element_count()
        self.info_label.setText(f"{ec} 个元素 · 约 {wc} 字")

    def _show_about(self) -> None:
        """显示关于对话框."""
        QMessageBox.about(
            self, "关于 DocFormatter",
            "<h2>DocFormatter v1.0</h2>"
            "<p>跨平台文档排版工具</p>"
            "<p>支持导入 TXT / Markdown / HTML / DOCX，"
            "一键套用样式模板，导出为精美 Word 文档。</p>"
            "<p>技术栈：Python + PySide6 + python-docx</p>"
            "<hr>"
            "<p><b>提示</b>：本工具为排版生成器，最终效果以 Word 打开为准。</p>"
        )


def QPushButton_styled(text: str):
    """创建带样式的按钮."""
    from PySide6.QtWidgets import QPushButton
    btn = QPushButton(text)
    btn.setMinimumHeight(32)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #4a90e2;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #357abd;
        }
        QPushButton:pressed {
            background-color: #2a5f9e;
        }
        QPushButton:disabled {
            background-color: #cccccc;
        }
    """)
    return btn
