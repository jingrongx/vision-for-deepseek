"""自定义异常层次。"""


class VisionBridgeError(Exception):
    """所有 vision-bridge 异常的基类。"""
    pass


class ConfigError(VisionBridgeError):
    """配置文件不存在、格式错误或缺少必需字段。"""
    pass


class ProviderNotAvailableError(VisionBridgeError):
    """指定的提供者不可用（未安装依赖或未配置）。"""
    pass


class ImageTooLargeError(VisionBridgeError):
    """图像文件超过大小限制。"""
    pass


class UnsupportedFormatError(VisionBridgeError):
    """图像格式不受当前提供者支持。"""
    pass


class APIError(VisionBridgeError):
    """API 调用失败。"""
    pass


class AuthenticationError(APIError):
    """API 认证失败（API Key 无效或未设置）。"""
    pass


class RateLimitError(APIError):
    """API 请求频率超限。"""
    pass
