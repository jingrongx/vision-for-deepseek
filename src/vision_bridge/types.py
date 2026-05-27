"""共享类型定义。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OutputFormat(Enum):
    """输出格式枚举。"""
    STRUCTURED = "structured"   # 分段描述，最适合 LLM 消费
    NARRATIVE = "narrative"     # 自然段落
    SIMPLE = "simple"           # 纯文本，不含元数据


class ImageFormat(Enum):
    """支持的图像格式。"""
    PNG = "png"
    JPEG = "jpeg"
    GIF = "gif"
    WEBP = "webp"
    BMP = "bmp"


@dataclass
class ProviderConfig:
    """单个视觉提供者的配置。"""
    name: str                              # "doubao", "qwen", "claude", "openai", "ollama"
    model: str                             # 模型名称
    api_key: Optional[str] = None          # API Key（Ollama 不需要）
    api_base: Optional[str] = None         # 自定义 API 地址
    max_tokens: int = 1500                 # 最大输出 token 数
    temperature: float = 0.0               # 温度参数

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "ProviderConfig":
        """从字典创建配置。"""
        return cls(
            name=name,
            model=data.get("model", ""),
            api_key=data.get("api_key"),
            api_base=data.get("api_base"),
            max_tokens=data.get("max_tokens", 1500),
            temperature=data.get("temperature", 0.0),
        )


@dataclass
class OutputSettings:
    """输出格式化设置。"""
    format: OutputFormat = OutputFormat.STRUCTURED
    language: str = "zh"                   # "zh" / "en"
    include_metadata: bool = True          # 是否在输出中包含提供者/模型/时间信息

    @classmethod
    def from_dict(cls, data: dict) -> "OutputSettings":
        """从字典创建设置。"""
        fmt = data.get("format", "structured")
        if isinstance(fmt, str):
            fmt = OutputFormat(fmt)
        return cls(
            format=fmt,
            language=data.get("language", "zh"),
            include_metadata=data.get("include_metadata", True),
        )


@dataclass
class AppConfig:
    """应用完整配置。"""
    default_provider: str = "doubao"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    output: OutputSettings = field(default_factory=OutputSettings)
