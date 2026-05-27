"""Ollama 本地视觉模型提供者。

API 文档: https://github.com/ollama/ollama/blob/main/docs/api.md
无需 API Key，需本地运行 Ollama 服务。
"""

from pathlib import Path
from typing import Optional

import httpx

from .base import VisionProvider
from ..exceptions import APIError, ProviderNotAvailableError


class OllamaVisionProvider(VisionProvider):
    """Ollama 本地视觉模型提供者。

    使用 Ollama HTTP API (/api/generate)。
    默认模型: llava:13b

    使用前需确保:
      1. Ollama 已安装并运行: ollama serve
      2. 模型已下载: ollama pull llava:13b
    """

    provider_name = "ollama"

    # Ollama 支持的视觉模型
    KNOWN_VISION_MODELS = {
        "llava:13b", "llava:7b", "llava:latest",
        "bakllava", "bakllava:latest",
        "minicpm-v", "minicpm-v:latest",
        "llava-llama3", "llava-llama3:latest",
    }

    def describe_image(
        self,
        image_path: Path,
        prompt: Optional[str] = None,
    ) -> str:
        self._validate_image(image_path)

        api_base = self.config.api_base or "http://localhost:11434"
        image_data = self._encode_image(image_path)

        default_prompt = (
            "请详细描述这张图片的内容。包括：\n"
            "1. 主要对象和场景\n"
            "2. 图片中的文字内容（如有）\n"
            "3. 布局与结构\n"
            "4. 色彩与风格\n"
            "5. 值得注意的细节\n"
            "请用中文详细回答。"
        )

        request_body = {
            "model": self.config.model,
            "prompt": prompt or default_prompt,
            "images": [image_data],
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{api_base}/api/generate",
                    json=request_body,
                )
                response.raise_for_status()
                result = response.json()
        except httpx.ConnectError:
            raise ProviderNotAvailableError(
                f"无法连接到 Ollama 服务 ({api_base})。\n"
                "请确保 Ollama 已启动:\n"
                "  ollama serve"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise APIError(
                    f"模型 '{self.config.model}' 未找到。\n"
                    f"请先下载模型:\n"
                    f"  ollama pull {self.config.model}"
                )
            raise APIError(f"Ollama API 调用失败: {e}")
        except Exception as e:
            raise APIError(f"Ollama API 调用失败: {e}")

        response_text = result.get("response", "")
        if not response_text:
            raise APIError("Ollama API 返回空内容")

        return response_text

    def describe_images(
        self,
        image_paths: list[Path],
        prompt: Optional[str] = None,
    ) -> str:
        for p in image_paths:
            self._validate_image(p)

        import httpx

        api_base = self.config.api_base or "http://localhost:11434"
        image_datas = [self._encode_image(p) for p in image_paths]

        default_prompt = (
            "请详细描述以下图片的内容并进行对比分析。包括：\n"
            "1. 每张图片的主要对象和场景\n"
            "2. 图片中的文字内容（如有）\n"
            "3. 图片之间的异同与关联\n"
            "4. 值得注意的细节\n"
            "请用中文详细回答。"
        )

        request_body = {
            "model": self.config.model,
            "prompt": prompt or default_prompt,
            "images": image_datas,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{api_base}/api/generate",
                    json=request_body,
                )
                response.raise_for_status()
                result = response.json()
        except httpx.ConnectError:
            raise ProviderNotAvailableError(
                f"无法连接到 Ollama 服务 ({api_base})。\n请确保 Ollama 已启动: ollama serve"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise APIError(
                    f"模型 '{self.config.model}' 未找到。\n请先下载: ollama pull {self.config.model}"
                )
            raise APIError(f"Ollama API 调用失败: {e}")
        except Exception as e:
            raise APIError(f"Ollama API 调用失败: {e}")

        response_text = result.get("response", "")
        if not response_text:
            raise APIError("Ollama API 返回空内容")
        return response_text

    def supports_format(self, image_format: str) -> bool:
        """Ollama 视觉模型通常支持 PNG, JPEG 格式。"""
        return image_format.lower() in ("png", "jpeg", "jpg")
