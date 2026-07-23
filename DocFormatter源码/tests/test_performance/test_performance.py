"""性能压力测试 — 验证大文档和极端场景下的表现."""
import time
import pytest
import tempfile
from pathlib import Path

# 尝试导入 psutil（可选，用于内存测试）
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from app.importers.md_importer import MarkdownImporter
from app.importers.txt_importer import TxtImporter
from app.importers.docx_importer import DocxImporter
from app.templates import TemplateManager
from app.engine import Typesetter
from app.exporter import DocxExporter


def get_memory_mb():
    """获取当前进程内存（MB）."""
    if HAS_PSUTIL:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    return 0


@pytest.fixture
def perf_report():
    """性能测试报告收集器."""
    results = []
    yield results
    # 测试结束时打印报告
    if results:
        print("\n" + "=" * 70)
        print("性能测试报告")
        print("=" * 70)
        print(f"{'测试项':<40} {'耗时':>10} {'内存':>10} {'结果':>8}")
        print("-" * 70)
        for r in results:
            status = "✅" if r.get("pass", False) else "❌"
            mem = f"{r.get('memory', 0):.1f} MB" if r.get('memory') else "N/A"
            print(f"{r['name']:<40} {r['time']*1000:>8.1f} ms {mem:>10} {status:>8}")
        print("=" * 70)


def _run_perf_test(name, fn, perf_report, time_limit=5.0, memory_limit=500):
    """运行性能测试并记录结果."""
    mem_before = get_memory_mb()
    start = time.perf_counter()
    try:
        result = fn()
        elapsed = time.perf_counter() - start
        mem_after = get_memory_mb()
        mem_used = mem_after - mem_before if mem_before > 0 else 0

        passed = elapsed < time_limit and (not HAS_PSUTIL or mem_after < memory_limit)
        perf_report.append({
            "name": name,
            "time": elapsed,
            "memory": mem_used if mem_used > 0 else None,
            "pass": passed,
        })
        assert passed, f"性能不达标: 耗时 {elapsed:.2f}s, 内存 {mem_after:.1f}MB"
        return result
    except Exception as e:
        perf_report.append({
            "name": name,
            "time": time.perf_counter() - start,
            "memory": None,
            "pass": False,
        })
        raise


class TestLargeDocuments:
    """大文档性能测试."""

    @pytest.mark.slow
    @pytest.mark.p1
    def test_large_markdown_import(self, perf_report, temp_dir):
        """大型 Markdown 导入（1000 段落）."""
        # 生成大文件
        md_lines = []
        for i in range(1000):
            md_lines.append(f"## 第 {i+1} 节")
            md_lines.append(f"这是第 {i+1} 节的内容。包含**加粗**和*斜体*文字。")
            md_lines.append("")

        md_file = temp_dir / "large.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")
        file_size = md_file.stat().st_size

        def run():
            return MarkdownImporter().import_file(md_file)

        doc = _run_perf_test(
            f"大 MD 导入 ({file_size/1024:.0f}KB, 1000段)",
            run, perf_report, time_limit=10.0
        )
        assert doc.element_count() >= 1000

    @pytest.mark.slow
    @pytest.mark.p1
    def test_large_markdown_typeset(self, perf_report, temp_dir):
        """大型 Markdown 排版（1000 段落）."""
        md_lines = []
        for i in range(1000):
            md_lines.append(f"## 第 {i+1} 节\n\n内容段落。\n")
        md_file = temp_dir / "large.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")

        doc = MarkdownImporter().import_file(md_file)
        tpl = TemplateManager().get_template("通用文档")

        def run():
            return Typesetter(tpl).apply(doc)

        _run_perf_test("大 MD 排版 (1000段)", run, perf_report, time_limit=5.0)

    @pytest.mark.slow
    @pytest.mark.p1
    def test_large_markdown_export(self, perf_report, temp_dir):
        """大型 Markdown 导出（1000 段落）."""
        md_lines = []
        for i in range(1000):
            md_lines.append(f"## 第 {i+1} 节\n\n内容段落。\n")
        md_file = temp_dir / "large.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")

        doc = MarkdownImporter().import_file(md_file)
        tpl = TemplateManager().get_template("通用文档")
        doc = Typesetter(tpl).apply(doc)

        output = temp_dir / "large.docx"

        def run():
            DocxExporter().export(doc, output)

        _run_perf_test("大 MD 导出 (1000段)", run, perf_report, time_limit=10.0)
        assert output.exists()
        assert output.stat().st_size > 10000

    @pytest.mark.slow
    @pytest.mark.p1
    def test_large_table(self, perf_report, temp_dir):
        """大型表格（100 行 × 20 列）."""
        md_lines = ["| " + " | ".join(f"列{j}" for j in range(20)) + " |"]
        md_lines.append("|" + "|".join(["---"] * 20) + "|")
        for i in range(100):
            md_lines.append("| " + " | ".join(f"数据{i}-{j}" for j in range(20)) + " |")

        md_file = temp_dir / "large_table.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")

        def run():
            doc = MarkdownImporter().import_file(md_file)
            tpl = TemplateManager().get_template("通用文档")
            doc = Typesetter(tpl).apply(doc)
            output = temp_dir / "large_table.docx"
            DocxExporter().export(doc, output)
            return output

        output = _run_perf_test("大表格 (100x20)", run, perf_report, time_limit=60.0)
        assert output.exists()

    @pytest.mark.slow
    @pytest.mark.p1
    def test_many_images_placeholder(self, perf_report, temp_dir):
        """大量图片占位符（100 个）."""
        md_lines = []
        for i in range(100):
            md_lines.append(f"## 图片 {i+1}")
            md_lines.append(f"![图片{i+1}](/nonexistent/image{i+1}.png)")
            md_lines.append("")

        md_file = temp_dir / "many_images.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")

        def run():
            doc = MarkdownImporter().import_file(md_file)
            tpl = TemplateManager().get_template("通用文档")
            doc = Typesetter(tpl).apply(doc)
            output = temp_dir / "many_images.docx"
            DocxExporter().export(doc, output)
            return output

        _run_perf_test("多图片 (100个占位)", run, perf_report, time_limit=10.0)


