"""OpenAI GPT-4V/GPT-4o 视觉提供者。

API 文档: https://platform.openai.com/docs/guides/vision
"""

from pathlib import Path
from typing import Optional

from .base import VisionProvider
from ..exceptions import APIError, AuthenticationError


class OpenAIVisionProvider(VisionProvider):
    """OpenAI 视觉模型提供者。

    使用 OpenAI Chat Completions API。
    默认模型: gpt-4o
    """

    provider_name = "openai"

    def describe_image(
        self,
        image_path: Path,
        prompt: Optional[str] = None,
    ) -> str:
        self._validate_image(image_path)

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "使用 OpenAI 提供者需要安装 openai 包。\n"
                "  pip install openai\n"
                "或: pip install vision-bridge[openai]"
            )

        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
        )

        default_prompt = (
            "请详细描述这张图片的内容。包括：\n"
            "1. 主要对象和场景\n"
            "2. 图片中的文字内容（如有）\n"
            "3. 布局与结构\n"
            "4. 色彩与风格\n"
            "5. 值得注意的细节\n"
            "请用中文详细回答。"
        )

        data_url = self._encode_data_url(image_path)

        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                        {"type": "text", "text": prompt or default_prompt},
                    ],
                }],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg or "auth" in error_msg.lower():
                raise AuthenticationError(
                    f"OpenAI API 认证失败。请检查 OPENAI_API_KEY 环境变量。\n{error_msg}"
                ) from e
            raise APIError(f"OpenAI API 调用失败: {error_msg}") from e

        content = response.choices[0].message.content
        if content is None:
            raise APIError("OpenAI API 返回空内容")
        return content

    def supports_format(self, image_format: str) -> bool:
        """OpenAI 支持 PNG, JPEG, GIF, WebP 格式。"""
        return image_format.lower() in ("png", "jpeg", "jpg", "gif", "webp")
