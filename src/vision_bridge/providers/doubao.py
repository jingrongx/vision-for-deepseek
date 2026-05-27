"""豆包（火山方舟）视觉提供者 - 默认提供者。

API 文档: https://www.volcengine.com/docs/82379
使用 OpenAI 兼容接口。
"""

from pathlib import Path
from typing import Optional

from .base import VisionProvider
from ..exceptions import APIError, AuthenticationError


class DoubaoVisionProvider(VisionProvider):
    """豆包视觉模型提供者。

    使用火山方舟 OpenAI 兼容 API。
    默认模型: doubao-seed-2-0-mini-260428
    """

    provider_name = "doubao"

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
                "使用豆包提供者需要安装 openai 包。\n"
                "  pip install openai\n"
                "或: pip install vision-bridge[doubao]"
            )

        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base or "https://ark.cn-beijing.volces.com/api/v3",
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
                    f"豆包 API 认证失败。请检查 DOUBAO_API_KEY 环境变量。\n{error_msg}"
                ) from e
            raise APIError(f"豆包 API 调用失败: {error_msg}") from e

        content = response.choices[0].message.content
        if content is None:
            raise APIError("豆包 API 返回空内容")
        return content

    def supports_format(self, image_format: str) -> bool:
        """豆包支持 PNG, JPEG, GIF, WebP 格式。"""
        return image_format.lower() in ("png", "jpeg", "jpg", "gif", "webp")
