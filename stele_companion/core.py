# -*- coding: utf-8 -*-
"""
核心业务模块 - 字典构建和文本标注
"""

import re
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from .utils import (
    PUNCTUATION,
    DICT_COLORS,
    SHARED_COLOR,
    SHARED_COLOR_NAME,
    VARIANT_MAP,
    TRAD_TO_SIMP,
    log_err,
    log_ok,
    log_info,
    log_warn,
    log_step,
    normalize_char,
    _is_cjk_char,
)
from .io import read_input


def build_dict(
    input_path,
    output_path,
    start_line=None,
    start_marker=None,
    variant_base="simplified",
):
    """
    从标准文档构建字典。

    处理流程：
      1. 读取文件（.doc/.docx/.txt）
      2. 定位正文起始（--start-line 或 --start-marker）
      3. 语义段落合并（处理强制换行）
      4. 逐段逐字编号（只给汉字编号，跳过标点/数字）
      5. 输出 JSON 字典（保留原始编号格式：段号-字号）

    字典格式：
      {
        "source": "文件名",
        "variant_base": "simplified",
        "paragraph_count": 15,
        "char_count": 375,
        "unique_chars": 300,
        "mappings": {"字": "1-1", "字": "1-2", ...},
        "variant_pairs": {"简": ["简", "繁"], ...},
        "created": "2026-03-22T18:00:00"
      }
    """
    log_step(f"Phase 1: 构建字典")
    log_info(f"输入文件: {input_path}")

    paragraphs = read_input(input_path)
    log_info(f"读取 {len(paragraphs)} 行")

    # 定位正文起始
    main_start_idx = _find_start_index(paragraphs, start_line, start_marker)
    log_info(f"正文从第 {main_start_idx + 1} 行开始")

    main_paragraphs = paragraphs[main_start_idx:]

    # 语义段落合并
    merged = _merge_paragraphs(main_paragraphs)
    log_info(f"语义合并后: {len(merged)} 段落")

    merged = _clean_line_prefix(merged)
    log_info(f"清理前缀后: {len(merged)} 段落")

    # 逐字编号
    mappings = {}
    variant_pairs = {}
    total_chars = 0

    for para_idx, para in enumerate(merged, 1):
        char_idx = 0
        for char in para:
            if char in PUNCTUATION or char.isspace() or char.isdigit():
                continue
            if not _is_cjk_char(char):
                continue

            # 统一字形
            clean = normalize_char(char, variant_base)
            total_chars += 1
            char_idx += 1
            label = f"{para_idx}-{char_idx}"

            if clean not in mappings:
                mappings[clean] = label
                # 记录简繁对
                if clean in VARIANT_MAP:
                    trad = VARIANT_MAP[clean]
                    variant_pairs[clean] = [clean] + (
                        trad if isinstance(trad, list) else [trad]
                    )
                elif clean in TRAD_TO_SIMP:
                    simp = TRAD_TO_SIMP[clean]
                    if simp in VARIANT_MAP:
                        trad = VARIANT_MAP[simp]
                        variant_pairs[simp] = [simp] + (
                            trad if isinstance(trad, list) else [trad]
                        )

    dict_data = {
        "source": Path(input_path).stem,
        "variant_base": variant_base,
        "paragraph_count": len(merged),
        "char_count": total_chars,
        "unique_chars": len(mappings),
        "mappings": mappings,
        "variant_pairs": variant_pairs,
        "created": datetime.now().isoformat(),
        "version": "1.0",
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dict_data, f, ensure_ascii=False, indent=2)

    log_ok(f"字典已生成: {output_path}")
    log_info(f"  总字数: {total_chars} | 唯一字: {len(mappings)} | 段落: {len(merged)}")
    return dict_data


def _find_start_index(paragraphs, start_line=None, start_marker=None):
    if start_line is not None:
        return max(0, start_line - 1)
    if start_marker:
        for i, p in enumerate(paragraphs):
            if start_marker in p:
                return i
        log_warn(f"未找到标记 '{start_marker}'，从第 1 行开始")
    return 0


def _merge_paragraphs(paragraphs):
    """语义段落合并：句末标点之前被强制换行的段落合并。

    规则：
    1. 当前段落末尾有 END_PUNCT → 停止，不合并下一段
    2. 当前末尾无 END_PUNCT，但下一段是序号段落（如 "1." "2." "10."）→ 停止，不合并
    3. 只有当前末尾无 END_PUNCT 且下一段也不是序号段落时，才合并
    """
    END_PUNCT = "。！？"

    PARA_NUM_PATTERN = re.compile(r"^[\u4e00-\u9fff\u3400-\u4dbf]*\d{1,2}\.")
    result = []
    i = 0
    while i < len(paragraphs):
        merged = paragraphs[i]
        i += 1
        while i < len(paragraphs):
            stripped = merged.rstrip()
            last_char = stripped[-1] if stripped else ""
            next_para = paragraphs[i]
            if PARA_NUM_PATTERN.match(next_para.lstrip()) or last_char in END_PUNCT:
                break
            merged += next_para
            i += 1
        result.append(merged)
    return result


