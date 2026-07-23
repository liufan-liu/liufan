# DocFormatter 测试计划

**版本**: 1.0
**日期**: 2026-07-22
**测试负责人**: QA Team

---

## 1. 测试概述

### 1.1 被测系统

| 项目 | 说明 |
|------|------|
| 系统名称 | DocFormatter 文档排版工具 |
| 版本 | 1.0.0 (MVP) |
| 类型 | 跨平台桌面 GUI 应用 |
| 平台 | Windows 10/11, macOS 12+ |
| 技术栈 | Python 3.9+, PySide6, python-docx |

### 1.2 测试目标

1. 验证核心功能（导入/排版/导出）的正确性
2. 验证 GUI 交互的可用性
3. 验证异常情况的容错能力
4. 验证跨平台一致性
5. 验证边界条件下的稳定性

### 1.3 测试范围

| 范围内 | 范围外 |
|--------|--------|
| TXT / Markdown 导入 | HTML / DOCX 导入（MVP 未实现） |
| 通用文档模板 | 论文/报告/公文模板（待开发） |
| 排版引擎（样式合并） | 复杂嵌套表格 |
| DOCX 导出 | PDF 导出 |
| GUI 主流程 | 主题切换、快捷键 |
| 单元测试 + 端到端测试 | 性能压测、安全测试 |

---

## 2. 测试策略

### 2.1 测试金字塔

```
        ╱╲
       ╱ E2E╲         端到端测试（少量，验证关键业务流程）
      ╱──────╲
     ╱ 集成测试 ╲      导入→排版→导出 链路测试
    ╱────────────╲
   ╱   单元测试     ╲   模型/导入器/导出器/模板（大量，覆盖细节）
  ╱──────────────────╲
```

### 2.2 测试类型

| 类型 | 数量 | 工具 |
|------|------|------|
| 单元测试 | ~60 | pytest |
| 集成测试 | ~15 | pytest |
| GUI 冒烟测试 | ~10 | pytest-qt |
| 端到端测试 | 5 | pytest + subprocess |
| 手工测试 | ~20 | 人工验证 |

### 2.3 测试环境

| 环境 | 用途 |
|------|------|
| macOS (开发机) | 开发期测试 |
| Windows 10 VM | 兼容性测试 |
| Windows 11 VM | 兼容性测试 |
| macOS (另一台) | 跨机器一致性 |

---

## 3. 测试模块与用例

### 3.1 文档模型 (test_model)

**目标**: 验证 Document 模型的数据结构和操作方法。

| 编号 | 用例名 | 前置条件 | 操作 | 预期结果 | 优先级 |
|------|--------|----------|------|----------|--------|
| M-001 | 创建空文档 | 无 | `Document()` | 所有字段为默认值，body 为空 | P0 |
| M-002 | 添加段落 | 空文档 | `add_paragraph("测试")` | body 增加 1 个 Paragraph，runs 有 1 个 Run | P0 |
| M-003 | 添加标题 | 空文档 | `add_heading("标题", 1)` | body 增加 1 个 Heading，level=H1 | P0 |
| M-004 | 提取标题 | 文档含多个标题/段落 | `get_headings()` | 只返回 Heading 元素，按顺序 | P0 |
| M-005 | 字数统计（中文） | 文档含"测试文档" | `word_count()` | 返回 4 | P1 |
| M-006 | 字数统计（英文） | 文档含"hello world" | `word_count()` | 返回 2 | P1 |
| M-007 | 字数统计（混合） | 文档含"测试 hello 文档" | `word_count()` | 返回 4（2中文+2英文） | P1 |
| M-008 | 样式合并 | RunStyle 部分字段 | `merge_with(另一个)` | 非 None 字段覆盖，None 字段保留 | P0 |
| M-009 | 段落纯文本 | Paragraph 含多个 Run | `get_text()` | 拼接所有 run 的 text | P0 |
| M-010 | 文档清空 | 含内容的文档 | `clear()` | body 为空，header/footer 为 None | P1 |
| M-011 | 表格快速创建 | 二维字符串数组 | `Table.from_data()` | rows/cols 正确，cells 补齐 | P1 |

