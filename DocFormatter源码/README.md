# DocFormatter - 快速开始

## 🚀 自动打包（推荐）

本项目已配置 GitHub Actions，自动打包 Windows 和 macOS 版本。

### 首次使用

1. **创建 GitHub 仓库**
   - 访问 https://github.com/new
   - 创建名为 `DocFormatter` 的仓库

2. **推送代码**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/你的用户名/DocFormatter.git
   git push -u origin main
   ```

3. **创建版本标签**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. **等待自动打包**
   - 访问仓库的 "Actions" 页面
   - 等待 5-10 分钟
   - 打包完成后在 "Releases" 页面下载

### 手动触发

1. 访问仓库 Actions 页面
2. 点击 "Run workflow"
3. 选择分支
4. 点击 "Run workflow"

## 📦 本地打包

### macOS

```bash
cd docformatter
python3 -m venv build_env
source build_env/bin/activate
pip install -r requirements.txt
pip install pyinstaller
python build/build_app.py
```

输出：`dist/DocFormatter.app`

### Windows

```cmd
cd docformatter
build\build_windows.bat
```

输出：`dist\DocFormatter.exe`

##  文件结构

```
docformatter/
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions 配置
├── app/                       # 应用代码
│   ├── main_window.py
│   ├── gui/
│   ├── model/
│   ├── importers/
│   ├── engine/
│   ├── exporter/
│   └── templates/
├── build/
│   ├── build_app.py           # macOS 打包脚本
│   ├── build_windows.bat      # Windows 打包脚本
│   └── Windows 打包指南.md
├── dist/                      # 打包输出（自动生成）
├── main.py                    # 应用入口
├── requirements.txt           # 依赖列表
└── README.md                  # 本文件
```

## 📋 功能特性

- **多格式导入**：TXT、Markdown、HTML、DOCX
- **样式模板**：通用、论文、报告、公文
- **智能排版**：自动识别标题、清理格式
- **DOCX 导出**：完整样式、表格、图片
- **跨平台**：Windows + macOS

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

##  许可证

MIT License
