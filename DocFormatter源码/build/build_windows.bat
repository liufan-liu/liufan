@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   DocFormatter Windows 打包工具
echo ============================================================
echo.

REM --- 检测 Python ---
set PYTHON=
for %%p in (python python3 py) do (
    %%p --version >nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON=%%p
        echo [√] 检测到 Python: %%p
        %%p --version
    )
)
if "%PYTHON%"=="" (
    echo [X] 未检测到 Python，请安装 Python 3.9+
    echo     下载地址：https://www.python.org/downloads/
    echo     安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

REM --- 检查和创建虚拟环境 ---
echo.
echo [1/4] 准备虚拟环境...
if not exist "build_env\Scripts\python.exe" (
    echo   正在创建虚拟环境...
    %PYTHON% -m venv build_env
    if errorlevel 1 (
        echo [X] 创建虚拟环境失败
        pause
        exit /b 1
    )
) else (
    echo   [√] 虚拟环境已存在
)

REM --- 激活虚拟环境 ---
call build_env\Scripts\activate.bat
if errorlevel 1 (
    echo [X] 激活虚拟环境失败
    pause
    exit /b 1
)

REM --- 安装依赖 ---
echo.
echo [2/4] 安装依赖包（可能需要几分钟）...
python -m pip install --upgrade pip -q
python -m pip install PySide6 python-docx markdown-it-py mdit-py-plugins beautifulsoup4 lxml PyYAML Pillow pyinstaller
if errorlevel 1 (
    echo [X] 安装依赖失败，请检查网络连接
    pause
    exit /b 1
)
echo   [√] 依赖安装完成

REM --- 清理旧文件 ---
echo.
echo [3/4] 清理旧文件...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
del /q DocFormatter.spec 2>nul
echo   [√] 清理完成

REM --- 打包 ---
echo.
echo [4/4] 开始打包（需要 5-10 分钟，请耐心等待）...
echo.

pyinstaller --name=DocFormatter --windowed --onefile --noconfirm --clean --add-data "app/templates/builtin;app/templates/builtin" --collect-data docx --hidden-import=lxml --hidden-import=lxml.etree --hidden-import=lxml._elementpath --hidden-import=markdown_it --hidden-import=mdit_py_plugins --hidden-import=bs4 --hidden-import=PIL main.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo   [X] 打包失败！
    echo ============================================================
    echo.
    echo 请截图上面的错误信息，发给开发者排查。
    echo 常见问题：
    echo   1. 杀毒软件拦截了 PyInstaller → 暂时关闭杀毒软件重试
    echo   2. 路径包含中文/空格 → 把文件夹移到 C:\DocFormatter 重试
    echo   3. 磁盘空间不足 → 至少需要 2GB 空闲空间
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   [√] 打包成功！
echo ============================================================
echo.
echo 生成的文件：
dir dist\DocFormatter.exe 2>nul
echo.
echo 双击 dist\DocFormatter.exe 即可运行。
echo ============================================================
pause
