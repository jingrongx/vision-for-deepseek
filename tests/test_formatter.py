"""输出格式化测试。"""

from pathlib import Path

import pytest

from vision_bridge.formatter import OutputFormatter
from vision_bridge.types import OutputFormat, OutputSettings


class TestOutputFormatter:
    """测试输出格式化器。"""

    @pytest.fixture
    def raw_description(self):
        return "图片中有一只猫坐在窗台上，背景是蓝天白云。"

    @pytest.fixture
    def formatter_structured(self):
        settings = OutputSettings(
            format=OutputFormat.STRUCTURED,
            language="zh",
            include_metadata=True,
        )
        return OutputFormatter(settings)

    @pytest.fixture
    def formatter_narrative(self):
        settings = OutputSettings(
            format=OutputFormat.NARRATIVE,
            language="zh",
            include_metadata=True,
        )
        return OutputFormatter(settings)

    @pytest.fixture
    def formatter_simple(self):
        settings = OutputSettings(
            format=OutputFormat.SIMPLE,
            language="zh",
            include_metadata=False,
        )
        return OutputFormatter(settings)

    def test_structured_format(self, formatter_structured, raw_description):
        result = formatter_structured.format(
            raw_description=raw_description,
            provider_name="doubao",
            model="doubao-seed-2-0-mini-260428",
            image_path=Path("test.png"),
            elapsed_ms=1234.5,
        )
        assert "图像描述" in result
        assert "doubao" in result
        assert "doubao-seed-2-0-mini-260428" in result
        assert "test.png" in result
        assert "猫坐在窗台上" in result

    def test_narrative_format(self, formatter_narrative, raw_description):
        result = formatter_narrative.format(
            raw_description=raw_description,
            provider_name="qwen",
            model="qwen-vl-plus",
            image_path=Path("test.png"),
            elapsed_ms=500.0,
        )
        assert "图像描述" in result
        assert "猫坐在窗台上" in result

    def test_simple_format(self, formatter_simple, raw_description):
        result = formatter_simple.format(
            raw_description=raw_description,
            provider_name="claude",
            model="claude-opus-4-5-20251101",
            image_path=Path("test.png"),
            elapsed_ms=100.0,
        )
        # 简单模式直接返回原始内容
        assert result == raw_description

    def test_no_metadata(self, raw_description):
        settings = OutputSettings(
            format=OutputFormat.STRUCTURED,
            language="zh",
            include_metadata=False,
        )
        formatter = OutputFormatter(settings)
        result = formatter.format(
            raw_description=raw_description,
            provider_name="doubao",
            model="doubao-seed-2-0-mini-260428",
            image_path=Path("test.png"),
            elapsed_ms=1234.5,
        )
        assert "提供者" not in result
        assert "猫坐在窗台上" in result

    def test_structured_description_preserved(self, formatter_structured):
        """已有结构的描述应保持原样。"""
        structured_raw = "### 概览\n图片包含一个红色方块。\n### 细节\n方块位于中央。"
        result = formatter_structured.format(
            raw_description=structured_raw,
            provider_name="doubao",
            model="doubao-seed-2-0-mini-260428",
            image_path=Path("test.png"),
            elapsed_ms=100.0,
        )
        # 原始结构化内容保持不变
        assert "### 概览" in result
        assert "红色方块" in result

    def test_batch_summary(self, formatter_structured):
        results = {
            "img1.png": "第一张图片的描述。",
            "img2.png": "第二张图片的描述。",
        }
        summary = formatter_structured.format_batch_summary(results, "doubao")
        assert "批量图像描述" in summary
        assert "doubao" in summary
        assert "img1.png" in summary
        assert "img2.png" in summary
        assert "2" in summary  # 数量
