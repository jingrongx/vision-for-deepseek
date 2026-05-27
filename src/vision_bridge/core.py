"""核心编排器 - VisionBridge 主类。

协调配置、提供者、格式化三者，提供统一的外部接口。
"""

import time
from pathlib import Path
from typing import Any, Optional

from .config import load_config, AppConfig
from .exceptions import ConfigError, ProviderNotAvailableError
from .formatter import OutputFormatter
from .providers import get_provider, list_providers
from .providers.base import VisionProvider

# 在模块加载时注册所有内置提供者
def _register_builtin_providers():
    """注册所有内置提供者。"""
    from .providers.doubao import DoubaoVisionProvider
    from .providers.qwen import QwenVisionProvider
    from .providers.claude import ClaudeVisionProvider
    from .providers.openai import OpenAIVisionProvider
    from .providers.ollama import OllamaVisionProvider

    from .providers import register_provider

    register_provider("doubao", DoubaoVisionProvider)
    register_provider("qwen", QwenVisionProvider)
    register_provider("claude", ClaudeVisionProvider)
    register_provider("openai", OpenAIVisionProvider)
    register_provider("ollama", OllamaVisionProvider)


_register_builtin_providers()


class VisionBridge:
    """视觉桥接核心类。

    整合配置读取、提供者选择、图片描述、格式化输出的完整流程。

    用法:
        bridge = VisionBridge()
        description = bridge.describe("photo.jpg")
        print(description)

        # 指定提供者
        description = bridge.describe("photo.jpg", provider="qwen")

        # 批量处理
        results = bridge.describe_batch("./images/")
    """

    def __init__(self, config_path: Optional[str | Path] = None):
        """初始化 VisionBridge。

        Args:
            config_path: 配置文件路径，为 None 时自动查找。
        """
        self.config = load_config(config_path)
        self.formatter = OutputFormatter(self.config.output)

    def describe(
        self,
        image_path: str | Path,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        output_format: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """描述单张图片。

        Args:
            image_path: 图片文件路径。
            provider: 提供者名称，为 None 使用默认提供者。
            model: 模型名称，为 None 使用配置中的默认模型。
            prompt: 自定义提示词。
            output_format: 输出格式 (structured/narrative/simple)。
            language: 输出语言 (zh/en)。

        Returns:
            格式化后的图片描述文本。
        """
        image_path = Path(image_path)

        # 选择提供者
        provider_name = provider or self.config.default_provider
        provider_config = self.config.providers.get(provider_name)
        if provider_config is None:
            available = ", ".join(self.config.providers.keys())
            raise ProviderNotAvailableError(
                f"提供者 '{provider_name}' 未在配置中找到。可用提供者: {available}"
            )

        # 覆盖模型
        if model:
            provider_config = provider_config.__class__(**{
                **provider_config.__dict__,
                "model": model,
            })

        # 创建提供者实例
        provider_cls = get_provider(provider_name)
        vision_provider: VisionProvider = provider_cls(provider_config)

        # 覆盖输出格式
        if output_format or language:
            from .types import OutputFormat, OutputSettings
            fmt = OutputFormat(output_format) if output_format else self.config.output.format
            lang = language or self.config.output.language
            formatter = OutputFormatter(OutputSettings(
                format=fmt,
                language=lang,
                include_metadata=self.config.output.include_metadata,
            ))
        else:
            formatter = self.formatter

        # 调用 API
        start_time = time.time()
        raw_description = vision_provider.describe_image(image_path, prompt)
        elapsed_ms = (time.time() - start_time) * 1000

        # 格式化输出
        return formatter.format(
            raw_description=raw_description,
            provider_name=provider_name,
            model=provider_config.model,
            image_path=image_path,
            elapsed_ms=elapsed_ms,
        )

    def compare(
        self,
        image_paths: list[str | Path],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        output_format: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """对比分析多张图片（单次 API 调用）。

        Args:
            image_paths: 多张图片的路径列表。
            provider: 提供者名称，为 None 使用默认提供者。
            model: 模型名称，为 None 使用配置中的默认模型。
            prompt: 自定义提示词。
            output_format: 输出格式。
            language: 输出语言。

        Returns:
            格式化后的多图对比描述文本。
        """
        if len(image_paths) < 2:
            raise ValueError("至少需要 2 张图片进行对比")

        image_paths = [Path(p) for p in image_paths]

        provider_name = provider or self.config.default_provider
        provider_config = self.config.providers.get(provider_name)
        if provider_config is None:
            available = ", ".join(self.config.providers.keys())
            raise ProviderNotAvailableError(
                f"提供者 '{provider_name}' 未在配置中找到。可用提供者: {available}"
            )

        if model:
            provider_config = provider_config.__class__(**{
                **provider_config.__dict__,
                "model": model,
            })

        provider_cls = get_provider(provider_name)
        vision_provider: VisionProvider = provider_cls(provider_config)

        if output_format or language:
            from .types import OutputFormat, OutputSettings
            fmt = OutputFormat(output_format) if output_format else self.config.output.format
            lang = language or self.config.output.language
            formatter = OutputFormatter(OutputSettings(
                format=fmt,
                language=lang,
                include_metadata=self.config.output.include_metadata,
            ))
        else:
            formatter = self.formatter

        start_time = time.time()
        raw_description = vision_provider.describe_images(image_paths, prompt)
        elapsed_ms = (time.time() - start_time) * 1000

        filenames = ", ".join(p.name for p in image_paths)
        return formatter.format(
            raw_description=raw_description,
            provider_name=provider_name,
            model=provider_config.model,
            image_path=Path(filenames),
            elapsed_ms=elapsed_ms,
        )

    def describe_batch(
        self,
        directory: str | Path,
        provider: Optional[str] = None,
        output_format: Optional[str] = None,
        output_dir: Optional[str | Path] = None,
    ) -> dict[str, str]:
        """批量描述目录中的所有图片。

        Args:
            directory: 包含图片的目录路径。
            provider: 提供者名称。
            output_format: 输出格式。
            output_dir: 可选，将每个描述保存为 .txt 文件的目录。

        Returns:
            {文件名: 描述文本} 的字典。
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"目录不存在: {directory}")

        # 收集图片文件
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
        image_files = sorted([
            f for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ])

        if not image_files:
            raise ValueError(f"目录中没有找到图片文件: {directory}")

        results: dict[str, str] = {}
        provider_name = provider or self.config.default_provider

        for img_file in image_files:
            try:
                description = self.describe(
                    image_path=img_file,
                    provider=provider,
                    output_format=output_format,
                )
                results[img_file.name] = description

                # 保存到文件
                if output_dir:
                    out_path = Path(output_dir) / f"{img_file.stem}.txt"
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(description, encoding="utf-8")

            except Exception as e:
                # 单个文件失败不中断批量处理
                results[img_file.name] = f"[错误] {e}"

        return results

    def get_provider_info(self) -> dict[str, dict[str, Any]]:
        """获取所有已配置提供者的信息。

        Returns:
            {提供者名称: {model, configured, ...}}
        """
        info = {}
        for name, provider_config in self.config.providers.items():
            is_default = name == self.config.default_provider
            has_key = bool(provider_config.api_key and "your-" not in str(provider_config.api_key).lower())
            info[name] = {
                "model": provider_config.model,
                "api_base": provider_config.api_base or "默认",
                "is_default": is_default,
                "has_api_key": has_key,
                "needs_api_key": name != "ollama",
            }
        return info
