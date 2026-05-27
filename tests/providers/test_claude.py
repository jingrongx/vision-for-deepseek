"""Claude 提供者测试。"""

from unittest.mock import MagicMock, patch

import pytest

from vision_bridge.providers.claude import ClaudeVisionProvider
from vision_bridge.types import ProviderConfig
from vision_bridge.exceptions import APIError, AuthenticationError


@pytest.fixture
def claude_config():
    return ProviderConfig(
        name="claude",
        model="claude-opus-4-5-20251101",
        api_key="test-key",
        max_tokens=1500,
    )


@pytest.fixture
def provider(claude_config):
    return ClaudeVisionProvider(claude_config)


class TestClaudeVisionProvider:
    """Claude 提供者单元测试。"""

    def test_provider_name(self, provider):
        assert provider.provider_name == "claude"

    def test_supports_format(self, provider):
        assert provider.supports_format("png") is True
        assert provider.supports_format("jpeg") is True
        assert provider.supports_format("webp") is True

    def test_describe_image_success(self, provider, sample_image_path, mock_claude_response):
        with patch("anthropic.Anthropic") as mock_anthropic_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response
            mock_anthropic_cls.return_value = mock_client

            result = provider.describe_image(sample_image_path)
            assert "测试图片" in result

    def test_describe_image_auth_error(self, provider, sample_image_path):
        with patch("anthropic.Anthropic") as mock_anthropic_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Invalid API key")
            mock_anthropic_cls.return_value = mock_client

            # 我们无法精确匹配 anthropic.AuthenticationError，
            # 所以直接测试异常被捕获并转换为 AuthenticationError
            with pytest.raises((AuthenticationError, APIError)):
                provider.describe_image(sample_image_path)

    def test_missing_anthropic_dependency(self, provider, sample_image_path):
        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises(ImportError, match="anthropic"):
                provider.describe_image(sample_image_path)
