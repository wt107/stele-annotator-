# -*- coding: utf-8 -*-
"""
命令行入口模块
"""

import sys
import os
import argparse
import tempfile
from pathlib import Path

from .utils import log_err, log_ok, log_info, log_step
from .network import fetch_stele_text, _extract_stele_name
from .core import build_dict, annotate
from .render import render_html


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
):
    """完整流程：加载字典 → 标注文本 → 输出 HTML"""

    log_step("=" * 50)
    log_step("碑帖学习伴侣 stele-companion 完整流程")
    log_step("=" * 50)

    # Step 1: 标注
    if annotated_output is None:
        annotated_output = tempfile.mktemp(suffix="_annotated.json")

    annotate(
        input_path,
        dict_paths,
        annotated_output,
        start_line=start_line,
        start_marker=start_marker,
        enable_convert=enable_convert,
        input_paragraphs=input_paragraphs,
    )

    # Step 2: 渲染横版
    if output_horizontal:
        render_html(
            annotated_output,
            output_horizontal,
            format_type="horizontal",
            font_size=font_size,
            theme=theme,
        )

    # Step 3: 渲染竖版
    if output_vertical:
        render_html(
            annotated_output,
            output_vertical,
            format_type="vertical",
            font_size=font_size,
            theme=theme,
        )

    log_step("=" * 50)
    log_ok("处理完成！")
    if output_horizontal:
        log_info(f"横版: {output_horizontal}")
    if output_vertical:
        log_info(f"竖版: {output_vertical}")
    log_step("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="碑帖学习伴侣 stele-companion v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用流程:
  1. build-dict : 从标准文档生成字典
  2. annotate   : 文本比对标注
  3. render     : 生成 HTML（横版/竖版）
  4. all        : 一步完成（推荐）

示例（完整流程）:
  stele-companion all 肥致碑.doc \\
      --dict 张迁碑_dict.json \\
      --output-horizontal 肥致碑_横版.html \\
      --output-vertical 肥致碑_竖版.html \\
      --start-marker "从事君之元嗣"

示例（仅建字典）:
  stele-companion build-dict 张迁碑.docx \\
      -o zhangqian_dict.json \\
      --start-marker "君讳迁"

示例（多字典标注）:
  stele-companion annotate 肥致碑.doc \\
      --dict 张迁碑.json,鲜于璜碑.json \\
      -o annotated.json

示例（渲染竖版）:
  stele-companion render \\
      --annotated annotated.json \\
      --format vertical \\
      -o 肥致碑_竖版.html
        """,
    )

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

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ── build-dict ──
    if args.command == "build-dict":
        if not os.path.exists(args.input):
            log_err(f"输入文件不存在: {args.input}")
            sys.exit(1)
        if not args.start_line and not args.start_marker:
            log_err("必须指定 --start-line 或 --start-marker")
            sys.exit(1)
        if args.start_line is not None and args.start_line < 1:
            log_err("--start-line 必须大于 0")
            sys.exit(1)
        build_dict(
            args.input, args.output, args.start_line, args.start_marker, args.variant
        )

    # ── annotate ──
    elif args.command == "annotate":
        dict_paths = [p.strip() for p in args.dict.split(",")]
        dict_paths = [p for p in dict_paths if p]
        if not dict_paths:
            log_err("必须指定有效的字典文件路径")
            sys.exit(1)
        for dp in dict_paths:
            if not os.path.exists(dp):
                log_err(f"字典文件不存在: {dp}")
                sys.exit(1)
        if not os.path.exists(args.input):
            log_err(f"输入文件不存在: {args.input}")
            sys.exit(1)
        annotate(
            args.input,
            dict_paths,
            args.output,
            args.start_line,
            args.start_marker,
            args.convert,
        )

    # ── render ──
    elif args.command == "render":
        if not os.path.exists(args.annotated):
            log_err(f"标注数据文件不存在: {args.annotated}")
            sys.exit(1)
        render_html(
            args.annotated, args.output, args.format, args.font_size, args.theme
        )

    # ── all ──
    elif args.command == "all":
        dict_paths = [p.strip() for p in args.dict.split(",")]
        dict_paths = [p for p in dict_paths if p]
        if not dict_paths:
            log_err("必须指定有效的字典文件路径")
            sys.exit(1)
        for dp in dict_paths:
            if not os.path.exists(dp):
                log_err(f"字典文件不存在: {dp}")
                sys.exit(1)

        # 如果启用 --fetch，先尝试获取权威原文
        input_paragraphs = None
        if args.fetch:
            stele_name = _extract_stele_name(args.input)
            log_info(f"尝试获取碑帖 '{stele_name}' 权威原文...")
            input_paragraphs = fetch_stele_text(stele_name, args.source)
            if input_paragraphs:
                log_ok(f"已使用 {len(input_paragraphs)} 段权威原文")
            else:
                log_info("获取失败，将使用原文件内容")

        if not os.path.exists(args.input) and not input_paragraphs:
            log_err(f"输入文件不存在: {args.input}")
            sys.exit(1)
        if not args.output_horizontal and not args.output_vertical:
            log_err("必须指定 --output-horizontal 和/或 --output-vertical")
            sys.exit(1)

        run_all(
            args.input,
            dict_paths,
            output_horizontal=args.output_horizontal,
            output_vertical=args.output_vertical,
            start_line=args.start_line,
            start_marker=args.start_marker,
            font_size=args.font_size,
            theme=args.theme,
            enable_convert=args.convert,
            annotated_output=args.annotated,
            input_paragraphs=input_paragraphs,
        )


if __name__ == "__main__":
    main()
