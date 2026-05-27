"""配置模块测试。"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from vision_bridge.config import (
    load_config,
    validate_config,
    _find_config_path,
    _resolve_env_vars,
    ConfigError,
)
from vision_bridge.types import AppConfig, OutputFormat


class TestResolveEnvVars:
    """测试环境变量解析。"""

    def test_resolve_simple_var(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "test-value")
        result = _resolve_env_vars("${TEST_KEY}")
        assert result == "test-value"

    def test_resolve_missing_var(self):
        with pytest.raises(ConfigError, match="未设置"):
            _resolve_env_vars("${NONEXISTENT_VAR}")

    def test_resolve_in_dict(self, monkeypatch):
        monkeypatch.setenv("KEY1", "val1")
        monkeypatch.setenv("KEY2", "val2")
        data = {"a": "${KEY1}", "b": {"c": "${KEY2}"}}
        result = _resolve_env_vars(data)
        assert result == {"a": "val1", "b": {"c": "val2"}}

    def test_resolve_non_string_passthrough(self):
        assert _resolve_env_vars(42) == 42
        assert _resolve_env_vars(True) is True


class TestLoadConfig:
    """测试配置加载。"""

    def test_load_from_dict(self, sample_config_dict, tmp_path):
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config_dict, f)

        config = load_config(config_path)
        assert config.default_provider == "doubao"
        assert "doubao" in config.providers
        assert config.providers["doubao"].model == "doubao-seed-2-0-mini-260428"
        assert config.output.format == OutputFormat.STRUCTURED
        assert config.output.language == "zh"

    def test_load_default_provider_not_found(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        data = {
            "default_provider": "unknown",
            "providers": {"claude": {"model": "claude"}},
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        with pytest.raises(ConfigError, match="默认提供者"):
            load_config(config_path)

    def test_load_empty_config(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text("")

        with pytest.raises(ConfigError, match="为空"):
            load_config(config_path)

    def test_load_missing_providers(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text("default_provider: doubao\n")

        with pytest.raises(ConfigError, match="providers"):
            load_config(config_path)

    def test_env_var_override_default_provider(self, sample_config_dict, tmp_path, monkeypatch):
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config_dict, f)

        monkeypatch.setenv("VISION_BRIDGE_DEFAULT_PROVIDER", "claude")
        config = load_config(config_path)
        assert config.default_provider == "claude"


class TestValidateConfig:
    """测试配置验证。"""

    def test_valid_config(self, sample_config_dict, tmp_path):
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config_dict, f)

        issues = validate_config(config_path)
        assert len(issues) == 0

    def test_no_config(self):
        issues = validate_config("/nonexistent/path/config.yaml")
        assert len(issues) == 1


class TestFindConfigPath:
    """测试配置路径查找。"""

    def test_explicit_path(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text("default_provider: doubao\nproviders: {}")

        found = _find_config_path(config_path)
        assert found == config_path

    def test_explicit_path_not_exists(self):
        with pytest.raises(ConfigError, match="指定"):
            _find_config_path("/nonexistent/path.yaml")

    def test_env_var_path(self, tmp_path, monkeypatch):
        config_path = tmp_path / "custom.yaml"
        config_path.write_text("default_provider: doubao\nproviders: {}")
        monkeypatch.setenv("VISION_BRIDGE_CONFIG", str(config_path))

        found = _find_config_path()
        assert found == config_path
