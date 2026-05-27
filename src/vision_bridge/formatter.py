"""输出格式化 - 将原始描述格式化为结构化文本供 DeepSeek 消费。"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .types import OutputFormat, OutputSettings


class OutputFormatter:
    """格式化视觉模型的原始输出。

    提供三种格式:
      - structured: 分段描述，最适合 LLM 下游推理
      - narrative: 自然段落形式
      - simple: 纯文本，不含元数据
    """

    def __init__(self, settings: OutputSettings):
        self.settings = settings
        self._zh_labels = {
            "overview": "概览 / Overview",
            "detail": "详细内容 / Detailed Content",
            "subjects": "主体 / Main Subjects",
            "text": "文字 / Text Content",
            "layout": "布局与结构 / Layout and Structure",
            "colors": "色彩与风格 / Colors and Style",
            "key_details": "关键细节 / Key Details",
        }

    def format(
        self,
        raw_description: str,
        provider_name: str,
        model: str,
        image_path: Path,
        elapsed_ms: float,
    ) -> str:
        """格式化单张图片的描述。

        Args:
            raw_description: 视觉模型返回的原始文本。
            provider_name: 提供者名称。
            model: 使用的模型名称。
            image_path: 图片路径。
            elapsed_ms: API 调用耗时（毫秒）。

        Returns:
            格式化后的描述文本。
        """
        lines = []

        # 简单模式：只返回原始描述
        if self.settings.format == OutputFormat.SIMPLE:
            return raw_description

        # 标题与元数据
        lines.append("=" * 60)
        lines.append("[图像描述 - Image Description]")
        lines.append("=" * 60)

        if self.settings.include_metadata:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"图片: {image_path.name}")
            lines.append(f"提供者: {provider_name} ({model})")
            lines.append(f"时间: {timestamp}")
            lines.append(f"耗时: {elapsed_ms:.0f}ms")
            lines.append("")

        if self.settings.format == OutputFormat.NARRATIVE:
            # 自然段落模式
            lines.append(raw_description)
            lines.append("")
            lines.append("=" * 60)
            return "\n".join(lines)

        # 结构化模式（默认）
        if self.settings.language == "zh":
            lines.append("请根据以下描述分析这张图片：")
        else:
            lines.append("Please analyze this image based on the following description:")
        lines.append("")

        # 尝试解析模型输出的分段结构
        # 如果原始输出已包含分段的标题，则保留原样
        structured = self._structure_description(raw_description)
        lines.append(structured)
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _structure_description(self, raw: str) -> str:
        """尝试给原始描述添加结构化标记。

        如果原始内容已经包含明显的段落/标题结构，保持原样。
        否则添加基本标注。
        """
        # 检测是否已有结构化内容（含编号或标题）
        has_structure = any(
            marker in raw
            for marker in ("1.", "###", "**", "概览", "概述", "Overview", "Summary")
        )

        if has_structure:
            # 已有结构，保持原样
            return raw

        # 没有明显结构，添加基本分段
        lines = [
            f"--- {self._zh_labels['overview']} ---",
            "",
            raw,
            "",
            "---",
        ]
        return "\n".join(lines)

    def format_batch_summary(
        self,
        results: dict[str, str],
        provider_name: str,
    ) -> str:
        """格式化批量处理的结果摘要。

        Args:
            results: {文件名: 描述文本} 的字典。
            provider_name: 提供者名称。

        Returns:
            批量摘要文本。
        """
        lines = [
            "=" * 60,
            "[批量图像描述 - Batch Image Description]",
            "=" * 60,
            f"提供者: {provider_name}",
            f"图片数量: {len(results)}",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        for i, (filename, description) in enumerate(results.items(), 1):
            lines.append(f"{'─' * 60}")
            lines.append(f"[{i}/{len(results)}] {filename}")
            lines.append(f"{'─' * 60}")
            # 截取前 500 字符作为摘要
            preview = description[:500]
            if len(description) > 500:
                preview += "..."
            lines.append(preview)
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