### 3.2 导入器 (test_importers)

**目标**: 验证各类文件能被正确解析为 Document 模型。

#### 3.2.1 TXT 导入器

| 编号 | 用例名 | 输入 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| T-001 | 普通文本导入 | 多段纯文本 | 按空行分段，每段 1 个 Paragraph | P0 |
| T-002 | 中文标题识别 | "第一章 简介" | 识别为 Heading H1 | P0 |
| T-003 | 数字标题识别 | "1.1 功能特点" | 识别为 Heading H2 | P0 |
| T-004 | 全大写英文标题 | "INTRODUCTION" | 识别为 Heading H1 | P1 |
| T-005 | UTF-8 编码 | UTF-8 文件 | 正常解析 | P0 |
| T-006 | GBK 编码 | GBK 文件 | 正常解析 | P1 |
| T-007 | 带 BOM 的 UTF-8 | UTF-8 BOM 文件 | 正常解析，无乱码 | P1 |
| T-008 | 空文件 | 0 字节文件 | 抛出 ImportError | P0 |
| T-009 | 不存在文件 | 假路径 | 抛出 ImportError | P0 |
| T-010 | 多级标题混合 | 含 H1/H2/H3 文本 | 各自识别为对应 level | P0 |

#### 3.2.2 Markdown 导入器

