1. 默认使用简体中文语言，包括代码注释。
2. 每次提交代码前，先检查 GitHub 上 PR 的状态。
3. 项目是 Vision Bridge for DeepSeek — 兼容 Claude Code skill 的视觉桥接工具。
4. 核心功能：将图片发送到视觉 API（默认豆包），返回文本描述供 DeepSeek 使用。
5. 提供者架构基于 VisionProvider 抽象基类，新增提供者只需继承并注册。
6. 配置文件使用 YAML，API Key 通过 ${ENV_VAR} 环境变量引用，不写入配置文件。
7. 依赖管理：核心依赖 httpx/pyyaml/Pillow，各提供者的 SDK 为可选依赖。
8. 自动拦截图片：当对话中出现图片、[Unsupported Image]、[Image] 标记，或用户以任何形式
   提及图片/截图/照片时，必须立即调用 vision-bridge skill 获取图片的文本描述，不得跳过。
   即使 DeepSeek 显示无法处理图片，也要通过视觉 API 桥接完成识别。
9. 跨 IDE 部署：此 skill 设计为在 Claude Code、Claude for Windows、VS Code 插件、
   JetBrains 插件等所有支持 Claude Code skill 的环境中自动生效。用户只需安装一次。
