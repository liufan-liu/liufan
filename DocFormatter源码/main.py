"""DocFormatter 应用入口."""
import sys
import os
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _fix_docx_frozen_paths():
    """ponytail: python-docx 用 __file__ 找 templates/，PyInstaller 下 parts/ 等
    目录不存在（.pyc 在 PYZ 里），导致 parts/../templates/ 解析失败。
    在 _MEIPASS 下创建空壳目录绕过 POSIX 路径遍历检查。"""
    if not getattr(sys, 'frozen', False):
        return
    meipass = Path(sys._MEIPASS)
    docx_dir = meipass / "docx"
    for sub in ("parts", "opc", "oxml"):
        (docx_dir / sub).mkdir(exist_ok=True)


def main():
    """应用主入口."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont

    # PyInstaller frozen 模式下修复 python-docx 模板路径
    _fix_docx_frozen_paths()

    # 高 DPI 支持
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("DocFormatter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DocFormatter")

    # 设置默认字体
    font = QFont()
    font.setFamily("Microsoft YaHei, PingFang SC, Helvetica Neue, Arial, sans-serif")
    font.setPointSize(10)
    app.setFont(font)

    # 设置全局样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QMenuBar {
            background-color: #ffffff;
            border-bottom: 1px solid #ddd;
        }
        QMenuBar::item:selected {
            background-color: #e8e8e8;
        }
        QMenu {
            background-color: #ffffff;
            border: 1px solid #ccc;
        }
        QMenu::item:selected {
            background-color: #4a90e2;
            color: white;
        }
        QStatusBar {
            background-color: #f8f8f8;
            border-top: 1px solid #ddd;
            color: #555;
        }
        QComboBox {
            padding: 4px 8px;
            border: 1px solid #ccc;
            border-radius: 3px;
            background-color: white;
        }
        QComboBox:hover {
            border-color: #4a90e2;
        }
        QLabel {
            color: #333;
        }
    """)

    from app.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