| 编号 | 用例名 | 输入 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| MD-001 | 标题导入 | `# H1` `## H2` `### H3` | 对应 Heading H1/H2/H3 | P0 |
| MD-002 | 段落导入 | 普通文本 | Paragraph 元素 | P0 |
| MD-003 | 粗体识别 | `**bold**` | Run.style.bold=True | P0 |
| MD-004 | 斜体识别 | `*italic*` | Run.style.italic=True | P0 |
| MD-005 | 行内代码 | `` `code` `` | Run.font_name="Courier New" | P1 |
| MD-006 | 无序列表 | `- item` | DocumentList，list_type=UNORDERED | P0 |
| MD-007 | 有序列表 | `1. item` | DocumentList，list_type=ORDERED | P0 |
| MD-008 | 表格解析 | GFM 表格 | Table 元素，rows/cols 正确 | P0 |
| MD-009 | 代码块 | ````python\n...` | CodeBlock 元素，language="python" | P0 |
| MD-010 | 引用块 | `> quote` | BlockQuote 元素 | P1 |
| MD-011 | 图片 | `![alt](path.png)` | Image 元素 | P1 |
| MD-012 | 分隔线 | `---` | PageBreak 元素 | P1 |
| MD-013 | 嵌套列表 | 缩进列表 | ListItem.level 反映嵌套层级 | P2 |
| MD-014 | 复杂 Markdown | 混合所有语法 | 全部正确解析，无丢失 | P0 |

#### 3.2.3 导入器注册中心

| 编号 | 用例名 | 操作 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| R-001 | 注册导入器 | `register(TxtImporter())` | list_importers 包含它 | P0 |
| R-002 | 自动选择 | 传入 .txt 文件 | 返回 TxtImporter | P0 |
| R-003 | 不支持格式 | 传入 .pdf 文件 | 抛出 ImportError | P0 |
| R-004 | 文件过滤器字符串 | 调用 `file_filter_string()` | 包含所有支持的扩展名 | P1 |

### 3.3 模板系统 (test_templates)

| 编号 | 用例名 | 操作 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| PL-001 | 加载内置模板 | 启动 TemplateManager | 包含"通用文档" | P0 |
| PL-002 | 获取模板 | `get_template("通用文档")` | 返回完整模板字典 | P0 |
| PL-003 | 模板列表 | `list_templates()` | 非空，包含所有内置模板 | P0 |
| PL-004 | 不存在的模板 | `get_template("xxx")` | 返回 None | P1 |
| PL-005 | 获取默认模板 | `get_template_or_default(None)` | 返回"通用文档" | P0 |
| PL-006 | 获取样式规则 | `get_style_rules("通用文档", "Normal")` | 返回 run + paragraph 规则 | P0 |
| PL-007 | 添加用户模板 | YAML 字符串 | 保存到 user/ 目录，可获取 | P1 |
| PL-008 | 删除用户模板 | 删除用户添加的模板 | 模板被移除 | P1 |
| PL-009 | 不能删除内置模板 | 删除内置模板 | 抛出 TemplateError | P1 |
| PL-010 | 无效 YAML | 格式错误的 YAML | 抛出 TemplateError | P1 |
| PL-011 | 样式规则合并 | `merge_style_rules(base, override)` | override 非 None 字段覆盖 base | P0 |

### 3.4 排版引擎 (test_engine)

| 编号 | 用例名 | 操作 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| E-001 | 应用页面设置 | 排版含 page 规则的模板 | doc.page_style 被更新 | P0 |
| E-002 | 应用标题样式 | 排版含 Heading 1 规则 | 标题 run 字体为黑体 | P0 |
| E-003 | 应用段落样式 | 排版含 Normal 规则 | 段落对齐、行距、缩进正确 | P0 |
| E-004 | 首行缩进（字符） | 模板含 first_line_indent_chars=2 | 段落 style.first_line_indent_chars=2 | P0 |
| E-005 | 不覆盖已有样式 | 段落原有 bold=True，模板 bold=None | 原有 bold=True 保留 | P0 |
| E-006 | 目录域插入 | 模板启用 toc.enabled | body 首元素为 TOCField | P0 |
| E-007 | 页眉页脚 | 模板含 header/footer | doc.header/footer 不为 None | P1 |
| E-008 | 原始文档不可变 | 排版后检查原 doc | 原始 doc 未被修改 | P0 |
| E-009 | 表格样式应用 | 含 Table 的文档 | 单元格字体为模板指定值 | P1 |
| E-010 | 列表样式应用 | 含 List 的文档 | 列表项字体/缩进正确 | P1 |
| E-011 | 代码块转换 | 含 CodeBlock 的文档 | CodeBlock 转为 Paragraph | P1 |
| E-012 | TOC 生成 | 含多级标题 | TOCGenerator 输出所有标题 | P0 |

### 3.5 DOCX 导出器 (test_exporter)

| 编号 | 用例名 | 操作 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| X-001 | 导出空文档 | 空 Document | 生成有效 .docx，可在 Word 打开 | P0 |
| X-002 | 导出标题 | 含 Heading 的文档 | Word 中样式名为 Heading N，字体正确 | P0 |
| X-003 | 导出段落 | 含 Paragraph 的文档 | 对齐/行距/缩进在 Word 中正确 | P0 |
| X-004 | 导出粗体斜体 | Run 含 bold/italic | Word 中显示对应效果 | P0 |
| X-005 | 导出表格 | 含 Table 的文档 | Word 中有对应行列数的表格 | P0 |
| X-006 | 导出列表 | 含 DocumentList | Word 中使用 List Bullet / List Number 样式 | P1 |
| X-007 | 导出图片 | 含 Image 的文档（文件存在） | Word 中显示图片 | P1 |
| X-008 | 导出图片（不存在） | Image 路径不存在 | Word 中显示占位符文本 | P1 |
| X-009 | 导出分页符 | 含 PageBreak | Word 中在该位置分页 | P1 |
| X-010 | 导出目录域 | 含 TOCField | Word 中有 TOC 域代码，提示文字 | P0 |
| X-011 | 导出代码块 | 含 CodeBlock | 等宽字体，灰底 | P1 |
| X-012 | 导出引用块 | 含 BlockQuote | 缩进，楷体 | P1 |
| X-013 | 页面设置正确 | 设置页面边距 | Word 中页面设置匹配 | P0 |
| X-014 | 中文字体设置 | 设置 font_name_east_asia | Word 中 rFonts eastAsia 正确 | P0 |
| X-015 | 核心属性 | 设置 title/author | docx 属性中可见 | P1 |
| X-016 | 导出到不存在目录 | 路径含不存在的目录 | 自动创建目录 | P1 |

### 3.6 GUI 测试 (test_gui)

| 编号 | 用例名 | 操作 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| G-001 | 窗口启动 | 运行 main.py | 窗口正常显示，无报错 | P0 |
| G-002 | 窗口标题 | 启动后检查 | 显示 "DocFormatter — 文档排版工具" | P1 |
| G-003 | 导入按钮 | 点击导入，选择 .md 文件 | 预览区显示内容，状态栏更新 | P0 |
| G-004 | 导出按钮初始禁用 | 启动后检查 | 导出按钮为灰色禁用状态 | P1 |
| G-005 | 导入后启用导出 | 导入文件后 | 导出按钮变为可用 | P0 |
| G-006 | 模板切换 | 切换模板下拉框 | 预览区立即更新 | P0 |
| G-007 | 导出对话框 | 点击导出 | 弹出文件保存对话框 | P0 |
| G-008 | 导入失败提示 | 导入不支持的文件 | 弹出错误对话框 | P0 |
| G-009 | 导出成功提示 | 导出成功 | 弹出成功信息对话框 | P1 |
| G-010 | 关于对话框 | 点击帮助 → 关于 | 显示版本信息和说明 | P1 |
| G-011 | 文档信息标签 | 导入后 | 显示元素数和字数 | P1 |
| G-012 | 预览区提示 | 查看预览区底部 | 显示"预览为近似效果"提示 | P2 |

### 3.7 端到端测试 (test_e2e)

| 编号 | 用例名 | 流程 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| EE-001 | TXT 全链路 | TXT → 排版 → DOCX → 用 python-docx 读回验证 | 段落、标题样式正确 | P0 |
| EE-002 | Markdown 全链路 | MD → 排版 → DOCX → 验证 | 所有元素类型都正确导出 | P0 |
| EE-003 | 复杂 MD 全链路 | 含所有语法的 MD → DOCX | 无元素丢失 | P0 |
| EE-004 | 模板切换链路 | 导入 → 切换模板 → 导出 | 不同模板产生不同样式 | P0 |
| EE-005 | 中文排版验证 | 含中文的 MD → DOCX | Word 中打开无乱码，字体正确 | P0 |

### 3.8 异常与边界测试

| 编号 | 用例名 | 输入 | 预期结果 | 优先级 |
|------|--------|------|----------|--------|
| EX-001 | 超大文件 | 10MB 文本 | 不崩溃，内存 < 500MB | P1 |
| EX-002 | 特殊字符 | 含 emoji、特殊 Unicode | 不崩溃，正确导出 | P1 |
| EX-003 | 长单词 | 单行 > 10000 字符 | 不崩溃 | P1 |
| EX-004 | 零字节文件 | 空文件 | ImportError 友好提示 | P0 |
| EX-005 | 二进制文件 | 传入 .exe 当作 .txt | ImportError | P1 |
| EX-006 | 权限不足 | 写入只读目录 | ExportError 友好提示 | P1 |
| EX-007 | 磁盘空间不足 | 导出到已满磁盘 | ExportError 友好提示 | P2 |
| EX-008 | 非法路径 | 导出到 /xxx/yyy | 错误处理 | P1 |
| EX-009 | 模板 YAML 损坏 | 损坏的 YAML 文件 | 跳过该模板，不影响其他 | P1 |
| EX-010 | 重复样式字段 | 模板含未知样式字段 | 忽略未知字段 | P2 |
| EX-011 | 中文路径 | 导入/导出含中文路径 | 正常工作 | P1 |
| EX-012 | 超长文件名 | 100+ 字符文件名 | 不崩溃 | P2 |

---

## 4. 测试数据（Fixtures）

### 4.1 输入文件 (`tests/fixtures/inputs/`)

| 文件 | 用途 |
|------|------|
| `simple.txt` | 纯文本，3 段 |
| `with_headings.txt` | 含多种标题格式 |
| `utf8.txt` | UTF-8 编码中文 |
| `gbk.txt` | GBK 编码中文 |
| `empty.txt` | 空文件（0 字节） |
| `simple.md` | 基础 Markdown |
| `all_syntax.md` | 包含所有 Markdown 语法 |
| `chinese.md` | 中文内容 Markdown |
| `large.md` | 大型 Markdown（100+ 段落） |
| `nested_lists.md` | 嵌套列表 |
| `complex_table.md` | 复杂表格（合并单元格） |

### 4.2 期望输出 (`tests/fixtures/expected/`)

| 文件 | 用途 |
|------|------|
| `simple_typeset.docx` | simple.md 排版后的期望输出 |
| `template_rules.json` | 模板规则解析后的期望结果 |

### 4.3 模板 (`tests/fixtures/templates/`)

| 文件 | 用途 |
|------|------|
| `test_template.yaml` | 测试用模板（极简） |
| `invalid.yaml` | 格式错误的 YAML |
| `no_name.yaml` | 缺少 name 字段的 YAML |

---

## 5. 测试执行

### 5.1 执行命令

```bash
# 运行全部测试
cd docformatter
python -m pytest tests/ -v

