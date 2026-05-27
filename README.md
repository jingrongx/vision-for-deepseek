# Vision Bridge for DeepSeek

为 DeepSeek 大模型提供多模态识图能力的视觉桥接工具。兼容 Claude Code skill。

## 解决的问题

DeepSeek 模型无法直接处理图片。Vision Bridge 作为中间层，将图片发送到视觉大模型 API（豆包/千问/Claude/GPT-4V/Ollama），返回结构化的文本描述，再提供给 DeepSeek 进行推理。

## 支持的视觉提供者

| 提供者 | 默认模型 | 说明 |
|--------|---------|------|
| **doubao** (默认) | `doubao-seed-2-0-mini-260428` | 豆包/火山方舟，国内首选 |
| qwen | `qwen-vl-plus` | 千问/阿里 DashScope |
| claude | `claude-opus-4-5-20251101` | Anthropic Claude Vision |
| openai | `gpt-4o` | OpenAI GPT-4V/GPT-4o |
| ollama | `llava:13b` | 本地模型，无需 API Key |

## 快速开始

### 安装

```bash
# 克隆仓库
git clone git@github.com:jingrongx/vision-for-deepseek.git
cd vision-for-deepseek

# 安装（推荐使用虚拟环境）
pip install -e ".[all]"
```

### 配置

```bash
# 1. 设置 API Key 环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key
source .env  # 或手动 export

# 2. 初始化配置文件
vision-bridge config init

# 3. 验证配置
vision-bridge config validate
```

### 使用

```bash
# 描述单张图片（使用默认提供者 - 豆包）
vision-bridge describe photo.jpg

# 使用千问
vision-bridge describe photo.jpg --provider qwen

# 使用指定模型
vision-bridge describe photo.jpg --model doubao-vision-pro-32k

# 批量处理
vision-bridge batch ./images/ --output-dir ./results/

# 查看当前配置
vision-bridge config show

# 列出所有提供者
vision-bridge list-providers
```

### Python 库使用

```python
from vision_bridge import VisionBridge, describe_image

# 快速调用
description = describe_image("photo.jpg")
print(description)

# 完整控制
bridge = VisionBridge()
result = bridge.describe("photo.jpg", provider="qwen")
print(result)

# 批量处理
results = bridge.describe_batch("./images/", output_dir="./results/")
```

## 项目结构

```
vision-for-deepseek/
├── SKILL.md                  # Claude Code skill 定义
├── src/vision_bridge/        # Python 包
│   ├── core.py               # VisionBridge 核心编排器
│   ├── config.py             # 配置管理
│   ├── cli.py                # 命令行接口
│   ├── formatter.py          # 输出格式化
│   └── providers/            # 视觉提供者
│       ├── doubao.py         # 豆包（默认）
│       ├── qwen.py           # 千问
│       ├── claude.py         # Claude
│       ├── openai.py         # OpenAI
│       └── ollama.py         # Ollama 本地
├── config.example.yaml       # 配置示例
├── .env.example              # 环境变量示例
└── tests/                    # 测试
```

## 扩展新提供者

1. 在 `src/vision_bridge/providers/` 创建新文件，继承 `VisionProvider`
2. 实现 `describe_image()` 和 `supports_format()` 方法
3. 在 `core.py` 的 `_register_builtin_providers()` 中注册

## License

MIT
