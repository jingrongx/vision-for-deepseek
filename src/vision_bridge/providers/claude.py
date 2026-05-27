"""Anthropic Claude Vision 提供者。

API 文档: https://docs.anthropic.com/en/docs/build-with-claude/vision
"""

from pathlib import Path
from typing import Optional

from .base import VisionProvider
from ..exceptions import APIError, AuthenticationError


class ClaudeVisionProvider(VisionProvider):
    """Claude 视觉模型提供者。

    使用 Anthropic Messages API。
    默认模型: claude-opus-4-5-20251101
    """

    provider_name = "claude"

    def describe_image(
        self,
        image_path: Path,
        prompt: Optional[str] = None,
    ) -> str:
        self._validate_image(image_path)

        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "使用 Claude 提供者需要安装 anthropic 包。\n"
                "  pip install anthropic\n"
                "或: pip install vision-bridge[claude]"
            )

        client = anthropic.Anthropic(api_key=self.config.api_key)

        default_prompt = (
            "请详细描述这张图片的内容。包括：\n"
            "1. 主要对象和场景\n"
            "2. 图片中的文字内容（如有）\n"
            "3. 布局与结构\n"
            "4. 色彩与风格\n"
            "5. 值得注意的细节\n"
            "请用中文详细回答。"
        )

        media_type = self._get_media_type(image_path)
        image_data = self._encode_image(image_path)

        try:
            response = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt or default_prompt},
                    ],
                }],
            )
        except anthropic.AuthenticationError as e:
            raise AuthenticationError(
                f"Claude API 认证失败。请检查 ANTHROPIC_API_KEY 环境变量。\n{e}"
            ) from e
        except anthropic.RateLimitError as e:
            raise APIError(f"Claude API 请求频率超限: {e}") from e
        except Exception as e:
            raise APIError(f"Claude API 调用失败: {e}") from e

        content = response.content[0].text
        return content

    def describe_images(
        self,
        image_paths: list[Path],
        prompt: Optional[str] = None,
    ) -> str:
        for p in image_paths:
            self._validate_image(p)

        import anthropic

        client = anthropic.Anthropic(api_key=self.config.api_key)

        default_prompt = (
            "请详细描述以下图片的内容并进行对比分析。包括：\n"
            "1. 每张图片的主要对象和场景\n"
            "2. 图片中的文字内容（如有）\n"
            "3. 图片之间的异同与关联\n"
            "4. 值得注意的细节\n"
            "请用中文详细回答。"
        )

        content_blocks: list[dict] = []
        for p in image_paths:
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self._get_media_type(p),
                    "data": self._encode_image(p),
                },
            })
        content_blocks.append({"type": "text", "text": prompt or default_prompt})

        try:
            response = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[{"role": "user", "content": content_blocks}],
            )
        except anthropic.AuthenticationError as e:
            raise AuthenticationError(
                f"Claude API 认证失败。请检查 ANTHROPIC_API_KEY 环境变量。\n{e}"
            ) from e
        except anthropic.RateLimitError as e:
            raise APIError(f"Claude API 请求频率超限: {e}") from e
        except Exception as e:
            raise APIError(f"Claude API 调用失败: {e}") from e

        content = response.content[0].text
        return content

    def supports_format(self, image_format: str) -> bool:
        """Claude 支持 PNG, JPEG, GIF, WebP 格式。"""
        return image_format.lower() in ("png", "jpeg", "jpg", "gif", "webp")
