"""视觉提供者抽象基类。"""

import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..exceptions import ImageTooLargeError, UnsupportedFormatError
from ..types import ImageFormat, ProviderConfig

# 最大图片大小: 20MB
MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024

# 支持的图片格式及其 MIME 类型
SUPPORTED_FORMATS: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


class VisionProvider(ABC):
    """视觉提供者抽象基类。

    所有视觉模型提供者应继承此类，实现 describe_image 方法。
    每个子类封装将图片发送到特定 API 并获取文本描述的逻辑。
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._validate_config()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者唯一标识符: 'doubao', 'qwen', 'claude', 'openai', 'ollama'."""
        ...

    @abstractmethod
    def describe_image(
        self,
        image_path: Path,
        prompt: Optional[str] = None,
    ) -> str:
        """分析图片并返回文本描述。

        Args:
            image_path: 图片文件路径。
            prompt: 可选的自定义提示词。

        Returns:
            图片的详细文本描述。

        Raises:
            ImageTooLargeError: 图片超过大小限制。
            UnsupportedFormatError: 图片格式不受支持。
            APIError: API 调用失败。
        """
        ...

    def describe_images(
        self,
        image_paths: list[Path],
        prompt: Optional[str] = None,
    ) -> str:
        """分析多张图片并返回文本描述。

        将多张图片在同一 API 调用中发送给视觉模型，用于对比、关联分析。

        Args:
            image_paths: 多张图片的路径列表。
            prompt: 可选的自定义提示词。

        Returns:
            所有图片的综合文本描述。

        Raises:
            ImageTooLargeError: 图片超过大小限制。
            UnsupportedFormatError: 图片格式不受支持。
            APIError: API 调用失败。
        """
        raise NotImplementedError(
            f"[{self.provider_name}] 不支持多图识别"
        )

    @abstractmethod
    def supports_format(self, image_format: str) -> bool:
        """检查此提供者是否支持指定格式。"""
        ...

    def _validate_config(self) -> None:
        """验证配置完整性。子类可覆盖以添加额外验证。"""
        if not self.config.model:
            raise ValueError(f"[{self.provider_name}] 未指定模型名称")

    def _validate_image(self, image_path: Path) -> None:
        """验证图片文件存在、格式受支持、大小合理。

        Raises:
            FileNotFoundError: 文件不存在。
            UnsupportedFormatError: 格式不受支持。
            ImageTooLargeError: 文件超过 20MB。
        """
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        if not image_path.is_file():
            raise FileNotFoundError(f"路径不是文件: {image_path}")

        suffix = image_path.suffix.lower()
        if suffix not in SUPPORTED_FORMATS:
            raise UnsupportedFormatError(
                f"不支持的图片格式: {suffix}。"
                f"支持的格式: {', '.join(SUPPORTED_FORMATS.keys())}"
            )

        file_size = image_path.stat().st_size
        if file_size > MAX_IMAGE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            limit_mb = MAX_IMAGE_SIZE_BYTES / (1024 * 1024)
            raise ImageTooLargeError(
                f"图片文件过大: {size_mb:.1f}MB。"
                f"最大允许: {limit_mb:.0f}MB"
            )

    def _get_media_type(self, image_path: Path) -> str:
        """根据文件扩展名获取 MIME 类型。"""
        suffix = image_path.suffix.lower()
        return SUPPORTED_FORMATS.get(suffix, "image/png")

    def _encode_image(self, image_path: Path) -> str:
        """将图片编码为 base64 字符串。"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _encode_data_url(self, image_path: Path) -> str:
        """将图片编码为 data URL 格式 (data:image/xxx;base64,...)。"""
        media_type = self._get_media_type(image_path)
        b64_data = self._encode_image(image_path)
        return f"data:{media_type};base64,{b64_data}"
