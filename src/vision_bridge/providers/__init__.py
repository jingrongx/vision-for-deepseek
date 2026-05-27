"""视觉提供者注册表。

新增提供者只需: 创建文件 → 继承 VisionProvider → 在这里注册。
"""

from .base import VisionProvider


# 提供者名称 -> 提供者类的映射
PROVIDER_REGISTRY: dict[str, type[VisionProvider]] = {}


def get_provider(name: str) -> type[VisionProvider]:
    """通过名称获取提供者类。

    Args:
        name: 提供者名称 ('doubao', 'qwen', 'claude', 'openai', 'ollama')。

    Returns:
        VisionProvider 子类。

    Raises:
        ValueError: 提供者名称未注册。
    """
    if name not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"未知的提供者 '{name}'。可用: {available}"
        )
    return PROVIDER_REGISTRY[name]


def register_provider(name: str, cls: type[VisionProvider]) -> None:
    """注册一个自定义提供者。

    Args:
        name: 提供者名称。
        cls: VisionProvider 子类。
    """
    PROVIDER_REGISTRY[name] = cls


def list_providers() -> list[str]:
    """列出所有已注册的提供者名称。"""
    return list(PROVIDER_REGISTRY.keys())
