"""OpenAI 提供者测试。"""

from unittest.mock import MagicMock, patch

import pytest

from vision_bridge.providers.openai import OpenAIVisionProvider
from vision_bridge.types import ProviderConfig
from vision_bridge.exceptions import APIError, AuthenticationError


@pytest.fixture
def openai_config():
    return ProviderConfig(
        name="openai",
        model="gpt-4o",
        api_key="test-key",
        max_tokens=1500,
    )


@pytest.fixture
def provider(openai_config):
    return OpenAIVisionProvider(openai_config)


class TestOpenAIVisionProvider:
    """OpenAI 提供者单元测试。"""

    def test_provider_name(self, provider):
        assert provider.provider_name == "openai"

    def test_supports_format(self, provider):
        assert provider.supports_format("png") is True
        assert provider.supports_format("jpeg") is True
        assert provider.supports_format("gif") is True

    def test_describe_image_success(self, provider, sample_image_path, mock_openai_response):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai.return_value = mock_client

            result = provider.describe_image(sample_image_path)
            assert "测试图片" in result

    def test_describe_image_error(self, provider, sample_image_path):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")
            mock_openai.return_value = mock_client

            with pytest.raises(AuthenticationError):
                provider.describe_image(sample_image_path)
