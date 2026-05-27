"""共享测试 fixtures。"""

import base64
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


def _create_test_image_bytes(width=100, height=100, color=(255, 0, 0)):
    """创建测试图片的字节数据。"""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_image_path(tmp_path):
    """创建临时测试图片文件。"""
    img_path = tmp_path / "test_image.png"
    img_data = _create_test_image_bytes()
    img_path.write_bytes(img_data)
    return img_path


@pytest.fixture
def sample_image_dir(tmp_path):
    """创建包含测试图片的临时目录。"""
    for i in range(3):
        img_path = tmp_path / f"image_{i}.png"
        img_data = _create_test_image_bytes(color=(i * 80, 100, 100))
        img_path.write_bytes(img_data)
    return tmp_path


@pytest.fixture
def sample_config_dict():
    """示例配置字典。"""
    return {
        "default_provider": "doubao",
        "providers": {
            "doubao": {
                "model": "doubao-seed-2-0-mini-260428",
                "api_key": "test-doubao-key",
                "api_base": "https://ark.cn-beijing.volces.com/api/v3",
                "max_tokens": 1500,
                "temperature": 0.0,
            },
            "qwen": {
                "model": "qwen-vl-plus",
                "api_key": "test-qwen-key",
                "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "max_tokens": 1500,
                "temperature": 0.0,
            },
            "claude": {
                "model": "claude-opus-4-5-20251101",
                "api_key": "test-claude-key",
                "max_tokens": 1500,
                "temperature": 0.0,
            },
            "openai": {
                "model": "gpt-4o",
                "api_key": "test-openai-key",
                "max_tokens": 1500,
                "temperature": 0.0,
            },
        },
        "output": {
            "format": "structured",
            "language": "zh",
            "include_metadata": True,
        },
    }


@pytest.fixture
def mock_openai_response():
    """模拟 OpenAI 兼容 API 的响应。"""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = "这是一张测试图片，包含红色背景。"
    return mock


@pytest.fixture
def mock_claude_response():
    """模拟 Claude API 的响应。"""
    mock = MagicMock()
    mock.content = [MagicMock()]
    mock.content[0].text = "这是一张测试图片，包含红色背景。"
    return mock


@pytest.fixture
def mock_ollama_response():
    """模拟 Ollama API 的响应。"""
    return {"response": "这是一张测试图片，包含红色背景。"}
