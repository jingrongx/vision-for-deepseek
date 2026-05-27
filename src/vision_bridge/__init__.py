"""Vision Bridge - 为 DeepSeek 提供多模态识图能力的视觉桥接工具。

用法:
    from vision_bridge import VisionBridge, describe_image

    # 快速调用
    description = describe_image("photo.jpg")

    # 完整控制
    bridge = VisionBridge()
    description = bridge.describe("photo.jpg", provider="qwen")
    results = bridge.describe_batch("./images/")
"""

from .core import VisionBridge
from .config import load_config
from .exceptions import (
    VisionBridgeError,
    ConfigError,
    ProviderNotAvailableError,
    APIError,
    AuthenticationError,
)

__version__ = "1.0.0"
__all__ = [
    "VisionBridge",
    "describe_image",
    "load_config",
    "VisionBridgeError",
    "ConfigError",
    "ProviderNotAvailableError",
    "APIError",
    "AuthenticationError",
]


def describe_image(
    image_path: str,
    provider: str | None = None,
    model: str | None = None,
    prompt: str | None = None,
    config_path: str | None = None,
) -> str:
    """快速描述单张图片（便捷函数）。

    Args:
        image_path: 图片文件路径。
        provider: 提供者名称，为 None 使用默认提供者。
        model: 模型名称，为 None 使用配置中的默认模型。
        prompt: 自定义提示词。
        config_path: 配置文件路径。

    Returns:
        格式化后的图片描述文本。
    """
    bridge = VisionBridge(config_path)
    return bridge.describe(
        image_path=image_path,
        provider=provider,
        model=model,
        prompt=prompt,
    )
