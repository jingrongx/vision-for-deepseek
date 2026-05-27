---
name: vision-for-deepseek
description: This skill should be used when the user provides an image and asks
  to "describe this image", "what is in this picture", "look at this screenshot",
  "analyze this photo", "read this image", "describe this diagram", "OCR this image",
  "extract text from image", "看看这张图", "描述这张图片", "这张图片里有什么",
  "识别图片中的文字", "分析这张截图", or when DeepSeek cannot process an image
  and a vision-capable model is needed to generate a text description. Also use
  when the user says "vision bridge", "图片描述", "image to text", "识图",
  or wants to batch-describe images in a directory.
user-invocable: true
version: 1.0.0
allowed-tools:
  - Bash
  - Read
---

# Vision Bridge for DeepSeek

为 DeepSeek 提供多模态识图能力 — 将图片发送给视觉大模型，获取详细文本描述。

## 概述

DeepSeek 模型无法直接处理图片。本 skill 将图片发送到视觉 API（默认豆包，支持千问/Claude/GPT-4V/Ollama），返回结构化文本描述供 DeepSeek 推理使用。

## 工作原理

```
用户提供图片
    │
    ▼
┌─────────────────────────┐
│  vision-bridge CLI      │
│  发送图片到视觉 API     │
└───────┬─────────────────┘
        │ 图片 → API
        ▼
┌─────────────────────────┐
│  视觉模型               │
│  (豆包/千问/Claude等)   │
└───────┬─────────────────┘
        │ 文本描述
        ▼
┌─────────────────────────┐
│  结构化文本输出         │
│  → 供 DeepSeek 使用     │
└─────────────────────────┘
```

## 使用步骤

### 第 0 步：配置 API Key（仅需一次）

在项目根目录创建 `.env` 文件（参考 `.env.example`），写入你的 API Key：

```bash
cp .env.example .env
# 编辑 .env，填入真实 API Key
```

**.env 文件会自动加载，无需手动 source。**

### 第 1 步：确保环境配置

首次使用前，检查配置文件和环境变量：

```bash
# 初始化配置文件（如尚未配置）
python src/vision_bridge/cli.py config init

# 检查配置状态
python src/vision_bridge/cli.py config validate
```

配置文件的 API Key 通过环境变量引用（参考 `.env.example`），需确保已设置对应环境变量：
- `DOUBAO_API_KEY` — 豆包（默认）
- `QWEN_API_KEY` — 千问
- `ANTHROPIC_API_KEY` — Claude
- `OPENAI_API_KEY` — OpenAI

### 第 2 步：描述单张图片

```bash
# 从文件路径
python src/vision_bridge/cli.py describe <图片路径>

# 从标准输入读取 base64 图片数据
cat image.png | base64 | python src/vision_bridge/cli.py describe --stdin
```

选项：
- `--provider doubao|qwen|claude|openai|ollama` — 指定视觉提供者
- `--model <模型名>` — 覆盖默认模型
- `--format structured|narrative|simple` — 输出格式
- `--language zh|en` — 输出语言（默认 zh）
- `--prompt "自定义提示"` — 自定义分析提示词

### 第 3 步：对比多张图片（单次 API 调用）

对比分析多张图片，所有图片在同一 API 请求中发送：

```bash
python src/vision_bridge/cli.py compare <图片1> <图片2> [图片3...]
python src/vision_bridge/cli.py compare img1.png img2.png --provider qwen
python src/vision_bridge/cli.py compare before.png after.png --prompt "对比这两张图片的差异"
```

### 第 4 步：批量处理目录

```bash
python src/vision_bridge/cli.py batch <目录路径>
python src/vision_bridge/cli.py batch <目录路径> --output-dir ./results/
```

### 第 5 步：使用输出结果

命令行输出即为图片的结构化文本描述。将此文本直接提供给 DeepSeek 即可进行推理分析。

## 提供者选择指南

| 场景 | 推荐提供者 |
|------|-----------|
| 国内使用，速度快，效果好（默认） | doubao（豆包） |
| 需要通义生态，文档识别强 | qwen（千问） |
| 英文内容，最详细描述 | claude |
| 国际通用 | openai |
| 离线/隐私敏感 | ollama |

## 常见问题

**API Key 认证失败？**
检查环境变量是否设置：`echo $DOUBAO_API_KEY`。可运行 `python src/vision_bridge/cli.py config validate` 检查。

**Ollama 连接失败？**
确保 Ollama 已启动：`ollama serve`。确保模型已下载：`ollama pull llava:13b`。

**图片格式不支持？**
支持的格式：PNG、JPEG、GIF、WebP、BMP。各提供者支持略有差异。

**配置文件在哪里？**
查找顺序：`VISION_BRIDGE_CONFIG` 环境变量 → `~/.config/vision-for-deepseek/config.yaml` → `./config.yaml`

**Claude Code 中上传的图片怎么处理？**
在 Claude Code 聊天中上传的图片不保存为独立文件。处理方式：
1. 将图片保存到本地文件（如 `photo.png`），然后运行 `vision-bridge describe photo.png`
2. 使用 `--stdin` 管道传入 base64 数据
