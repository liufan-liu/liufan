# DocFormatter Windows 打包指南

## 📋 系统要求

### 打包环境（开发者）
- Windows 10/11
- Python 3.9 或更高版本
- 网络连接（下载依赖包）

### 运行环境（用户）
- Windows 10/11 (64 位)
- 不需要安装 Python

##  快速打包（一键脚本）

### 步骤 1：准备项目

将完整的 `docformatter` 文件夹复制到 Windows 电脑。

### 步骤 2：运行打包脚本

1. 打开 `docformatter\build` 文件夹
2. 双击运行 `build_windows.bat`
3. 等待 5-10 分钟（首次需要下载依赖）
4. 打包完成后，exe 文件在 `dist\DocFormatter.exe`

### 步骤 3：测试运行

```cmd
cd docformatter
dist\DocFormatter.exe
```

## 🔧 手动打包（进阶）

如果一键脚本失败，可以手动执行：

### 1. 安装 Python

从官网下载：https://www.python.org/downloads/

安装时勾选：
- ✅ Add Python to PATH
- ✅ Install pip

### 2. 打开命令提示符

```cmd
# 进入项目目录
cd C:\Users\你的用户名\Documents\docformatter
```

### 3. 创建虚拟环境

```cmd
python -m venv build_env
build_env\Scripts\activate
```

### 4. 安装依赖

```cmd
pip install PySide6 python-docx markdown-it-py mdit-py-plugins beautifulsoup4 lxml PyYAML Pillow
pip install pyinstaller
```

### 5. 执行打包

```cmd
pyinstaller --name=DocFormatter --windowed --onefile --noconfirm --clean --add-data "app/templates/builtin;app/templates/builtin" --hidden-import=lxml --hidden-import=lxml.etree --hidden-import=markdown_it --hidden-import=bs4 --hidden-import=PIL main.py
```

### 6. 完成

打包完成后，exe 文件位于：
```
dist\DocFormatter.exe
```

## 📦 打包选项说明

### 单文件模式（推荐）
```cmd
--onefile
```
- 生成单个 exe 文件
- 优点：分发方便
- 缺点：首次启动慢（需要解压到临时目录）

### 目录模式
```cmd
--onedir
```
- 生成包含所有文件的文件夹
- 优点：启动快
- 缺点：文件多，需要压缩后分发

### 控制台模式（调试用）
```cmd
--console
```
- 显示控制台窗口，可以看到错误信息
- 用于调试打包问题

### 添加图标
```cmd
--icon=resources\icons\app.ico
```
- 需要准备 .ico 格式的图标文件

##  常见问题

### 问题 1：打包时报错 "ModuleNotFoundError"

**原因**：缺少隐藏导入

**解决**：添加更多 `--hidden-import` 参数：
```cmd
--hidden-import=模块名
```

### 问题 2：运行 exe 提示 "Failed to execute script"

**原因**：缺少数据文件或依赖

**解决**：
1. 使用 `--console` 模式重新打包，查看具体错误
2. 确保 `--add-data` 参数正确

### 问题 3：exe 文件过大（>100MB）

**原因**：包含了不必要的库

**解决**：
1. 使用虚拟环境，只安装必要依赖
2. 使用 UPX 压缩：
   ```cmd
   upx dist\DocFormatter.exe
   ```

### 问题 4：杀毒软件误报

**原因**：PyInstaller 打包的 exe 可能被误判

**解决**：
1. 添加白名单
2. 使用代码签名证书
3. 上传到 VirusTotal 确认是误报

### 问题 5：中文路径问题

**原因**：PyInstaller 对中文路径支持不佳

**解决**：
1. 将项目放在纯英文路径下
2. 如：`C:\projects\docformatter\`

## 📝 创建安装程序（可选）

使用 **Inno Setup** 创建专业的安装程序：

### 1. 下载 Inno Setup
https://jrsoftware.org/isdl.php

### 2. 创建脚本 `setup.iss`

```ini
[Setup]
AppName=DocFormatter
AppVersion=1.0.0
DefaultDirName={pf}\DocFormatter
OutputBaseFilename=DocFormatter_Setup

[Files]
Source: "dist\DocFormatter.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{commondesktop}\DocFormatter"; Filename: "{app}\DocFormatter.exe"
```

### 3. 编译安装程序

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
```

输出：`Output\DocFormatter_Setup.exe`

## 🎯 分发建议

### 方式 1：直接分发 exe
- 压缩：`DocFormatter.zip`
- 大小：约 50-100MB
- 适合：内部使用、小范围分发

### 方式 2：安装程序
- 使用 Inno Setup 或 NSIS
- 可以创建桌面快捷方式
- 适合：正式发行

### 方式 3：微软商店
- 需要开发者账号
- 适合：商业发布

## 📊 打包后检查清单

- [ ] exe 文件能正常启动
- [ ] 导入 TXT 文件正常
- [ ] 导入 Markdown 文件正常
- [ ] 导入 DOCX 文件正常
- [ ] 导出 DOCX 文件正常
- [ ] 模板切换正常
- [ ] 预览显示正常
- [ ] 中文字体显示正常
- [ ] 表格、列表显示正常

## 🔗 相关资源

- PyInstaller 文档：https://pyinstaller.org/
- PySide6 文档：https://doc.qt.io/qtforpython/
- Inno Setup：https://jrsoftware.org/isinfo.php
- NSIS：https://nsis.sourceforge.io/

---

**版本**: 1.0.0  
**更新日期**: 2026-07-22  
**适用系统**: Windows 10/11 (64 位)
