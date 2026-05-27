"""Ollama 提供者测试。"""

from unittest.mock import MagicMock, patch

import pytest
import httpx

from vision_bridge.providers.ollama import OllamaVisionProvider
from vision_bridge.types import ProviderConfig
from vision_bridge.exceptions import APIError, ProviderNotAvailableError


@pytest.fixture
def ollama_config():
    return ProviderConfig(
        name="ollama",
        model="llava:13b",
        api_base="http://localhost:11434",
        max_tokens=1000,
    )


@pytest.fixture
def provider(ollama_config):
    return OllamaVisionProvider(ollama_config)


class TestOllamaVisionProvider:
    """Ollama 提供者单元测试。"""

    def test_provider_name(self, provider):
        assert provider.provider_name == "ollama"

    def test_supports_format(self, provider):
        assert provider.supports_format("png") is True
        assert provider.supports_format("jpeg") is True
        assert provider.supports_format("gif") is False

    def test_describe_image_success(self, provider, sample_image_path, mock_ollama_response):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = MagicMock()

        with patch("vision_bridge.providers.ollama.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = provider.describe_image(sample_image_path)
            assert "测试图片" in result

    def test_describe_image_connection_error(self, provider, sample_image_path):
        with patch("vision_bridge.providers.ollama.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ProviderNotAvailableError, match="连接"):
                provider.describe_image(sample_image_path)

    def test_describe_image_model_not_found(self, provider, sample_image_path):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with patch("vision_bridge.providers.ollama.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(APIError, match="未找到"):
                provider.describe_image(sample_image_path)
