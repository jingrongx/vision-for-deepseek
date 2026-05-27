"""千问提供者测试。"""

from unittest.mock import MagicMock, patch

import pytest

from vision_bridge.providers.qwen import QwenVisionProvider
from vision_bridge.types import ProviderConfig
from vision_bridge.exceptions import APIError, AuthenticationError


@pytest.fixture
def qwen_config():
    return ProviderConfig(
        name="qwen",
        model="qwen-vl-plus",
        api_key="test-key",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_tokens=1500,
    )


@pytest.fixture
def provider(qwen_config):
    return QwenVisionProvider(qwen_config)


class TestQwenVisionProvider:
    """千问提供者单元测试。"""

    def test_provider_name(self, provider):
        assert provider.provider_name == "qwen"

    def test_supports_format(self, provider):
        assert provider.supports_format("png") is True
        assert provider.supports_format("jpeg") is True
        assert provider.supports_format("bmp") is True
        assert provider.supports_format("tiff") is False

    def test_describe_image_success(self, provider, sample_image_path, mock_openai_response):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai.return_value = mock_client

            result = provider.describe_image(sample_image_path)
            assert "测试图片" in result

            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

    def test_describe_image_error(self, provider, sample_image_path):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("403 Forbidden")
            mock_openai.return_value = mock_client

            with pytest.raises(AuthenticationError):
                provider.describe_image(sample_image_path)
