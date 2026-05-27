"""核心编排测试。"""

import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vision_bridge.core import VisionBridge
from vision_bridge.exceptions import ProviderNotAvailableError


@pytest.fixture
def config_yaml_path(sample_config_dict, tmp_path):
    """创建临时配置文件。"""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config_dict, f)
    return config_path


class TestVisionBridge:
    """VisionBridge 核心类测试。"""

    def test_init_with_config(self, config_yaml_path):
        bridge = VisionBridge(config_yaml_path)
        assert bridge.config.default_provider == "doubao"
        assert "doubao" in bridge.config.providers

    def test_describe_default_provider(self, config_yaml_path, sample_image_path):
        bridge = VisionBridge(config_yaml_path)

        with patch("vision_bridge.providers.doubao.DoubaoVisionProvider.describe_image") as mock_desc:
            mock_desc.return_value = "图片描述测试文本"

            result = bridge.describe(sample_image_path)
            assert "图片描述测试文本" in result
            assert "doubao" in result

    def test_describe_specific_provider(self, config_yaml_path, sample_image_path):
        bridge = VisionBridge(config_yaml_path)

        with patch("vision_bridge.providers.qwen.QwenVisionProvider.describe_image") as mock_desc:
            mock_desc.return_value = "千问描述的图片"

            result = bridge.describe(sample_image_path, provider="qwen")
            assert "千问描述的图片" in result
            assert "qwen" in result

    def test_describe_unknown_provider(self, config_yaml_path, sample_image_path):
        bridge = VisionBridge(config_yaml_path)
        with pytest.raises(ProviderNotAvailableError, match="unknown_provider"):
            bridge.describe(sample_image_path, provider="unknown_provider")

    def test_describe_batch(self, config_yaml_path, sample_image_dir):
        bridge = VisionBridge(config_yaml_path)

        with patch("vision_bridge.providers.doubao.DoubaoVisionProvider.describe_image") as mock_desc:
            mock_desc.return_value = "批量测试描述"

            results = bridge.describe_batch(sample_image_dir)
            assert len(results) == 3
            for name, desc in results.items():
                assert "批量测试描述" in desc

    def test_get_provider_info(self, config_yaml_path):
        bridge = VisionBridge(config_yaml_path)
        info = bridge.get_provider_info()

        assert "doubao" in info
        assert info["doubao"]["is_default"] is True
        assert info["doubao"]["has_api_key"] is True
        # claude 也有 test key，但 ollama 不需要
        assert info.get("qwen", {}).get("has_api_key") is True

    def test_describe_with_model_override(self, config_yaml_path, sample_image_path):
        bridge = VisionBridge(config_yaml_path)

        with patch("vision_bridge.providers.doubao.DoubaoVisionProvider.describe_image") as mock_desc:
            mock_desc.return_value = "自定义模型描述"

            result = bridge.describe(sample_image_path, model="doubao-vision-pro-32k")
            assert "自定义模型描述" in result
