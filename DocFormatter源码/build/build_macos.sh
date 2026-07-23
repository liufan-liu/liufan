#!/bin/bash
# DocFormatter macOS 打包脚本
# 修复了 python-docx 模板文件缺失的问题

echo "============================================================"
echo "DocFormatter macOS 打包工具"
echo "============================================================"
echo ""

# 检查虚拟环境
if [ ! -d "/tmp/build_env" ]; then
    echo "[错误] 虚拟环境不存在：/tmp/build_env"
    echo "请先运行：python3 -m venv /tmp/build_env"
    exit 1
fi

# 清理旧文件
echo "[1/4] 清理旧文件..."
rm -rf dist/DocFormatter.app
rm -rf build/

# 获取 docx 模板路径
DOCX_TEMPLATES=$(/tmp/build_env/bin/python -c "import docx; from pathlib import Path; print(Path(docx.__file__).parent / 'templates')")

echo "[2/4] docx 模板路径：$DOCX_TEMPLATES"

# 执行打包
echo "[3/4] 开始打包..."
echo ""
/tmp/build_env/bin/python -m PyInstaller \
    --name=DocFormatter \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "app/templates/builtin:app/templates/builtin" \
    --add-data "$DOCX_TEMPLATES:docx/templates" \
    --hidden-import=lxml \
    --hidden-import=lxml.etree \
    --hidden-import=markdown_it \
    --hidden-import=bs4 \
    --hidden-import=PIL \
    main.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[4/4] 打包成功！"
    echo ""
    echo "输出文件："
    ls -lh dist/DocFormatter.app

    echo ""
    echo "复制到打包发布文件夹..."
    rm -rf "/Users/mac/Documents/量化/office/打包发布/DocFormatter.app"
    cp -r dist/DocFormatter.app "/Users/mac/Documents/量化/office/打包发布/"
    xattr -cr "/Users/mac/Documents/量化/office/打包发布/DocFormatter.app"

    echo ""
    echo "✅ 完成！"
    echo "位置：/Users/mac/Documents/量化/office/打包发布/DocFormatter.app"
else
    echo ""
    echo "❌ 打包失败"
    exit 1
fi
