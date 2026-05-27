"""豆包提供者测试。"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vision_bridge.providers.doubao import DoubaoVisionProvider
from vision_bridge.types import ProviderConfig
from vision_bridge.exceptions import APIError, AuthenticationError


@pytest.fixture
def doubao_config():
    return ProviderConfig(
        name="doubao",
        model="doubao-seed-2-0-mini-260428",
        api_key="test-key",
        api_base="https://ark.cn-beijing.volces.com/api/v3",
        max_tokens=1500,
    )


@pytest.fixture
def provider(doubao_config):
    return DoubaoVisionProvider(doubao_config)


class TestDoubaoVisionProvider:
    """豆包提供者单元测试。"""

    def test_provider_name(self, provider):
        assert provider.provider_name == "doubao"

    def test_supports_format(self, provider):
        assert provider.supports_format("png") is True
        assert provider.supports_format("jpeg") is True
        assert provider.supports_format("webp") is True
        assert provider.supports_format("tiff") is False

    def test_validate_image_success(self, provider, sample_image_path):
        # 不应抛出异常
        provider._validate_image(sample_image_path)

    def test_validate_image_not_found(self, provider):
        with pytest.raises(FileNotFoundError):
            provider._validate_image(Path("/nonexistent/image.png"))

    def test_describe_image_success(self, provider, sample_image_path, mock_openai_response):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai.return_value = mock_client

            result = provider.describe_image(sample_image_path)
            assert "测试图片" in result

            # 验证调用参数
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
            )

    def test_describe_image_auth_error(self, provider, sample_image_path):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")
            mock_openai.return_value = mock_client

            with pytest.raises(AuthenticationError, match="认证失败"):
                provider.describe_image(sample_image_path)

    def test_describe_image_api_error(self, provider, sample_image_path):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("500 Server Error")
            mock_openai.return_value = mock_client

            with pytest.raises(APIError, match="API 调用失败"):
                provider.describe_image(sample_image_path)

    def test_missing_openai_dependency(self, provider, sample_image_path):
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(ImportError, match="openai"):
                provider.describe_image(sample_image_path)