# 运行指定模块
python -m pytest tests/test_model/ -v
python -m pytest tests/test_importers/ -v
python -m pytest tests/test_e2e/ -v

# 仅运行 P0 用例
python -m pytest tests/ -v -m p0

# 生成 HTML 报告
python -m pytest tests/ --html=tests/reports/report.html

# 运行 GUI 测试（需要显示器）
python -m pytest tests/test_gui/ -v --headed
```

### 5.2 测试命名规范

```
test_<模块>_<功能>_<场景>.py

示例:
test_document_creation.py
test_txt_importer_headings.py
test_typesetter_style_merge.py
test_docx_exporter_tables.py
```

### 5.3 测试标记（Markers）

```python
@pytest.mark.p0      # 最高优先级，必须通过
@pytest.mark.p1      # 高优先级
@pytest.mark.p2      # 中优先级
@pytest.mark.slow    # 耗时测试
@pytest.mark.gui     # GUI 测试（需要显示器）
@pytest.mark.xplatform  # 跨平台测试
```

---

## 6. 缺陷管理

### 6.1 严重等级

| 等级 | 定义 | 示例 |
|------|------|------|
| S1 阻塞 | 系统崩溃/无法启动 | 启动报错、导入必崩 |
| S2 严重 | 核心功能不可用 | 导出失败、样式全丢 |
| S3 一般 | 功能部分异常 | 某种标题识别错误 |
| S4 轻微 | 界面/提示问题 | 文案错误、对齐偏差 |

### 6.2 缺陷报告模板

```markdown
**标题**: [模块] 简短描述
**严重度**: S1 / S2 / S3 / S4
**优先级**: P0 / P1 / P2
**环境**: macOS 14 / Windows 11
**复现步骤**:
1. ...
2. ...
**实际结果**: ...
**预期结果**: ...
**附件**: 截图 / 测试文件
```

---

## 7. 测试通过标准

### 7.1 MVP 发布标准

- [ ] 所有 P0 用例 100% 通过
- [ ] 所有 P1 用例 95% 以上通过
- [ ] S1 / S2 缺陷全部关闭
- [ ] S3 缺陷关闭率 ≥ 80%
- [ ] 端到端测试全部通过
- [ ] Windows + macOS 双平台验证通过

### 7.2 完整发布标准

- [ ] 所有 P0/P1 用例 100% 通过
- [ ] P2 用例 90% 以上通过
- [ ] 所有 S1/S2/S3 缺陷关闭
- [ ] 性能测试达标（10MB 文件不卡顿）
- [ ] 兼容性测试（Win10/11, macOS 12+）通过

---

## 8. 测试自动化规划

### 8.1 自动化覆盖目标

| 模块 | 自动化率 | 说明 |
|------|---------|------|
| 文档模型 | 100% | 纯数据类，易测 |
| 导入器 | 95% | 文本处理，易测 |
| 模板系统 | 90% | 文件操作，易测 |
| 排版引擎 | 90% | 逻辑处理，易测 |
| 导出器 | 85% | 需要读回 docx 验证 |
| GUI | 60% | 需要 pytest-qt，交互复杂 |
| 端到端 | 100% | 关键业务路径 |

### 8.2 CI/CD 集成（未来）

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ['3.9', '3.10', '3.11', '3.12']
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-html pytest-qt
      - run: pytest tests/ -v --html=report.html --ignore=tests/test_gui
```