class TestRepeatedOperations:
    """重复操作测试（检查内存泄漏）."""

    @pytest.mark.slow
    @pytest.mark.p1
    def test_repeated_import_export(self, perf_report, temp_dir):
        """重复导入/导出 50 次（检查内存泄漏）."""
        md_file = temp_dir / "test.md"
        md_file.write_text("# 标题\n\n" + "正文。\n" * 100, encoding="utf-8")

        mem_before = get_memory_mb()
        start = time.perf_counter()

        for i in range(50):
            doc = MarkdownImporter().import_file(md_file)
            tpl = TemplateManager().get_template("通用文档")
            doc = Typesetter(tpl).apply(doc)
            output = temp_dir / f"output_{i}.docx"
            DocxExporter().export(doc, output)

        elapsed = time.perf_counter() - start
        mem_after = get_memory_mb()
        mem_growth = mem_after - mem_before if mem_before > 0 else 0

        perf_report.append({
            "name": "重复导入导出 50 次",
            "time": elapsed,
            "memory": mem_growth if mem_growth > 0 else None,
            "pass": True,
        })

        # 50 次操作应该在合理时间内完成
        assert elapsed < 30.0, f"50 次操作耗时过长: {elapsed:.2f}s"

        # 内存增长应有限（允许一些增长，但不能无限）
        if HAS_PSUTIL:
            assert mem_growth < 200, f"内存增长过多: {mem_growth:.1f}MB"

    @pytest.mark.slow
    @pytest.mark.p1
    def test_repeated_template_switch(self, perf_report, temp_dir):
        """重复切换模板 100 次."""
        md_file = temp_dir / "test.md"
        md_file.write_text("# 标题\n\n正文。\n" * 50, encoding="utf-8")
        doc = MarkdownImporter().import_file(md_file)

        # 创建多个模板
        templates = []
        for i in range(5):
            templates.append({
                "name": f"模板{i}",
                "page": {"width": 210, "height": 297,
                         "margin_top": 20 + i, "margin_bottom": 20 + i,
                         "margin_left": 25 + i, "margin_right": 25 + i},
                "styles": {
                    "Normal": {
                        "run": {"font_size": 11 + i},
                        "paragraph": {"line_spacing": 1.25 + i * 0.1},
                    }
                },
            })

        start = time.perf_counter()
        for i in range(100):
            tpl = templates[i % len(templates)]
            Typesetter(tpl).apply(doc)

        elapsed = time.perf_counter() - start

        perf_report.append({
            "name": "重复切换模板 100 次",
            "time": elapsed,
            "memory": None,
            "pass": elapsed < 5.0,
        })

        assert elapsed < 5.0, f"模板切换耗时过长: {elapsed:.2f}s"


class TestStartupPerformance:
    """启动性能测试."""

    @pytest.mark.p1
    def test_template_manager_startup(self, perf_report):
        """模板管理器启动时间."""
        def run():
            return TemplateManager()

        tm = _run_perf_test("模板管理器启动", run, perf_report, time_limit=1.0)
        assert len(tm.list_templates()) >= 1

    @pytest.mark.p1
    def test_importer_registry_startup(self, perf_report):
        """导入器注册中心启动时间."""
        from app.importers.base import ImporterRegistry
        from app.importers.txt_importer import TxtImporter
        from app.importers.md_importer import MarkdownImporter
        from app.importers.docx_importer import DocxImporter

        def run():
            reg = ImporterRegistry()
            reg.register(TxtImporter())
            reg.register(MarkdownImporter())
            reg.register(DocxImporter())
            return reg

        _run_perf_test("导入器注册中心启动", run, perf_report, time_limit=1.0)
