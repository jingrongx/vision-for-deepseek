"""配置管理 - 加载、验证、环境变量插值。

配置文件使用 YAML 格式，支持 ${ENV_VAR} 语法引用环境变量。
查找优先级:
  1. VISION_BRIDGE_CONFIG 环境变量
  2. ~/.config/vision-for-deepseek/config.yaml
  3. ./config.yaml
"""

import os
import re
from pathlib import Path
from typing import Optional

import yaml

from .exceptions import ConfigError
from .types import AppConfig, OutputSettings, ProviderConfig


# 环境变量引用正则: ${VAR_NAME}
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(value):
    """递归解析字符串中的 ${ENV_VAR} 引用。"""
    if isinstance(value, str):
        def _replace(match):
            var_name = match.group(1)
            env_val = os.environ.get(var_name)
            if env_val is None:
                raise ConfigError(
                    f"环境变量 '{var_name}' 未设置。"
                    f"请确保已设置该变量（参考 .env.example）。"
                )
            return env_val
        return _ENV_VAR_PATTERN.sub(_replace, value)
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def _find_config_path(explicit_path: Optional[str | Path] = None) -> Path:
    """查找配置文件路径。"""
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if path.exists():
            return path
        raise ConfigError(f"指定的配置文件不存在: {path}")

    # 环境变量
    env_path = os.environ.get("VISION_BRIDGE_CONFIG")
    if env_path:
        path = Path(env_path).expanduser().resolve()
        if path.exists():
            return path

    # 用户配置目录
    user_config = Path.home() / ".config" / "vision-for-deepseek" / "config.yaml"
    if user_config.exists():
        return user_config

    # 当前目录
    cwd_config = Path.cwd() / "config.yaml"
    if cwd_config.exists():
        return cwd_config

    raise ConfigError(
        "未找到配置文件。请执行以下操作之一:\n"
        "  1. 运行 'vision-bridge config init' 创建默认配置\n"
        "  2. 复制 config.example.yaml 为 config.yaml\n"
        f"  3. 设置 VISION_BRIDGE_CONFIG 环境变量\n"
        f"  已搜索路径:\n"
        f"    - {user_config}\n"
        f"    - {cwd_config}"
    )


def load_config(config_path: Optional[str | Path] = None) -> AppConfig:
    """加载并验证配置文件。

    Args:
        config_path: 配置文件路径，为 None 时自动查找。

    Returns:
        解析后的 AppConfig 对象。

    Raises:
        ConfigError: 配置文件不存在或格式错误。
    """
    path = _find_config_path(config_path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"配置文件 YAML 格式错误 ({path}): {e}") from e

    if raw is None:
        raise ConfigError(f"配置文件为空: {path}")

    # 解析环境变量
    try:
        raw = _resolve_env_vars(raw)
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"环境变量解析失败: {e}") from e

    # 解析提供者配置
    providers = {}
    providers_raw = raw.get("providers", {})
    if not providers_raw:
        raise ConfigError("配置文件中缺少 'providers' 字段")

    for name, data in providers_raw.items():
        providers[name] = ProviderConfig.from_dict(name, data)

    # 解析输出设置
    output_settings = OutputSettings.from_dict(raw.get("output", {}))

    # 默认提供者
    default_provider = os.environ.get(
        "VISION_BRIDGE_DEFAULT_PROVIDER",
        raw.get("default_provider", "doubao"),
    )

    if default_provider not in providers:
        available = ", ".join(providers.keys())
        raise ConfigError(
            f"默认提供者 '{default_provider}' 未在 providers 中配置。"
            f"可用提供者: {available}"
        )

    return AppConfig(
        default_provider=default_provider,
        providers=providers,
        output=output_settings,
    )


def create_default_config(path: str | Path) -> Path:
    """创建默认配置文件。

    从包内模板复制 config.example.yaml 到指定位置。

    Args:
        path: 目标路径。

    Returns:
        创建的配置文件路径。

    Raises:
        ConfigError: 文件已存在时抛出。
    """
    target = Path(path).expanduser().resolve()
    if target.exists():
        raise ConfigError(f"配置文件已存在: {target}")

    # 尝试查找模板文件
    template_paths = [
        Path(__file__).parent.parent.parent / "config.example.yaml",
        Path.cwd() / "config.example.yaml",
    ]

    template = None
    for tp in template_paths:
        if tp.exists():
            template = tp
            break

    if template is None:
        raise ConfigError("找不到 config.example.yaml 模板文件")

    target.parent.mkdir(parents=True, exist_ok=True)
    content = template.read_text(encoding="utf-8")
    target.write_text(content, encoding="utf-8")
    return target


def validate_config(config_path: Optional[str | Path] = None) -> list[str]:
    """验证配置文件，返回问题列表。"""
    issues = []
    try:
        config = load_config(config_path)
    except ConfigError as e:
        return [str(e)]

    # 检查默认提供者
    provider = config.providers.get(config.default_provider)
    if provider is None:
        issues.append(f"默认提供者 '{config.default_provider}' 未配置")
    elif provider.api_base is None and provider.name not in ("ollama",):
        # 非 Ollama 提供者需要 API key
        if not provider.api_key or "your-" in str(provider.api_key).lower():
            issues.append(
                f"提供者 '{provider.name}' 的 API Key 未设置（仍为占位符）"
            )

    return issues