def _clean_line_prefix(paragraphs):
    PREFIX_PATTERN = re.compile(r"\[\s*\d+\s*\]")
    result = []
    for para in paragraphs:
        while PREFIX_PATTERN.search(para):
            para = PREFIX_PATTERN.sub("", para)
        result.append(para)
    return result


def _split_stele_paragraphs(paragraphs):
    """拆分碑文段落：按碑文结构标记拆分单行碑文。

    适用于处理单行碑文文本，根据碑文结构标记拆分段落。
    拆分规则（按碑文结构，不按句号）：
    1. 碑阳/碑阴标题：含"碑阳释文"、"碑阴释文"等结构标记
    2. 赞词标记："其颂曰："+ 赞词内容（到落款之前）
    3. 落款标记：含年号（如"延熹"、"永平"等）的造碑记录

    注意：不按句号拆分！保持正文的完整性。

    Args:
        paragraphs: 段落列表

    Returns:
        拆分后的段落列表
    """
    # 碑文结构标记（通用匹配，适配多种碑帖）
    MARKERS = [
        # 碑阳/碑阴标题（通用模式：碑名+碑阳/碑阴释文+...）
        (r"[^\s]{2,10}碑・碑阳释文[^。]*?(博物馆|收藏|出土)?。?", "stele_title_yang"),
        (r"[^\s]{2,10}碑・碑阴释文[^。]*?\d*字?", "stele_title_yin"),
        # 赞词标记（含后续内容，到落款之前）
        (r"其颂曰：[^延永建和平元康]*?(?=[延永建和平元康]\w{0,2}年)", "eulogy"),
        # 落款标记（常见汉代年号：延熹、永平、建和、平元、康等）
        (r"[延永建和平元康]\w{0,2}年[^。]*?(造|立|刻|建)。?", "signature"),
        # 备用：博物馆收藏信息
        (r"(现|今)?藏[^。]*?博物馆。?", "museum_info"),
    ]

    result = []
    for para in paragraphs:
        # 找到所有标记的位置
        positions = []
        for pattern, label in MARKERS:
            for match in re.finditer(pattern, para):
                positions.append((match.start(), match.end(), label))

        # 按位置排序
        positions.sort(key=lambda x: x[0])

        # 如果没有找到任何标记，整个段落作为一个结果
        if not positions:
            result.append(para)
            continue

        # 按标记拆分
        last_end = 0
        for start, end, label in positions:
            # 标记之前的内容（正文部分）
            if start > last_end:
                before = para[last_end:start]
                if before.strip():
                    result.append(before.strip())

            # 标记本身
            marker_text = para[start:end]
            if marker_text.strip():
                result.append(marker_text.strip())
            last_end = end

        # 最后的内容
        if last_end < len(para):
            after = para[last_end:]
            if after.strip():
                result.append(after.strip())

    return result


