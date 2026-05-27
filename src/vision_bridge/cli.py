"""命令行接口 - argparse 子命令结构。

用法:
    vision-bridge describe <image> [--provider doubao] [--model xxx]
    vision-bridge batch <dir> [--provider qwen] [--output-dir out/]
    vision-bridge config show|validate|init
    vision-bridge list-providers
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Windows 终端默认 GBK 编码导致中文乱码，强制 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _cmd_describe(args: argparse.Namespace) -> int:
    """处理 describe 子命令。"""
    import tempfile
    from .core import VisionBridge

    bridge = VisionBridge(args.config)

    # 处理 stdin 输入
    image_path = args.image
    tmp_file = None
    if args.stdin:
        # 从 stdin 读取 base64 数据，写入临时文件
        import base64
        raw_data = sys.stdin.buffer.read()
        if not raw_data:
            print("错误: stdin 无数据输入", file=sys.stderr)
            return 1
        # 尝试解码为 base64，如果是纯 base64 字符串需要先解码
        try:
            data = base64.b64decode(raw_data)
        except Exception:
            # 如果不是 base64，当作原始二进制数据
            data = raw_data

        suffix = ".png"
        if data[:4] == b"\x89PNG":
            suffix = ".png"
        elif data[:2] == b"\xff\xd8":
            suffix = ".jpg"
        elif data[:4] == b"RIFF":
            suffix = ".webp"
        elif data[:6] == b"GIF89a" or data[:6] == b"GIF87a":
            suffix = ".gif"

        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_file.write(data)
        tmp_file.close()
        image_path = tmp_file.name

    try:
        result = bridge.describe(
            image_path=image_path,
            provider=args.provider,
            model=args.model,
            prompt=args.prompt,
            output_format=args.format,
            language=args.language,
        )
        print(result)
        return 0
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    finally:
        if tmp_file:
            Path(tmp_file.name).unlink(missing_ok=True)


def _cmd_compare(args: argparse.Namespace) -> int:
    """处理 compare 子命令。"""
    from .core import VisionBridge

    bridge = VisionBridge(args.config)
    try:
        result = bridge.compare(
            image_paths=args.images,
            provider=args.provider,
            model=args.model,
            prompt=args.prompt,
            output_format=args.format,
            language=args.language,
        )
        print(result)
        return 0
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def _cmd_batch(args: argparse.Namespace) -> int:
    """处理 batch 子命令。"""
    from .core import VisionBridge

    bridge = VisionBridge(args.config)
    try:
        results = bridge.describe_batch(
            directory=args.directory,
            provider=args.provider,
            output_format=args.format,
            output_dir=args.output_dir,
        )

        error_count = sum(1 for v in results.values() if v.startswith("[错误]"))
        success_count = len(results) - error_count

        print(f"\n处理完成: {success_count} 成功, {error_count} 失败 (共 {len(results)} 张图片)")

        if args.output_dir:
            print(f"输出已保存到: {args.output_dir}")

        return 0 if error_count == 0 else 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def _cmd_config_show(args: argparse.Namespace) -> int:
    """显示当前配置。"""
    from .config import load_config
    from .core import VisionBridge

    try:
        bridge = VisionBridge(args.config)
        config = bridge.config
    except Exception as e:
        print(f"配置错误: {e}", file=sys.stderr)
        return 1

    print("=" * 50)
    print("当前配置 / Current Configuration")
    print("=" * 50)
    print(f"默认提供者: {config.default_provider}")
    print()
    print("已配置的提供者:")
    print("-" * 50)

    provider_info = bridge.get_provider_info()
    for name, info in provider_info.items():
        default_mark = " [默认]" if info["is_default"] else ""
        key_status = "已设置" if info["has_api_key"] else "未设置" if info["needs_api_key"] else "无需"
        print(f"  {name}{default_mark}:")
        print(f"    模型: {info['model']}")
        print(f"    API 地址: {info['api_base']}")
        print(f"    API Key: {key_status}")

    print()
    print("输出设置:")
    print(f"  格式: {config.output.format.value}")
    print(f"  语言: {config.output.language}")
    print(f"  包含元数据: {config.output.include_metadata}")
    print("=" * 50)

    return 0


def _cmd_config_validate(args: argparse.Namespace) -> int:
    """验证配置文件。"""
    from .config import validate_config

    issues = validate_config(args.config)
    if not issues:
        print("配置文件验证通过。")
        return 0

    print(f"发现 {len(issues)} 个问题:")
    for issue in issues:
        print(f"  [!] {issue}")
    return 1


def _cmd_config_init(args: argparse.Namespace) -> int:
    """创建默认配置文件。"""
    from .config import create_default_config, ConfigError

    target = args.target or str(
        Path.home() / ".config" / "vision-for-deepseek" / "config.yaml"
    )

    try:
        path = create_default_config(target)
        print(f"配置文件已创建: {path}")
        print()
        print("下一步:")
        print("  1. 编辑配置文件设置默认提供者和模型")
        print("  2. 复制 .env.example 为 .env 并填入 API Key")
        print("  3. 运行 'vision-bridge config validate' 验证配置")
        return 0
    except ConfigError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def _cmd_list_providers(args: argparse.Namespace) -> int:
    """列出可用的视觉提供者。"""
    from .providers import list_providers as lp

    providers = lp()
    print("可用的视觉提供者:")
    print("-" * 30)

    descriptions = {
        "doubao": "豆包（火山方舟）- 默认，国内首选",
        "qwen": "千问（阿里云 DashScope）",
        "claude": "Anthropic Claude Vision",
        "openai": "OpenAI GPT-4V / GPT-4o",
        "ollama": "Ollama 本地视觉模型",
    }

    for name in sorted(providers):
        desc = descriptions.get(name, "")
        print(f"  {name:10s}  {desc}")

    print()
    print("使用方式: vision-bridge describe <image> --provider <name>")
    return 0


def main(args: Optional[list[str]] = None) -> int:
    """CLI 入口函数。"""
    parser = argparse.ArgumentParser(
        prog="vision-bridge",
        description="视觉桥接工具 - 为 DeepSeek 提供多模态识图能力",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  vision-bridge describe photo.jpg
  vision-bridge describe photo.jpg --provider qwen
  vision-bridge compare img1.png img2.png
  vision-bridge batch ./images/ --output-dir ./results/
  vision-bridge config show
  vision-bridge config init
  vision-bridge list-providers
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ---- describe ----
    desc_parser = subparsers.add_parser("describe", help="描述单张图片")
    desc_parser.add_argument("image", type=Path, nargs="?", help="图片文件路径（使用 --stdin 时可省略）")
    desc_parser.add_argument("--stdin", action="store_true", help="从标准输入读取 base64 图片数据")
    desc_parser.add_argument(
        "--provider", "-p",
        choices=["doubao", "qwen", "claude", "openai", "ollama"],
        help="视觉提供者（默认使用配置文件中的设置）",
    )
    desc_parser.add_argument("--model", "-m", help="覆盖默认模型")
    desc_parser.add_argument("--prompt", help="自定义分析提示词")
    desc_parser.add_argument(
        "--format", "-f",
        choices=["structured", "narrative", "simple"],
        help="输出格式",
    )
    desc_parser.add_argument(
        "--language", "-l",
        choices=["zh", "en"],
        default="zh",
        help="输出语言 (默认: zh)",
    )
    desc_parser.add_argument("--config", "-c", type=Path, help="配置文件路径")

    # ---- compare ----
    comp_parser = subparsers.add_parser("compare", help="对比分析多张图片（单次API调用）")
    comp_parser.add_argument("images", type=Path, nargs="+", help="多张图片的文件路径（至少2张）")
    comp_parser.add_argument(
        "--provider", "-p",
        choices=["doubao", "qwen", "claude", "openai", "ollama"],
        help="视觉提供者",
    )
    comp_parser.add_argument("--model", "-m", help="覆盖默认模型")
    comp_parser.add_argument("--prompt", help="自定义分析提示词")
    comp_parser.add_argument(
        "--format", "-f",
        choices=["structured", "narrative", "simple"],
        help="输出格式",
    )
    comp_parser.add_argument(
        "--language", "-l",
        choices=["zh", "en"],
        default="zh",
        help="输出语言 (默认: zh)",
    )
    comp_parser.add_argument("--config", "-c", type=Path, help="配置文件路径")

    # ---- batch ----
    batch_parser = subparsers.add_parser("batch", help="批量描述目录中的图片")
    batch_parser.add_argument("directory", type=Path, help="包含图片的目录路径")
    batch_parser.add_argument(
        "--provider", "-p",
        choices=["doubao", "qwen", "claude", "openai", "ollama"],
        help="视觉提供者",
    )
    batch_parser.add_argument(
        "--format", "-f",
        choices=["structured", "narrative", "simple"],
        help="输出格式",
    )
    batch_parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        help="输出目录（将每张图片的描述保存为 .txt 文件）",
    )
    batch_parser.add_argument("--config", "-c", type=Path, help="配置文件路径")

    # ---- config ----
    config_parser = subparsers.add_parser("config", help="管理配置")
    config_sub = config_parser.add_subparsers(dest="config_action", help="配置操作")

    config_show = config_sub.add_parser("show", help="显示当前配置")
    config_show.add_argument("--config", "-c", type=Path, help="配置文件路径")

    config_validate = config_sub.add_parser("validate", help="验证配置文件")
    config_validate.add_argument("--config", "-c", type=Path, help="配置文件路径")

    config_init = config_sub.add_parser("init", help="初始化默认配置文件")
    config_init.add_argument("--target", "-t", help="目标路径（默认: ~/.config/vision-for-deepseek/config.yaml）")

    # ---- list-providers ----
    subparsers.add_parser("list-providers", help="列出可用的视觉提供者")

    args = parser.parse_args(args)

    if args.command is None:
        parser.print_help()
        return 0

    # 命令分发
    if args.command == "describe":
        if args.image is None and not args.stdin:
            print("错误: 请提供图片路径或使用 --stdin 从标准输入读取", file=sys.stderr)
            return 1
        return _cmd_describe(args)
    elif args.command == "compare":
        return _cmd_compare(args)
    elif args.command == "batch":
        return _cmd_batch(args)
    elif args.command == "config":
        if args.config_action == "show":
            return _cmd_config_show(args)
        elif args.config_action == "validate":
            return _cmd_config_validate(args)
        elif args.config_action == "init":
            return _cmd_config_init(args)
        else:
            print("请指定配置操作: show, validate, init", file=sys.stderr)
            return 1
    elif args.command == "list-providers":
        return _cmd_list_providers(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
