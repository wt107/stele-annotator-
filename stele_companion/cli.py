# -*- coding: utf-8 -*-
"""
命令行入口模块
"""

import sys
import os
import argparse
import tempfile
import json
from pathlib import Path

from .utils import log_err, log_ok, log_info, log_step, log_warn
from .network import fetch_stele_text, _extract_stele_name
from .core import build_dict, annotate
from .render import render_html


class AIOutput:
    """AI友好的输出处理器"""
    
    def __init__(self, json_mode=False):
        self.json_mode = json_mode
        self.result = {
            "success": True,
            "command": None,
            "inputs": {},
            "outputs": {},
            "messages": [],
            "errors": [],
            "warnings": []
        }
    
    def set_command(self, cmd):
        self.result["command"] = cmd
    
    def add_input(self, key, value):
        self.result["inputs"][key] = str(value)
    
    def add_output(self, key, value):
        self.result["outputs"][key] = str(value)
    
    def info(self, msg):
        if self.json_mode:
            self.result["messages"].append(msg)
        else:
            log_info(msg)
    
    def ok(self, msg):
        if self.json_mode:
            self.result["messages"].append(f"[OK] {msg}")
        else:
            log_ok(msg)
    
    def error(self, msg):
        self.result["success"] = False
        if self.json_mode:
            self.result["errors"].append(msg)
        else:
            log_err(msg)
    
    def warning(self, msg):
        if self.json_mode:
            self.result["warnings"].append(msg)
        else:
            log_warn(msg)
    
    def print_result(self):
        if self.json_mode:
            print(json.dumps(self.result, ensure_ascii=False, indent=2))
        
    def exit(self, code=0):
        if self.json_mode:
            self.print_result()
        sys.exit(code)


def run_all(
    input_path,
    dict_paths,
    output_horizontal=None,
    output_vertical=None,
    start_line=None,
    start_marker=None,
    font_size="medium",
    theme="classic",
    enable_convert=False,
    annotated_output=None,
    input_paragraphs=None,
    output=None,
):
    """完整流程：加载字典 → 标注文本 → 输出 HTML"""
    
    if output is None:
        output = AIOutput(json_mode=False)

    output.info("=" * 50)
    output.info("碑帖学习伴侣 stele-companion 完整流程")
    output.info("=" * 50)

    # Step 1: 标注
    if annotated_output is None:
        annotated_output = tempfile.mktemp(suffix="_annotated.json")

    try:
        annotate(
            input_path,
            dict_paths,
            annotated_output,
            start_line=start_line,
            start_marker=start_marker,
            enable_convert=enable_convert,
            input_paragraphs=input_paragraphs,
        )
        output.ok(f"标注完成: {annotated_output}")
    except Exception as e:
        output.error(f"标注失败: {str(e)}")
        raise

    # Step 2: 渲染横版
    if output_horizontal:
        try:
            render_html(
                annotated_output,
                output_horizontal,
                format_type="horizontal",
                font_size=font_size,
                theme=theme,
            )
            output.ok(f"横版渲染完成: {output_horizontal}")
        except Exception as e:
            output.error(f"横版渲染失败: {str(e)}")
            raise

    # Step 3: 渲染竖版
    if output_vertical:
        try:
            render_html(
                annotated_output,
                output_vertical,
                format_type="vertical",
                font_size=font_size,
                theme=theme,
            )
            output.ok(f"竖版渲染完成: {output_vertical}")
        except Exception as e:
            output.error(f"竖版渲染失败: {str(e)}")
            raise

    output.info("=" * 50)
    output.ok("处理完成！")
    if output_horizontal:
        output.info(f"横版: {output_horizontal}")
    if output_vertical:
        output.info(f"竖版: {output_vertical}")
    output.info("=" * 50)