def annotate(
    input_path,
    dict_paths,
    output_path,
    start_line=None,
    start_marker=None,
    enable_convert=False,
    input_paragraphs=None,
):
    """
    将碑文文本与字典比对，生成标注数据。

    支持多字典（逗号分隔），每个字典分配独立颜色。

    字典原始编号格式：段号-字号（如 1-1, 5-3）
    标注数据中保留原始编号，不转换为连续编号。

    输出格式：
      {
        "source": "文件名",
        "dicts": [{"source": "字典1", "color": "#b8860b"}, ...],
        "shared_chars": ["字", ...],   # 多字典共有的字
        "paragraphs": [{"para_id": 1, "is_main": true, "chars": [...]}],
        "stats": {"total": 500, "matched": 420, "match_rate": "84.0%"...}
      }
    """
    log_step(f"Phase 2: 文本标注")
    log_info(f"输入文本: {input_path}")
    log_info(f"字典数量: {len(dict_paths)}")

    # 加载多字典
    dicts_data = []
    for dp in dict_paths:
        try:
            with open(dp, "r", encoding="utf-8") as f:
                d = json.load(f)
        except json.JSONDecodeError as e:
            log_err(f"字典文件 JSON 格式错误: {dp}")
            log_err(f"  错误: {e}")
            sys.exit(1)
        except Exception as e:
            log_err(f"读取字典文件失败: {dp}")
            log_err(f"  错误: {e}")
            sys.exit(1)

        if "mappings" not in d:
            log_err(f"字典文件缺少 'mappings' 字段: {dp}")
            sys.exit(1)

        dicts_data.append(d)
        log_info(
            f"  加载字典: {d.get('source', Path(dp).stem)} ({len(d['mappings'])} 字)"
        )

    # 读取文本
    paragraphs = read_input(input_path, input_paragraphs)
    log_info(f"读取 {len(paragraphs)} 行")

    # 定位正文起始
    main_start_idx = _find_start_index(paragraphs, start_line, start_marker)
    if main_start_idx > 0:
        log_info(f"正文从第 {main_start_idx + 1} 行开始，此前内容保留但不标注")

    paragraphs = _clean_line_prefix(paragraphs)
    log_info(f"清理前缀后: {len(paragraphs)} 段落")

    # 语义段落合并
    paragraphs = _merge_paragraphs(paragraphs)
    log_info(f"语义合并后: {len(paragraphs)} 段落")

    # 拆分碑文段落（处理单行文本中的多个结构段）
    paragraphs = _split_stele_paragraphs(paragraphs)
    log_info(f"拆分碑文段落后: {len(paragraphs)} 段落")

    main_start_idx = 0
    log_info(f"正文从第 {main_start_idx + 1} 段开始")

    # 逐段逐字标注
    result_paragraphs = []
    total_chars = 0
    dict_match_counts = [0] * len(dicts_data)
    shared_count = 0

    for para_idx, para in enumerate(paragraphs, 1):
        chars_data = []
        is_main = (para_idx - 1) >= main_start_idx

        for char in para:
            char_info = {"char": char, "matched": False, "labels": []}

            is_valid = not char.isspace() and char not in PUNCTUATION
            if is_valid:
                total_chars += 1

            if is_main and is_valid:
                clean = normalize_char(char) if enable_convert else char
                matched_dicts = []

                for di, dd in enumerate(dicts_data):
                    if clean in dd["mappings"]:
                        matched_dicts.append(di)
                        char_info["labels"].append(
                            {
                                "dict_idx": di,
                                "label": dd["mappings"][clean],
                                "color": DICT_COLORS[di % len(DICT_COLORS)]["fg"],
                            }
                        )

                if matched_dicts:
                    char_info["matched"] = True
                    if len(matched_dicts) > 1:
                        shared_count += 1
                    for di in matched_dicts:
                        dict_match_counts[di] += 1

            chars_data.append(char_info)

        result_paragraphs.append(
            {"para_id": para_idx, "is_main": is_main, "chars": chars_data}
        )

    # 统计多字典共有字（使用集合交集优化性能）
    shared_chars_set = set()
    if len(dicts_data) > 1:
        # 获取所有字典的字符集合
        char_sets = [set(d["mappings"].keys()) for d in dicts_data]
        # 计算交集：出现在多个字典中的字
        shared_chars_set = set.intersection(*char_sets)

    total_matched = sum(dict_match_counts)

    annotated_data = {
        "source": Path(input_path).stem,
        "dict_paths": [str(Path(p).stem) for p in dict_paths],
        "dicts": [
            {
                "source": d.get("source", Path(dp).stem),
                "color": DICT_COLORS[i % len(DICT_COLORS)]["fg"],
                "color_name": DICT_COLORS[i % len(DICT_COLORS)]["name"],
                "matched_count": dict_match_counts[i],
            }
            for i, (d, dp) in enumerate(zip(dicts_data, dict_paths))
        ],
        "shared_chars": list(shared_chars_set),
        "shared_color": SHARED_COLOR,
        "shared_color_name": SHARED_COLOR_NAME,
        "enable_convert": enable_convert,
        "paragraphs": result_paragraphs,
        "stats": {
            "total": total_chars,
            "matched": total_matched,
            "match_rate": f"{total_matched / total_chars * 100:.1f}%"
            if total_chars
            else "0%",
            "shared_count": shared_count,
            "shared_rate": f"{shared_count / total_chars * 100:.1f}%"
            if total_chars
            else "0%",
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(annotated_data, f, ensure_ascii=False, indent=2)

    log_ok(f"标注数据已生成: {output_path}")
    log_info(
        f"  总字数: {total_chars} | 已匹配: {total_matched} ({annotated_data['stats']['match_rate']})"
    )
    if shared_chars_set:
        log_info(
            f"  多字典共有字: {shared_count} ({annotated_data['stats']['shared_rate']})"
        )
    for i, cnt in enumerate(dict_match_counts):
        rate = f"{cnt / total_matched * 100:.1f}%" if total_matched else "0%"
        log_info(
            f"  字典{i + 1} '{dicts_data[i].get('source', '?')}' 匹配: {cnt} ({rate})"
        )

    return annotated_data
