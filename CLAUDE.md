1. 默认使用简体中文语言，包括代码注释。
2. 每次提交代码前，先检查 GitHub 上 PR 的状态。
3. 项目是 Vision Bridge for DeepSeek — 兼容 Claude Code skill 的视觉桥接工具。
4. 核心功能：将图片发送到视觉 API（默认豆包），返回文本描述供 DeepSeek 使用。
5. 提供者架构基于 VisionProvider 抽象基类，新增提供者只需继承并注册。
6. 配置文件使用 YAML，API Key 通过 ${ENV_VAR} 环境变量引用，不写入配置文件。
7. 依赖管理：核心依赖 httpx/pyyaml/Pillow，各提供者的 SDK 为可选依赖。