def validate_input_file(path, output):
    """验证输入文件安全性"""
    p = Path(path).resolve()
    
    # 检查路径遍历攻击
    try:
        p.relative_to(Path.cwd())
    except ValueError:
        output.error(f"路径安全检查失败: {path} 不在当前目录下")
        return None
    
    # 检查文件存在性
    if not p.exists():
        output.error(f"文件不存在: {path}")
        return None
    
    # 检查文件大小（防止超大文件）
    size = p.stat().st_size
    if size > 100 * 1024 * 1024:  # 100MB
        output.error(f"文件过大: {size / 1024 / 1024:.1f}MB > 100MB")
        return None
    
    # 检查文件扩展名
    allowed_ext = {'.doc', '.docx', '.txt', '.json'}
    if p.suffix.lower() not in allowed_ext:
        output.warning(f"非标准扩展名: {p.suffix}，建议转换为 .doc/.docx/.txt")
    
    return str(p)


def main():
    parser = argparse.ArgumentParser(
        description="碑帖学习伴侣 stele-companion v2.0 (AI Skill优化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
AI使用提示:
  --json      : 输出JSON格式结果，便于AI解析
  --dry-run   : 预览操作，不实际执行

使用流程:
  1. build-dict : 从标准文档生成字典
  2. annotate   : 文本比对标注
  3. render     : 生成 HTML（横版/竖版）
  4. all        : 一步完成（推荐）

示例（AI推荐）:
  stele-companion all 肥致碑.doc \\
      --dict 张迁碑_dict.json \\
      --output-horizontal 肥致碑_横版.html \\
      --output-vertical 肥致碑_竖版.html \\
      --start-marker "从事君之元嗣" \\
      --json
        """,
    )
    
    # 全局选项
    parser.add_argument("--json", action="store_true", help="输出JSON格式结果")
    parser.add_argument("--dry-run", action="store_true", help="预览操作，不实际执行")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # ── build-dict ──
    p1 = subparsers.add_parser("build-dict", help="从标准文档构建字典")
    p1.add_argument("input", help="输入文件 (.doc/.docx/.txt)")
    p1.add_argument("-o", "--output", required=True, help="输出字典文件 (.json)")
    p1.add_argument("--start-line", type=int, help="正文起始行号 (1-based)")
    p1.add_argument("--start-marker", help="正文起始标记文本")
    p1.add_argument(
        "--variant",
        choices=["simplified", "traditional"],
        default="simplified",
        help="基准字形（默认: simplified）",
    )

    # ── annotate ──
    p2 = subparsers.add_parser("annotate", help="文本比对标注")
    p2.add_argument("input", help="待标注文本文件 (.doc/.docx/.txt)")
    p2.add_argument("--dict", required=True, help="字典文件路径，多个用逗号分隔")
    p2.add_argument("-o", "--output", required=True, help="输出标注数据 (.json)")
    p2.add_argument("--start-line", type=int, help="正文起始行号")
    p2.add_argument("--start-marker", help="正文起始标记文本")
    p2.add_argument("--convert", action="store_true", help="启用简繁转换匹配")

    # ── render ──
    p3 = subparsers.add_parser("render", help="生成 HTML")
    p3.add_argument("--annotated", required=True, help="标注数据文件 (.json)")
    p3.add_argument("-o", "--output", required=True, help="输出 HTML 文件")
    p3.add_argument(
        "--format",
        choices=["horizontal", "vertical"],
        default="horizontal",
        help="输出格式（默认: horizontal）",
    )
    p3.add_argument(
        "--font-size",
        choices=["small", "medium", "large"],
        default="medium",
        help="字号（默认: medium）",
    )
    p3.add_argument(
        "--theme",
        choices=["classic", "elegant"],
        default="classic",
        help="颜色主题（默认: classic）",
    )

    # ── all ──
    p4 = subparsers.add_parser("all", help="完整流程（推荐）")
    p4.add_argument("input", help="待标注碑文文件 (.doc/.docx/.txt)")
    p4.add_argument("--dict", required=True, help="字典文件路径，多个用逗号分隔")
    p4.add_argument("--output-horizontal", help="横版 HTML 输出路径")
    p4.add_argument("--output-vertical", help="竖版 HTML 输出路径")
    p4.add_argument("--annotated", help="标注数据 JSON 输出路径（可选）")
    p4.add_argument("--start-line", type=int, help="正文起始行号")
    p4.add_argument("--start-marker", help="正文起始标记文本")
    p4.add_argument(
        "--font-size",
        choices=["small", "medium", "large"],
        default="medium",
        help="字号（默认: medium）",
    )
    p4.add_argument(
        "--theme",
        choices=["classic", "elegant"],
        default="classic",
        help="颜色主题（默认: classic）",
    )
    p4.add_argument("--convert", action="store_true", help="启用简繁转换匹配")
    p4.add_argument("--fetch", action="store_true", help="自动从网络获取权威碑帖原文")
    p4.add_argument(
        "--source",
        default="auto",
        choices=["auto", "wikisource", "yamoke"],
        help="数据源（默认: auto）",
    )

    args = parser.parse_args()
    
    # 初始化AI输出处理器
    output = AIOutput(json_mode=args.json)
    output.set_command(args.command)
    
    if not args.command:
        if args.json:
            output.error("未指定子命令")
            output.exit(1)
        else:
            parser.print_help()
            sys.exit(1)

    # ── build-dict ──
    if args.command == "build-dict":
        output.add_input("input", args.input)
        output.add_input("output", args.output)
        
        # 验证输入
        validated_input = validate_input_file(args.input, output)
        if not validated_input:
            output.exit(1)
        
        if not args.start_line and not args.start_marker:
            output.error("必须指定 --start-line 或 --start-marker")
            output.exit(1)
        if args.start_line is not None and args.start_line < 1:
            output.error("--start-line 必须大于 0")
            output.exit(1)
        
        # 检查输出目录
        output_dir = Path(args.output).parent
        if not output_dir.exists():
            output.error(f"输出目录不存在: {output_dir}")
            output.exit(1)
        
        if args.dry_run:
            output.info(f"[DRY-RUN] 将构建字典: {validated_input} -> {args.output}")
            output.add_output("dict", args.output)
            output.exit(0)
        
        try:
            build_dict(
                validated_input, args.output, args.start_line, args.start_marker, args.variant
            )
            output.add_output("dict", args.output)
            output.ok(f"字典构建完成: {args.output}")
        except Exception as e:
            output.error(f"字典构建失败: {str(e)}")
            output.exit(1)
        
        output.exit(0)

    # ── annotate ──
    elif args.command == "annotate":
        output.add_input("input", args.input)
        output.add_input("dict", args.dict)
        output.add_input("output", args.output)
        
        dict_paths = [p.strip() for p in args.dict.split(",")]
        dict_paths = [p for p in dict_paths if p]
        if not dict_paths:
            output.error("必须指定有效的字典文件路径")
            output.exit(1)
        
        # 验证所有字典文件
        validated_dicts = []
        for dp in dict_paths:
            validated = validate_input_file(dp, output)
            if not validated:
                output.exit(1)
            validated_dicts.append(validated)
        
        # 验证输入文件
        validated_input = validate_input_file(args.input, output)
        if not validated_input:
            output.exit(1)
        
        if args.dry_run:
            output.info(f"[DRY-RUN] 将标注文本: {validated_input}")
            output.info(f"[DRY-RUN] 使用字典: {', '.join(validated_dicts)}")
            output.add_output("annotated", args.output)
            output.exit(0)
        
        try:
            annotate(
                validated_input,
                validated_dicts,
                args.output,
                args.start_line,
                args.start_marker,
                args.convert,
            )
            output.add_output("annotated", args.output)
            output.ok(f"标注完成: {args.output}")
        except Exception as e:
            output.error(f"标注失败: {str(e)}")
            output.exit(1)
        
        output.exit(0)

    # ── render ──
    elif args.command == "render":
        output.add_input("annotated", args.annotated)
        output.add_input("format", args.format)
        
        validated = validate_input_file(args.annotated, output)
        if not validated:
            output.exit(1)
        
        # 检查输出目录
        output_dir = Path(args.output).parent
        if not output_dir.exists():
            output.error(f"输出目录不存在: {output_dir}")
            output.exit(1)
        
        if args.dry_run:
            output.info(f"[DRY-RUN] 将渲染 {args.format} 格式: {validated} -> {args.output}")
            output.add_output("html", args.output)
            output.exit(0)
        
        try:
            render_html(
                validated, args.output, args.format, args.font_size, args.theme
            )
            output.add_output("html", args.output)
            output.ok(f"渲染完成: {args.output}")
        except Exception as e:
            output.error(f"渲染失败: {str(e)}")
            output.exit(1)
        
        output.exit(0)

    # ── all ──
    elif args.command == "all":
        output.add_input("input", args.input)
        output.add_input("dict", args.dict)
        
        dict_paths = [p.strip() for p in args.dict.split(",")]
        dict_paths = [p for p in dict_paths if p]
        if not dict_paths:
            output.error("必须指定有效的字典文件路径")
            output.exit(1)
        
        # 验证所有字典文件
        validated_dicts = []
        for dp in dict_paths:
            validated = validate_input_file(dp, output)
            if not validated:
                output.exit(1)
            validated_dicts.append(validated)
        
        # 检查输出路径
        if not args.output_horizontal and not args.output_vertical:
            output.error("必须指定 --output-horizontal 和/或 --output-vertical")
            output.exit(1)
        
        for out_path in [args.output_horizontal, args.output_vertical]:
            if out_path:
                out_dir = Path(out_path).parent
                if not out_dir.exists():
                    output.error(f"输出目录不存在: {out_dir}")
                    output.exit(1)
        
        # 如果启用 --fetch，先尝试获取权威原文
        input_paragraphs = None
        if args.fetch:
            stele_name = _extract_stele_name(args.input)
            output.info(f"尝试获取碑帖 '{stele_name}' 权威原文...")
            input_paragraphs = fetch_stele_text(stele_name, args.source)
            if input_paragraphs:
                output.ok(f"已使用 {len(input_paragraphs)} 段权威原文")
            else:
                output.info("获取失败，将使用原文件内容")
        
        # 验证输入文件（如果使用本地文件）
        if not input_paragraphs:
            validated_input = validate_input_file(args.input, output)
            if not validated_input:
                output.exit(1)
        else:
            validated_input = args.input
        
        if args.dry_run:
            output.info(f"[DRY-RUN] 将处理: {validated_input}")
            output.info(f"[DRY-RUN] 使用字典: {', '.join(validated_dicts)}")
            if args.output_horizontal:
                output.info(f"[DRY-RUN] 输出横版: {args.output_horizontal}")
                output.add_output("horizontal", args.output_horizontal)
            if args.output_vertical:
                output.info(f"[DRY-RUN] 输出竖版: {args.output_vertical}")
                output.add_output("vertical", args.output_vertical)
            output.exit(0)
        
        try:
            run_all(
                validated_input,
                validated_dicts,
                output_horizontal=args.output_horizontal,
                output_vertical=args.output_vertical,
                start_line=args.start_line,
                start_marker=args.start_marker,
                font_size=args.font_size,
                theme=args.theme,
                enable_convert=args.convert,
                annotated_output=args.annotated,
                input_paragraphs=input_paragraphs,
                output=output,  # 传递output处理器
            )
            if args.output_horizontal:
                output.add_output("horizontal", args.output_horizontal)
            if args.output_vertical:
                output.add_output("vertical", args.output_vertical)
            output.ok("处理完成")
        except Exception as e:
            output.error(f"处理失败: {str(e)}")
            output.exit(1)
        
        output.exit(0)


if __name__ == "__main__":
    main()
