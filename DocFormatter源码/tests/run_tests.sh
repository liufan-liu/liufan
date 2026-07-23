#!/bin/bash
# DocFormatter 测试运行脚本
# 用法:
#   bash tests/run_tests.sh           # 运行全部测试
#   bash tests/run_tests.sh -m p0     # 仅运行 P0 用例
#   bash tests/run_tests.sh --html    # 生成 HTML 报告

set -e

cd "$(dirname "$0")/.."

echo "============================================================"
echo "DocFormatter 测试套件"
echo "============================================================"
echo ""

# 检查 pytest 是否安装
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "安装 pytest..."
    pip install -q pytest pytest-html
fi

# 解析参数
PYTEST_ARGS=("-v" "--tb=short")

if [[ "$1" == "-m" && -n "$2" ]]; then
    PYTEST_ARGS+=("-m" "$2")
    echo "运行标记: $2"
elif [[ "$1" == "--html" ]]; then
    PYTEST_ARGS+=("--html=tests/reports/report.html" "--self-contained-html")
    echo "生成 HTML 报告: tests/reports/report.html"
elif [[ -n "$1" ]]; then
    PYTEST_ARGS+=("$1")
fi

echo ""
echo "运行测试..."
echo "------------------------------------------------------------"

python3 -m pytest tests/ "${PYTEST_ARGS[@]}"

EXIT_CODE=$?

echo ""
echo "------------------------------------------------------------"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 全部测试通过"
else
    echo "❌ 存在失败用例"
fi
echo "============================================================"

exit $EXIT_CODE
