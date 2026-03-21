#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
碑文字标注器 v4.2
支持多文件格式（HTML/TXT/DOC/DOCX）、跨平台、批量断点续处理、灵活字典源

v4.2 新增:
- 段落格式保留：原文段落结构正确显示
- 多字典共有颜色：深紫色(#4a0080)，视觉最突出

v4.1 功能:
- 多字典共有标识：同一字在多个字典中同时出现时，使用第三种特殊颜色标识
- 共有字统计：显示多字典共有字的数量和比例

v4.0 功能:
- 多字典支持：同时对照多个碑文字典，颜色区分
- 简繁转换：支持简体/繁体/对照显示
- 打印优化：多字典紧凑布局、字号适配
- 字典颜色自动分配

v3.2: 双主题支持、打印优化、Google Fonts
v3.1: 安全修复（COM 宏禁用、HTML 注入防护、原子写入）、macOS 适配
"""

import sys
import os
import re
import json
import html as html_mod
import argparse
import platform
import shutil
import tempfile
import colorsys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

# 将 scripts 目录加入路径，以便导入模块
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# 导入简繁转换模块
try:
    from converter import ChineseConverter, to_traditional, to_simplified, get_dual_text
    HAS_CONVERTER = True
except ImportError:
    HAS_CONVERTER = False
    ChineseConverter = None
    to_traditional = lambda x: x
    to_simplified = lambda x: x
    get_dual_text = lambda x: (x, x)


# ============================================================
# 终端颜色
# ============================================================

class C:
    RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    BLUE = '\033[94m'; CYAN = '\033[96m'; BOLD = '\033[1m'; END = '\033[0m'

def log_err(msg):   print(f"{C.RED}  X {msg}{C.END}")
def log_ok(msg):    print(f"{C.GREEN}  OK {msg}{C.END}")
def log_info(msg):  print(f"{C.BLUE}  i {msg}{C.END}")
def log_warn(msg):  print(f"{C.YELLOW}  ! {msg}{C.END}")
def log_step(msg):  print(f"{C.CYAN}>> {msg}{C.END}")


# ============================================================
# 汉字 / 标点 判定
# ============================================================

PUNCTUATION = set(
    # CJK 标点
    '\u3002'  # 。
    '\uff0c'  # ，
    '\u3001'  # 、
    '\uff1a'  # ：
    '\uff1b'  # ；
    '\uff01'  # ！
    '\uff1f'  # ？
    '\u300c\u300d'  # 「」
    '\u300e\u300f'  # 『』
    '\u3008\u3009'  # 〈〉
    '\u201c\u201d'  # ""
    '\u2018\u2019'  # ''
    '\uff08\uff09'  # （）
    '\u300a\u300b'  # 《》
    '\u3010\u3011'  # 【】
    '\u3014\u3015'  # 〔〕
    '\u3016\u3017'  # 〖〗
    '\u3018\u3019'  # 〘〙
    '\uff5b\uff5d'  # ［］
    '\u2014'  # —
    '\u2026'  # …
    '\u00b7'  # ·
    '\uff5e'  # ～
    '\u3000'  # 全角空格
)

def is_punctuation(char):
    if char in PUNCTUATION: return True
    if char in ' \t\r\n': return True
    if char in ',.?!;:\'"()-[]{}<>/\\@#$%^&*_+=~`|': return True
    if '\u0030' <= char <= '\u0039': return True
    return False

def is_hanzi(char):
    cp = ord(char)
    return (
        (0x4E00 <= cp <= 0x9FFF) or (0x3400 <= cp <= 0x4DBF) or
        (0x20000 <= cp <= 0x2A6DF) or (0xF900 <= cp <= 0xFAFF) or
        (0x2F800 <= cp <= 0x2FA1F)
    )


# ============================================================
# 文件读取（统一入口）
# ============================================================

def detect_encoding(file_path):
    if HAS_CHARDET:
        with open(file_path, 'rb') as f:
            raw = f.read(50000)
            result = chardet.detect(raw)
            if result['confidence'] > 0.7:
                return result['encoding']
    for enc in ['utf-8', 'utf-8-sig', 'gbk', 'big5', 'gb18030', 'utf-16']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(10000)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'utf-8'


def read_file_safe(file_path, label="文件"):
    path = Path(file_path)
    if not path.exists():
        log_err(f"{label}不存在: {file_path}"); sys.exit(1)
    encoding = detect_encoding(file_path)
    log_info(f"编码: {encoding}")
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        log_err(f"无法解码: {file_path}"); sys.exit(1)


def read_any_file(file_path, label="文件"):
    """统一文件读取入口：自动识别格式"""
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext in ('.doc', '.docx'):
        from word_reader import WordReader, normalize_word_text
        log_step(f"读取 Word 文件: {path.name}")
        text = WordReader.read(str(path))
        return normalize_word_text(text)
    elif ext in ('.html', '.htm', '.txt'):
        return read_file_safe(file_path, label)
    else:
        log_warn(f"未知格式 {ext}，尝试文本读取")
        return read_file_safe(file_path, label)


# ============================================================
# HTML 解析工具
# ============================================================

def parse_html_chars(content):
    """从 HTML 中提取已有的字-标号映射（支持多种格式，合并所有匹配）"""
    patterns = [
        r'<div\s+class=["\']char-box["\'][^>]*>\s*<span\s+class=["\']char-text["\'][^>]*>([^<]+)</span>\s*<span\s+class=["\']char-idx["\'][^>]*>([^<]+)</span>\s*</div>',
        r'<span\s+class=["\']char-wrap["\'][^>]*>\s*<span\s+class=["\']char(?:\s+\w+)?["\'][^>]*>([^<]+)</span>\s*<span\s+class=["\']label["\'][^>]*>([^<]*)</span>\s*</span>',
        r'<span\s+class=["\']char-container["\'][^>]*>\s*<span\s+class=["\']text["\'][^>]*>([^<]+)</span>\s*<span\s+class=["\']index["\'][^>]*>([^<]+)</span>\s*</span>',
    ]
    all_matches = []
    seen_chars = set()
    for pattern in patterns:
        for c, i in re.findall(pattern, content, re.DOTALL | re.IGNORECASE):
            if c.strip() and c not in seen_chars:
                all_matches.append((c, i))
                seen_chars.add(c)
    return all_matches


# ============================================================
# 字典构建（灵活源）
# ============================================================

def build_dict_from_text(text, source_name="未知碑文"):
    """从纯文本构建字-标号字典

    按「N.」编号段落生成 "段号-字序" 标号；无编号则按自然段落。
    """
    char_first = {}
    char_all = defaultdict(list)

    body_match = re.search(r'(?<!\d)\d{1,3}\.', text)
    if body_match:
        body = text[body_match.start():]
        paragraphs = re.split(r'(?=\d{1,3}\.)', body)
        for para in paragraphs:
            m = re.match(r'(\d{1,3})\.(.*)', para)
            if not m: continue
            line_num = int(m.group(1))
            char_idx = 0
            for ch in m.group(2):
                if is_punctuation(ch): continue
                if is_hanzi(ch):
                    char_idx += 1
                    pos = f"{line_num}-{char_idx}"
                    char_all[ch].append(pos)
                    if ch not in char_first:
                        char_first[ch] = pos
    else:
        paragraphs = re.split(r'\n+', text)
        for line_num, para in enumerate(paragraphs, 1):
            char_idx = 0
            for ch in para:
                if is_punctuation(ch): continue
                if is_hanzi(ch):
                    char_idx += 1
                    pos = f"{line_num}-{char_idx}"
                    char_all[ch].append(pos)
                    if ch not in char_first:
                        char_first[ch] = pos

    return char_first, dict(char_all)


def build_dict_from_html(content, source_name="未知碑文"):
    """从 HTML 文件构建字-标号字典"""
    matches = parse_html_chars(content)
    if not matches: return {}, {}
    char_all = defaultdict(list)
    for char, idx in matches:
        if char.strip() and idx.strip():
            char_all[char].append(idx)
    char_first = {c: idxs[0] for c, idxs in char_all.items()}
    return char_first, dict(char_all)


def build_dict(file_path, source_name=None):
    """构建字典的统一入口（自动识别文件格式）"""
    if source_name is None:
        source_name = Path(file_path).stem

    ext = Path(file_path).suffix.lower()
    if ext in ('.doc', '.docx', '.txt'):
        text = read_any_file(file_path, "字典源文件")
        char_first, char_all = build_dict_from_text(text, source_name)
    elif ext in ('.html', '.htm'):
        content = read_file_safe(file_path, "字典源文件")
        char_first, char_all = build_dict_from_html(content, source_name)
        if not char_first:
            log_warn("HTML 未找到结构化标注，回退纯文本模式")
            char_first, char_all = build_dict_from_text(content, source_name)
    else:
        text = read_any_file(file_path, "字典源文件")
        char_first, char_all = build_dict_from_text(text, source_name)

    return char_first, char_all, source_name


def save_dictionary(char_first, output_json, source_name):
    data = {
        'source': source_name, 'char_count': len(char_first),
        'version': '3.2', 'created': datetime.now().isoformat(),
        'mappings': char_first
    }
    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log_ok(f"字典已保存: {output_json}")
    log_info(f"来源: {source_name}，字数: {len(char_first)}")


def load_dictionary(json_file):
    content = read_file_safe(json_file, "字典文件")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        log_err(f"JSON 错误: 行{e.lineno} 列{e.colno}"); sys.exit(1)
    if 'mappings' not in data:
        log_err("字典缺少 'mappings' 字段"); sys.exit(1)
    return data['mappings'], data.get('source', '未知来源')


# ============================================================
# 多字典支持
# ============================================================

# 预定义字典颜色（用于区分不同字典）
DICT_COLORS = [
    '#b8860b',  # 1. 古铜金
    '#a63d2f',  # 2. 朱砂红
    '#2d5a27',  # 3. 松石绿
    '#1a4a7a',  # 4. 靛青蓝
    '#6b3fa0',  # 5. 紫藤紫
    '#c45c26',  # 6. 赭石橙
    '#2d6b6b',  # 7. 青灰
    '#8b4513',  # 8. 栗壳棕
]

# 多字典共有时的特殊颜色
MULTI_DICT_COLOR = '#4a0080'  # 深紫色 - 多字典共有（最突出）


def format_source_name(source):
    """格式化来源名称，确保书名号正确

    如果已包含《》则保留，没有则添加
    """
    if not source:
        return '《未知来源》'
    source = source.strip()
    # 如果已经包含《和》，则保留原样
    if '《' in source and '》' in source:
        return source
    # 否则添加书名号
    return f'《{source}》'


def get_dict_color(index):
    """获取字典颜色

    Args:
        index: 字典索引（从 0 开始）

    Returns:
        颜色代码（十六进制）
    """
    if index < len(DICT_COLORS):
        return DICT_COLORS[index]
    # 超出预定义范围，使用 HSL 色轮生成
    hue = (index * 137.508) % 360  # 黄金角度
    r, g, b = colorsys.hls_to_rgb(hue / 360, 0.45, 0.55)
    return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'


def load_multiple_dictionaries(dict_files, enable_conversion=False):
    """加载多个字典

    Args:
        dict_files: 字典文件路径列表（逗号分隔的字符串或列表）
        enable_conversion: 是否启用简繁转换匹配

    Returns:
        (dict_list, dict_info_list)
        dict_list: [{'mappings': dict, 'source': str, 'color': str}, ...]
        dict_info_list: [(source_name, color), ...]
    """
    if isinstance(dict_files, str):
        dict_files = [f.strip() for f in dict_files.split(',') if f.strip()]

    dict_list = []
    dict_info_list = []

    for i, dict_file in enumerate(dict_files):
        mappings, source_name = load_dictionary(dict_file)
        color = get_dict_color(i)

        dict_entry = {
            'mappings': mappings,
            'source': source_name,
            'color': color,
            'file': dict_file
        }
        dict_list.append(dict_entry)
        dict_info_list.append((source_name, color))

        log_info(f"字典 {i+1}: {source_name} ({len(mappings)} 字) - 颜色: {color}")

    return dict_list, dict_info_list


def match_char_multi_dict(char, dict_list, enable_conversion=False):
    """在多个字典中匹配字符

    Args:
        char: 要匹配的字符
        dict_list: 字典列表
        enable_conversion: 是否启用简繁转换匹配

    Returns:
        [{'source': str, 'position': str, 'color': str}, ...]
    """
    matches = []

    for d in dict_list:
        mappings = d['mappings']

        # 直接匹配
        if char in mappings:
            matches.append({
                'source': d['source'],
                'position': mappings[char],
                'color': d['color']
            })
            continue

        # 简繁转换匹配
        if enable_conversion and HAS_CONVERTER:
            # 获取字符的简繁变体
            sim, tra = get_dual_text(char)
            if sim in mappings:
                matches.append({
                    'source': d['source'],
                    'position': mappings[sim],
                    'color': d['color']
                })
            elif tra in mappings:
                matches.append({
                    'source': d['source'],
                    'position': mappings[tra],
                    'color': d['color']
                })

    return matches


def merge_multi_dict_stats(total_chars, dict_list, text, enable_conversion=False):
    """计算多字典统计信息

    Args:
        total_chars: 总字数
        dict_list: 字典列表
        text: 文本内容
        enable_conversion: 是否启用简繁转换

    Returns:
        {'total': int, 'dicts': [...], 'combined_matched': int, 'combined_pct': float,
         'shared_matched': int, 'shared_pct': float}  # 新增多字典共有统计
    """
    stats = {
        'total': total_chars,
        'dicts': [],
        'combined_matched': 0,
        'combined_pct': 0.0,
        'shared_matched': 0,  # 多字典共有的字数
        'shared_pct': 0.0
    }

    combined_chars = set()
    char_match_count = {}  # 记录每个字在几个字典中匹配

    for d in dict_list:
        mappings = d['mappings']
        matched = 0

        for char in text:
            if is_hanzi(char):
                matched_flag = False
                if char in mappings:
                    matched_flag = True
                elif enable_conversion and HAS_CONVERTER:
                    sim, tra = get_dual_text(char)
                    if sim in mappings or tra in mappings:
                        matched_flag = True

                if matched_flag:
                    matched += 1
                    combined_chars.add(char)
                    char_match_count[char] = char_match_count.get(char, 0) + 1

        pct = (matched / total_chars * 100) if total_chars > 0 else 0
        stats['dicts'].append({
            'source': d['source'],
            'matched': matched,
            'pct': pct,
            'color': d['color']
        })

    stats['combined_matched'] = len(combined_chars)
    stats['combined_pct'] = (len(combined_chars) / total_chars * 100) if total_chars > 0 else 0

    # 计算多字典共有的字数（出现在2个及以上字典中）
    shared_chars = [c for c, cnt in char_match_count.items() if cnt >= 2]
    stats['shared_matched'] = len(shared_chars)
    stats['shared_pct'] = (len(shared_chars) / total_chars * 100) if total_chars > 0 else 0

    return stats


# ============================================================
# HTML 主题样式（两套完整设计）
# ============================================================

def get_css_classic():
    """经典主题 - 金黄标注（原版优化）

    特点：温暖黄底、古铜金边、传统楷体
    适合：正式文档、传统风格偏好
    """
    return '''
/* ============================================
   碑文标注器 v3.2 - 经典主题
   设计：温暖金黄 · 传统楷体 · 印刷友好
   ============================================ */

:root {
  --gold-deep: #8b6914;
  --gold-main: #b8860b;
  --gold-light: #daa520;
  --gold-bg: #fffde0;
  --gold-glow: #ffe680;
  --ink-dark: #2d2620;
  --ink-medium: #4a4035;
  --ink-light: #6b5f50;
  --paper: #fffef8;
  --border: rgba(184, 134, 11, 0.15);
}

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
}

body {
  font-family: "KaiTi", "標楷体", "FangSong", "SimSun", serif;
  font-size: 18px;
  line-height: 1.8;
  color: var(--ink-dark);
  background: var(--paper);
  padding: 20px;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  padding: 40px 50px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  min-height: calc(100vh - 40px);
}

/* 标题 */
.header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
  position: relative;
}

.header::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--gold-main), transparent);
}

h1 {
  font-family: "KaiTi", "標楷体", serif;
  font-size: 32px;
  font-weight: bold;
  color: var(--ink-dark);
  letter-spacing: 4px;
  margin-bottom: 6px;
}

h1 .subtitle {
  display: block;
  font-size: 16px;
  font-weight: normal;
  color: var(--ink-light);
  letter-spacing: 2px;
  margin-top: 4px;
}

/* 图例 */
.legend {
  display: flex;
  justify-content: center;
  gap: 28px;
  margin: 20px 0;
  font-size: 14px;
  color: var(--ink-medium);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sample {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 4px;
}

.sample.ztb-sample {
  background: var(--gold-glow);
  color: var(--gold-deep);
  border: 1px solid var(--gold-main);
}

.sample.normal-sample {
  background: #f5f5f0;
  color: var(--ink-medium);
  border: 1px solid #ddd;
}

/* 说明 */
.note {
  text-align: center;
  font-size: 13px;
  color: var(--ink-light);
  margin: 20px 0 30px;
  padding: 12px 24px;
  background: #faf8f0;
  border: 1px solid var(--border);
  border-radius: 6px;
  line-height: 1.8;
}

/* 章节 */
.section { margin-bottom: 32px; }

.section-title {
  font-family: "KaiTi", "標楷体", serif;
  font-size: 20px;
  font-weight: bold;
  color: var(--ink-dark);
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
  position: relative;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background: var(--gold-main);
}

.text-content {
  text-align: justify;
  line-height: 3.0;
  padding: 8px 0;
}

.text-content p {
  margin: 0 0 1.5em 0;
  text-indent: 2em;
  line-height: 2.8;
}

.text-content p:last-child {
  margin-bottom: 0;
}

/* 字-标号结构 */
.char-wrap {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  margin: 0 0.5px;
  vertical-align: top;
  line-height: normal;
}

.char {
  display: block;
  font-family: "KaiTi", "標楷体", "FangSong", serif;
  font-size: 24px;
  line-height: 1.6;
  color: var(--ink-dark);
}

.char.ztb {
  color: var(--gold-deep);
  background: linear-gradient(180deg, var(--gold-bg) 0%, var(--gold-glow) 100%);
  border-radius: 3px;
  padding: 0 4px;
  margin: 0 -1px;
  font-weight: bold;
  box-shadow: 0 1px 3px rgba(184, 134, 11, 0.2);
}

.label {
  display: block;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 10px;
  color: var(--gold-main);
  line-height: 1.2;
  margin-top: 2px;
  min-width: 2.2em;
  text-align: center;
}

.punct {
  font-family: "KaiTi", "標楷体", serif;
  font-size: 24px;
  line-height: 1.6;
  color: var(--ink-medium);
  margin: 0 1px;
}

/* 引文 */
.quote-content {
  background: #faf8f0;
  border-left: 3px solid var(--gold-main);
  padding: 14px 20px;
  margin: 12px 0;
  border-radius: 0 6px 6px 0;
}

/* 碑额 */
.stele-title-text {
  font-family: "KaiTi", "標楷体", serif;
  font-size: 22px;
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #faf8f0 0%, #f5f0e0 100%);
  border: 1px solid var(--border);
  border-radius: 6px;
  line-height: 2.2;
  letter-spacing: 4px;
  font-weight: bold;
  color: var(--ink-dark);
}

/* 统计 */
.stats {
  background: #faf8f0;
  padding: 18px 24px;
  margin: 30px 0 20px;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.stats h3 {
  font-family: "KaiTi", "標楷体", serif;
  font-size: 16px;
  color: var(--ink-dark);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.stats ul {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.stats li {
  font-size: 14px;
  color: var(--ink-medium);
}

.stats li strong {
  color: var(--gold-deep);
  font-weight: 600;
}

/* 页脚 */
.footer {
  text-align: center;
  font-size: 12px;
  color: var(--ink-light);
  padding-top: 20px;
  margin-top: 30px;
  border-top: 1px solid var(--border);
}

/* ============================================
   响应式
   ============================================ */
@media screen and (max-width: 600px) {
  body { font-size: 16px; padding: 10px; }
  .container { padding: 20px; }
  h1 { font-size: 26px; }
  .char { font-size: 20px; }
  .label { font-size: 9px; }
  .legend { flex-direction: column; align-items: center; gap: 10px; }
  .stats ul { grid-template-columns: 1fr; }
}

/* ============================================
   打印优化
   ============================================ */
@media print {
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

  html, body { font-size: 12pt; background: #fff !important; padding: 0; }

  .container { max-width: 100%; padding: 0; box-shadow: none; }

  h1 { font-size: 22pt; letter-spacing: 3pt; }
  h1 .subtitle { font-size: 11pt; }

  .legend { display: none; }

  .note { font-size: 10pt; padding: 8pt 16pt; margin-bottom: 16pt; }

  .section { margin-bottom: 16pt; page-break-inside: avoid; }

  .section-title { font-size: 14pt; margin-bottom: 10pt; }

  .text-content { line-height: 2.6; orphans: 3; widows: 3; }

  .char { font-size: 16pt; color: var(--ink-dark) !important; }

  .char.ztb {
    font-size: 16pt;
    color: #8b6914 !important;
    background: #ffe680 !important;
    border-radius: 2pt;
    padding: 1pt 3pt;
    box-shadow: none;
  }

  .label { font-size: 7pt; color: #b8860b !important; }

  .punct { font-size: 16pt; }

  .stele-title-text {
    font-size: 16pt;
    padding: 10pt;
    background: #faf8f0 !important;
    border: 1px solid #ddd;
  }

  .stats {
    background: #faf8f0 !important;
    padding: 12pt 16pt;
    margin: 16pt 0 12pt;
    page-break-inside: avoid;
  }

  .stats h3 { font-size: 12pt; margin-bottom: 8pt; }

  .stats li { font-size: 10pt; }

  .stats li strong { color: #8b6914 !important; }

  .footer { font-size: 9pt; padding-top: 12pt; margin-top: 16pt; }

  @page { size: A4; margin: 2cm 1.8cm; }
}
'''


def get_css_elegant():
    """典雅主题 - 朱砂红标注（新版设计）

    特点：朱砂红、温暖纸色、Google Fonts 书法字体
    适合：艺术展示、印刷出版、视觉冲击
    """
    return '''
/* ============================================
   碑文标注器 v3.2 - 典雅主题
   设计：朱砂红 · 温暖纸色 · 印刷友好
   ============================================ */

:root {
  /* 古墨色系 */
  --ink-deep: #1a1612;
  --ink-dark: #2d2620;
  --ink-medium: #4a4035;
  --ink-light: #6b5f50;

  /* 纸张色系 */
  --paper-warm: #faf6f0;
  --paper-cream: #f5ede0;
  --paper-aged: #ebe3d5;

  /* 朱砂色系 */
  --cinnabar: #a63d2f;
  --cinnabar-light: #c45c4a;
  --cinnabar-bg: #fdf3e8;
  --cinnabar-glow: rgba(166, 61, 47, 0.12);

  /* 辅助 */
  --border-subtle: rgba(42, 35, 28, 0.08);
  --shadow-soft: rgba(26, 22, 18, 0.06);

  /* 尺寸 */
  --char-size: 26px;
  --label-size: 10px;
}

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  font-family: "Noto Serif SC", "Source Han Serif SC", "宋体", "SimSun", serif;
  font-size: 18px;
  line-height: 1.8;
  color: var(--ink-dark);
  background: var(--paper-warm);
  min-height: 100vh;
}

/* 纸张纹理背景 */
body::before {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    radial-gradient(ellipse at 20% 30%, rgba(139, 115, 85, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 70%, rgba(166, 61, 47, 0.02) 0%, transparent 50%);
  pointer-events: none;
  z-index: -1;
}

.container {
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 50px;
  background: #fff;
  box-shadow:
    0 1px 3px var(--shadow-soft),
    0 8px 24px rgba(26, 22, 18, 0.04);
  min-height: 100vh;
}

/* 标题区域 */
.header {
  text-align: center;
  margin-bottom: 36px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--border-subtle);
  position: relative;
}

.header::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--cinnabar), transparent);
}

h1 {
  font-family: "Ma Shan Zheng", "ZCOOL XiaoWei", "標楷体", cursive;
  font-size: 36px;
  font-weight: 400;
  color: var(--ink-deep);
  letter-spacing: 8px;
  margin-bottom: 6px;
  line-height: 1.4;
}

h1 .subtitle {
  font-family: "Noto Serif SC", serif;
  font-size: 18px;
  font-weight: 400;
  color: var(--ink-light);
  letter-spacing: 4px;
  display: block;
  margin-top: 4px;
}

/* 图例 */
.legend {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin: 24px 0;
  font-size: 14px;
  color: var(--ink-medium);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sample {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 4px;
}

.sample.ztb-sample {
  background: var(--cinnabar-bg);
  color: var(--cinnabar);
  border: 1px solid rgba(166, 61, 47, 0.2);
}

.sample.normal-sample {
  background: var(--paper-cream);
  color: var(--ink-medium);
  border: 1px solid var(--border-subtle);
}

/* 说明 */
.note {
  text-align: center;
  font-size: 13px;
  color: var(--ink-light);
  padding: 14px 24px;
  background: var(--paper-cream);
  border-radius: 6px;
  line-height: 1.9;
  margin-bottom: 32px;
}

.note strong {
  color: var(--cinnabar);
  font-weight: 600;
}

/* 章节 */
.section { margin-bottom: 36px; }

.section-title {
  font-family: "Ma Shan Zheng", "ZCOOL XiaoWei", "標楷体", cursive;
  font-size: 22px;
  font-weight: 400;
  color: var(--ink-deep);
  letter-spacing: 4px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border-subtle);
  position: relative;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background: var(--cinnabar);
}

.text-content {
  line-height: 2.8;
  text-align: justify;
  padding: 8px 0;
}

.text-content p {
  margin: 0 0 1.5em 0;
  text-indent: 2em;
  line-height: 2.6;
}

.text-content p:last-child {
  margin-bottom: 0;
}

/* 字-标号结构 */
.char-wrap {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  vertical-align: top;
  margin: 0 1px;
  line-height: normal;
  position: relative;
}

.char {
  display: block;
  font-family: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
  font-size: var(--char-size);
  font-weight: 400;
  line-height: 1.5;
  color: var(--ink-dark);
  transition: color 0.2s ease;
}

.char.ztb {
  color: var(--cinnabar);
  background: linear-gradient(180deg, var(--cinnabar-bg) 0%, #fef9f3 100%);
  border-radius: 4px;
  padding: 2px 4px;
  margin: 0 -1px;
  font-weight: 600;
  box-shadow:
    0 1px 2px var(--cinnabar-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.char.ztb::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(166, 61, 47, 0.3), transparent);
}

.label {
  display: block;
  font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
  font-size: var(--label-size);
  font-weight: 500;
  color: var(--cinnabar-light);
  line-height: 1.2;
  margin-top: 2px;
  min-width: 2.4em;
  text-align: center;
  letter-spacing: -0.3px;
}

.punct {
  font-family: "Noto Serif SC", serif;
  font-size: var(--char-size);
  line-height: 1.5;
  color: var(--ink-medium);
  margin: 0 2px;
}

/* 引文 */
.quote-content {
  background: var(--paper-cream);
  border-left: 3px solid #8b7355;
  padding: 16px 24px;
  margin: 16px 0;
  border-radius: 0 6px 6px 0;
}

/* 碑额 */
.stele-title-text {
  font-family: "Ma Shan Zheng", "ZCOOL XiaoWei", "標楷体", cursive;
  font-size: 24px;
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, var(--paper-cream) 0%, var(--paper-aged) 100%);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  line-height: 2.2;
  letter-spacing: 6px;
  color: var(--ink-deep);
}

/* 统计 */
.stats {
  background: linear-gradient(135deg, var(--paper-cream) 0%, var(--paper-aged) 100%);
  padding: 20px 28px;
  margin: 40px 0 24px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
}

.stats h3 {
  font-family: "Ma Shan Zheng", "ZCOOL XiaoWei", "標楷体", cursive;
  font-size: 18px;
  font-weight: 400;
  color: var(--ink-deep);
  letter-spacing: 2px;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-subtle);
}

.stats ul {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.stats li {
  font-size: 14px;
  color: var(--ink-medium);
  padding: 4px 0;
}

.stats li strong {
  color: var(--cinnabar);
  font-weight: 600;
}

/* 页脚 */
.footer {
  text-align: center;
  font-size: 12px;
  color: var(--ink-light);
  padding-top: 24px;
  margin-top: 40px;
  border-top: 1px solid var(--border-subtle);
}

/* ============================================
   微交互（仅屏幕）
   ============================================ */
@media screen {
  .char-wrap:hover .char.ztb {
    transform: scale(1.05);
    box-shadow:
      0 2px 8px var(--cinnabar-glow),
      inset 0 1px 0 rgba(255, 255, 255, 0.6);
  }

  .char-wrap:hover .label {
    color: var(--cinnabar);
  }
}

/* ============================================
   响应式
   ============================================ */
@media screen and (max-width: 768px) {
  .container { padding: 24px 20px; }
  h1 { font-size: 28px; letter-spacing: 4px; }
  :root { --char-size: 22px; --label-size: 9px; }
  .legend { flex-direction: column; align-items: center; gap: 12px; }
  .stats ul { grid-template-columns: 1fr; }
}

/* ============================================
   打印优化
   ============================================ */
@media print {
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }

  html, body { font-size: 12pt; background: #fff !important; }

  body::before { display: none; }

  .container { max-width: 100%; padding: 0; margin: 0; box-shadow: none; background: #fff !important; }

  h1 { font-size: 24pt; letter-spacing: 6pt; page-break-after: avoid; }
  h1 .subtitle { font-size: 12pt; }

  .header { margin-bottom: 24pt; padding-bottom: 16pt; }

  .legend { display: none; }

  .note { font-size: 10pt; padding: 10pt 16pt; margin-bottom: 20pt; background: #f9f6f0 !important; border: 1px solid #e8e0d0; }

  .section { margin-bottom: 20pt; page-break-inside: avoid; }

  .section-title { font-size: 14pt; margin-bottom: 10pt; padding-bottom: 6pt; }
  .section-title::after { background: #a63d2f !important; }

  .text-content { line-height: 2.4; orphans: 3; widows: 3; }

  .char { font-size: 16pt; color: #2d2620 !important; }

  .char.ztb {
    font-size: 16pt;
    color: #a63d2f !important;
    background: #fef5ed !important;
    border-radius: 2pt;
    padding: 1pt 2pt;
    margin: 0 -0.5pt;
    box-shadow: none;
  }

  .char.ztb::before { display: none; }

  .label { font-size: 7pt; color: #c45c4a !important; margin-top: 1pt; }

  .punct { font-size: 16pt; color: #4a4035 !important; }

  .stele-title-text {
    font-size: 16pt;
    padding: 12pt;
    background: #f9f6f0 !important;
    border: 1px solid #d8d0c0;
    letter-spacing: 4pt;
  }

  .quote-content { background: #faf8f4 !important; border-left: 2pt solid #8b7355; padding: 10pt 16pt; }

  .stats {
    background: #f9f6f0 !important;
    padding: 14pt 18pt;
    margin: 20pt 0 16pt;
    border: 1px solid #e0d8c8;
    page-break-inside: avoid;
  }

  .stats h3 { font-size: 12pt; margin-bottom: 10pt; padding-bottom: 8pt; }
  .stats ul { grid-template-columns: repeat(2, 1fr); gap: 6pt; }
  .stats li { font-size: 10pt; }
  .stats li strong { color: #a63d2f !important; }

  .footer { font-size: 9pt; padding-top: 14pt; margin-top: 20pt; }

  @page {
    size: A4;
    margin: 2cm 1.8cm;
  }
}
'''


def get_google_fonts_link(theme):
    """返回 Google Fonts 链接（仅典雅主题需要）"""
    if theme == 'elegant':
        return '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;600;700&family=ZCOOL+XiaoWei&display=swap" rel="stylesheet">'''
    return ''


def get_css(theme='classic'):
    """根据主题返回 CSS"""
    if theme == 'elegant':
        return get_css_elegant()
    return get_css_classic()


# ============================================================
# HTML 生成
# ============================================================

def generate_char_span(char, char_dict):
    if char in char_dict:
        return f'<span class="char-wrap"><span class="char ztb">{char}</span><span class="label">{char_dict[char]}</span></span>'
    return f'<span class="char-wrap"><span class="char">{char}</span><span class="label"></span></span>'


def generate_char_span_multi(char, dict_list, enable_conversion=False):
    """生成多字典标注的字符 span

    Args:
        char: 字符
        dict_list: 字典列表
        enable_conversion: 是否启用简繁转换

    Returns:
        HTML 字符串
    """
    matches = match_char_multi_dict(char, dict_list, enable_conversion)

    if not matches:
        return f'<span class="char-wrap"><span class="char">{char}</span><span class="labels"></span></span>'

    # 生成标号列表
    labels_html = []
    for m in matches:
        labels_html.append(
            f'<span class="label" style="color:{m["color"]}" title="{m["source"]}">{m["position"]}</span>'
        )

    # 多字典共有时使用特殊颜色，单字典时使用该字典的颜色
    if len(matches) > 1:
        main_color = MULTI_DICT_COLOR
        multi_class = 'multi-dict'
    else:
        main_color = matches[0]['color']
        multi_class = ''

    return f'''<span class="char-wrap multi {multi_class}">
  <span class="char ztb" style="border-color:{main_color}">{char}</span>
  <span class="labels">{''.join(labels_html)}</span>
</span>'''


def text_to_annotated_html_multi(text, dict_list, enable_conversion=False):
    """将纯文本转为带多字典标注的 HTML 片段，保留段落结构"""
    # 先按段落分割
    paragraphs = re.split(r'\n\s*\n', text)

    para_htmls = []
    for para in paragraphs:
        if not para.strip():
            continue

        # 段落内按句子分割
        sentences = re.split(r'([。？！])', para)
        segments = []
        i = 0
        while i < len(sentences):
            seg = sentences[i]
            if i + 1 < len(sentences) and sentences[i + 1] in '。？！':
                seg += sentences[i + 1]
                i += 2
            else:
                i += 1
            if seg.strip():
                segments.append(seg)

        # 处理每个句子
        html_parts = []
        for seg in segments:
            parts = []
            for ch in seg:
                if is_punctuation(ch):
                    parts.append(f'<span class="punct">{ch}</span>')
                elif is_hanzi(ch):
                    parts.append(generate_char_span_multi(ch, dict_list, enable_conversion))
                else:
                    parts.append(ch)
            html_parts.append(''.join(parts))

        # 每个段落用 <p> 包裹
        if html_parts:
            para_htmls.append('<p>' + '\n    '.join(html_parts) + '</p>')

    return '\n    '.join(para_htmls)


def text_to_annotated_html(text, char_dict):
    """将纯文本转为带标注的 HTML 片段，保留段落结构"""
    # 先按段落分割
    paragraphs = re.split(r'\n\s*\n', text)

    para_htmls = []
    for para in paragraphs:
        if not para.strip():
            continue

        # 段落内按句子分割
        sentences = re.split(r'([。？！])', para)
        segments = []
        i = 0
        while i < len(sentences):
            seg = sentences[i]
            if i + 1 < len(sentences) and sentences[i + 1] in '。？！':
                seg += sentences[i + 1]
                i += 2
            else:
                i += 1
            if seg.strip():
                segments.append(seg)

        # 处理每个句子
        html_parts = []
        for seg in segments:
            parts = []
            for ch in seg:
                if is_punctuation(ch):
                    parts.append(f'<span class="punct">{ch}</span>')
                elif is_hanzi(ch):
                    parts.append(generate_char_span(ch, char_dict))
                else:
                    parts.append(ch)
            html_parts.append(''.join(parts))

        # 每个段落用 <p> 包裹
        if html_parts:
            para_htmls.append('<p>' + '\n    '.join(html_parts) + '</p>')

    return '\n    '.join(para_htmls)


def annotate_existing_html(content, char_dict):
    """对已有 HTML 中的 char-wrap 重新标注"""
    total = 0; matched = 0
    def replace_wrap(m):
        nonlocal total, matched
        char = m.group(2); total += 1
        if char in char_dict:
            matched += 1
            return f'<span class="char-wrap"><span class="char ztb">{char}</span><span class="label">{char_dict[char]}</span></span>'
        return f'<span class="char-wrap"><span class="char">{char}</span><span class="label"></span></span>'
    pattern = r'<span class="char-wrap"><span class="char([^"]*)">([^<]+)</span><span class="label">[^<]*</span></span>'
    new_content = re.sub(pattern, replace_wrap, content)
    return new_content, total, matched


def build_full_html(title, text, char_dict, source_name, theme='classic'):
    """从纯文本构建完整的标注 HTML"""
    safe_title = html_mod.escape(title)
    safe_source = html_mod.escape(format_source_name(source_name))
    total_hanzi = matched_hanzi = 0
    for ch in text:
        if is_hanzi(ch):
            total_hanzi += 1
            if ch in char_dict: matched_hanzi += 1

    body_html = text_to_annotated_html(text, char_dict)
    mp = (matched_hanzi / total_hanzi * 100) if total_hanzi > 0 else 0
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 主题相关文字
    if theme == 'elegant':
        highlight_name = '朱砂色'
        theme_name = '典雅版'
    else:
        highlight_name = '黄色'
        theme_name = '经典版'

    google_fonts = get_google_fonts_link(theme)
    css = get_css(theme)

    html = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title} 标注版</title>
{google_fonts}
<style>
{css}
</style>
</head>
<body>
<div class="container">

<header class="header">
  <h1>{safe_title}<span class="subtitle">标注版</span></h1>
</header>

<div class="legend">
  <span class="legend-item">
    <span class="sample ztb-sample">字</span>
    <span>在{safe_source}中出现</span>
  </span>
  <span class="legend-item">
    <span class="sample normal-sample">字</span>
    <span>不在字典中</span>
  </span>
</div>

<div class="note">
  {'<strong>朱砂色</strong>字' if theme == 'elegant' else '黄色字'}为{safe_source}中出现过的字，下方标注对应位置编号。<br>
  标注时间：{now_str}
</div>

<div class="section">
  <h2 class="section-title">碑文正文</h2>
  <div class="text-content">
  {body_html}
  </div>
</div>

<div class="stats">
  <h3>标注统计</h3>
  <ul>
    <li>正文总字数：<strong>{total_hanzi}</strong></li>
    <li>已标注（匹配）：<strong>{matched_hanzi}</strong>（{mp:.1f}%）</li>
    <li>未匹配：<strong>{total_hanzi - matched_hanzi}</strong>（{100-mp:.1f}%）</li>
    <li>字典源：{safe_source}（共 <strong>{len(char_dict)}</strong> 个不同汉字）</li>
  </ul>
</div>

<footer class="footer">
  碑文字标注器 v3.2 · {theme_name} · 生成时间：{now_str}
</footer>

</div>
</body>
</html>'''
    return html, total_hanzi, matched_hanzi


def inject_styles(html_content, theme='classic'):
    if 'char.ztb' not in html_content:
        css = get_css(theme)
        if '</style>' in html_content:
            html_content = html_content.replace('</style>', f'{css}\n</style>')
        elif '</head>' in html_content:
            html_content = html_content.replace('</head>', f'<style>\n{css}\n</style>\n</head>')
    return html_content


def get_css_multi_dict():
    """多字典标注专用 CSS"""
    return '''
/* 多字典标注样式 */
.char-wrap.multi {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  margin: 0 1px;
  vertical-align: top;
  line-height: normal;
}

.char-wrap.multi .char.ztb {
  border-left: 3px solid;
  padding-left: 2px;
  border-radius: 2px;
}

/* 多字典共有字符特殊样式 */
.char-wrap.multi.multi-dict .char.ztb {
  background: linear-gradient(135deg,
    rgba(74, 0, 128, 0.15) 0%,
    rgba(74, 0, 128, 0.08) 100%);
  box-shadow: 0 1px 3px rgba(74, 0, 128, 0.3);
}

.char-wrap.multi .labels {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 2px;
  margin-top: 2px;
}

.char-wrap.multi .label {
  font-size: 8px;
  font-family: "Consolas", monospace;
  line-height: 1.0;
}

/* 多字典图例样式 */
.legend-item.multi {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 4px 8px;
}

.sample.multi {
  width: 24px;
  height: 24px;
  font-size: 14px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

/* 多字典共有图例 */
.sample.multi-shared {
  width: 24px;
  height: 24px;
  font-size: 14px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  background: #4a0080;
  color: #fff;
}

/* 多字典统计样式 */
.stats-multi {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.stats-dict-item {
  padding: 10px;
  background: rgba(0,0,0,0.03);
  border-radius: 4px;
  border-left: 3px solid;
}

.stats-dict-item h4 {
  font-size: 13px;
  margin-bottom: 6px;
}

.stats-dict-item p {
  font-size: 12px;
  color: #666;
  margin: 0;
}

/* 打印优化 */
@media print {
  .char-wrap.multi .labels {
    gap: 1px;
  }

  .char-wrap.multi .label {
    font-size: 6pt;
  }

  .legend-item.multi {
    margin: 2px 6px;
  }

  .sample.multi {
    width: 18px;
    height: 18px;
    font-size: 10pt;
  }

  .sample.multi-shared {
    width: 18px;
    height: 18px;
    font-size: 10pt;
  }

  .char-wrap.multi.multi-dict .char.ztb {
    background: rgba(74, 0, 128, 0.2) !important;
  }
}
'''


def build_full_html_multi(title, text, dict_list, theme='classic', enable_conversion=False, convert_mode='none'):
    """构建多字典标注的完整 HTML

    Args:
        title: 标题
        text: 文本内容
        dict_list: 字典列表
        theme: 主题
        enable_conversion: 是否启用简繁转换匹配
        convert_mode: 转换模式 ('none', 'simplified', 'traditional', 'dual')

    Returns:
        (html, total_hanzi, matched_hanzi)
    """
    safe_title = html_mod.escape(title)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 处理文本转换
    if convert_mode == 'simplified' and HAS_CONVERTER:
        text = to_simplified(text)
    elif convert_mode == 'traditional' and HAS_CONVERTER:
        text = to_traditional(text)

    # 统计
    total_hanzi = sum(1 for ch in text if is_hanzi(ch))

    # 生成正文 HTML
    body_html = text_to_annotated_html_multi(text, dict_list, enable_conversion)

    # 计算统计信息
    stats = merge_multi_dict_stats(total_hanzi, dict_list, text, enable_conversion)

    # 生成图例 - 各字典
    legend_items = []
    for d in dict_list:
        color = d['color']
        source = html_mod.escape(format_source_name(d['source']))
        legend_items.append(f'''<span class="legend-item multi">
    <span class="sample multi" style="background:{color};color:#fff">{source[1] if len(source) > 2 else '字'}</span>
    <span>{source}</span>
  </span>''')

    # 多字典共有图例（只有多字典时才显示）
    if len(dict_list) > 1:
        legend_items.append(f'''<span class="legend-item multi">
    <span class="sample multi-shared">共</span>
    <span>多字典共有</span>
  </span>''')

    # 生成统计信息
    stats_items = []
    for d in stats['dicts']:
        color = d['color']
        source = html_mod.escape(format_source_name(d['source']))
        stats_items.append(f'''<div class="stats-dict-item" style="border-color:{color}">
    <h4 style="color:{color}">{source}</h4>
    <p>匹配: <strong>{d['matched']}</strong> 字 ({d['pct']:.1f}%)</p>
  </div>''')

    google_fonts = get_google_fonts_link(theme)
    css = get_css(theme)
    css_multi = get_css_multi_dict()

    theme_name = {'classic': '经典版', 'elegant': '典雅版'}.get(theme, '经典版')

    html = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title} 标注版</title>
{google_fonts}
<style>
{css}
{css_multi}
</style>
</head>
<body>
<div class="container">

<header class="header">
  <h1>{safe_title}<span class="subtitle">标注版</span></h1>
</header>

<div class="legend">
  {''.join(legend_items)}
</div>

<div class="note">
  已标注 <strong>{stats['combined_matched']}</strong> 个不同汉字（{stats['combined_pct']:.1f}%）
  {'，启用简繁转换匹配' if enable_conversion else ''}
  <br>标注时间：{now_str}
</div>

<div class="section">
  <h2 class="section-title">碑文正文</h2>
  <div class="text-content">
  {body_html}
  </div>
</div>

<div class="stats">
  <h3>标注统计</h3>
  <ul>
    <li>正文总字数：<strong>{total_hanzi}</strong></li>
    <li>多字典共匹配：<strong>{stats['combined_matched']}</strong> 字（{stats['combined_pct']:.1f}%）</li>
    {'<li>多字典共有字：<strong>' + str(stats['shared_matched']) + '</strong> 字（' + f"{stats['shared_pct']:.1f}" + '%）</li>' if len(dict_list) > 1 else ''}
  </ul>
  <div class="stats-multi">
    {''.join(stats_items)}
  </div>
</div>

<footer class="footer">
  碑文字标注器 v4.2 · 多字典版 · {theme_name} · 生成时间：{now_str}
</footer>

</div>
</body>
</html>'''

    # 计算匹配字数（用于返回）
    matched_hanzi = stats['combined_matched']

    return html, total_hanzi, matched_hanzi


# ============================================================
# 三轮校验
# ============================================================

def verify_html(html_content, char_dict):
    errors = {'wrong_mark': [], 'missing_mark': [], 'wrong_label': []}
    pattern = r'<span class="char-wrap"><span class="char(?:\s+ztb)?">([^<]+)</span><span class="label">([^<]*)</span></span>'
    matches = re.findall(pattern, html_content)
    ztb_chars = set(re.findall(r'<span class="char ztb">([^<]+)</span>', html_content))

    for ch in ztb_chars:
        if ch not in char_dict: errors['wrong_mark'].append(ch)
    for ch, label in matches:
        if ch in char_dict and ch not in ztb_chars:
            errors['missing_mark'].append({'char': ch, 'expected': char_dict[ch]})
    for ch, label in matches:
        if ch in char_dict and label and label != char_dict[ch]:
            errors['wrong_label'].append({'char': ch, 'actual': label, 'expected': char_dict[ch]})

    total_errors = sum(len(v) for v in errors.values())
    return errors, total_errors == 0


def print_verify_report(errors, is_valid, title):
    print(f"\n{'='*60}\n三轮逐字校验 - {title}\n{'='*60}")
    rounds = [
        ('wrong_mark', '标记的汉字是否都在字典中', '字不应有标记'),
        ('missing_mark', '字典中的字是否都有标记', '字遗漏标记'),
        ('wrong_label', '标号是否与字典一致', '标号不一致'),
    ]
    for idx, (key, desc, hint) in enumerate(rounds, 1):
        print(f"\n【{idx}】{desc}")
        if errors[key]:
            log_err(f"{len(errors[key])} 个")
            for e in errors[key][:10]:
                if isinstance(e, dict):
                    print(f"      '{e['char']}' {hint}，应为 {e.get('expected','')}")
                else:
                    print(f"      '{e}' {hint}")
            if len(errors[key]) > 10: print(f"      ... 还有 {len(errors[key])-10} 个")
        else:
            log_ok("通过")

    if is_valid:
        print(f"\n{'='*60}"); log_ok("全部检查通过！"); print(f"{'='*60}")
    else:
        log_err(f"共 {sum(len(v) for v in errors.values())} 个问题")


def annotate_file(file_path, char_first, source_name, theme='classic'):
    """单文件标注逻辑（统一入口）"""
    ext = Path(file_path).suffix.lower()
    stem = Path(file_path).stem

    if ext in ('.doc', '.docx', '.txt'):
        text = read_any_file(str(file_path), Path(file_path).name)
        return build_full_html(stem, text, char_first, source_name, theme)
    else:
        content = read_file_safe(str(file_path), Path(file_path).name)
        if parse_html_chars(content):
            result_html, total, matched = annotate_existing_html(content, char_first)
            return inject_styles(result_html, theme), total, matched
        else:
            return build_full_html(stem, content, char_first, source_name, theme)


# ============================================================
# 批量处理（支持 resume）
# ============================================================

BATCH_MANIFEST = '_batch_manifest.json'

def load_manifest(p):
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f: return json.load(f)
    return {'version': '3.2', 'source': '', 'processed': []}

def save_manifest(p, m):
    """原子写入 manifest"""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(p))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def process_batch(input_dir, output_dir, char_first, source_name,
                  recursive=False, resume=False, manifest_path=None, theme='classic'):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = []
    if recursive:
        for ext in ['html','htm','txt','doc','docx']:
            files.extend(input_path.rglob(f'*.{ext}'))
    else:
        for ext in ['html','htm','txt','doc','docx']:
            files.extend(input_path.glob(f'*.{ext}'))

    output_abs = output_path.resolve()
    files = [f for f in files if f.resolve().parent != output_abs]

    if not files:
        log_warn(f"未找到文件: {input_dir}"); return {'success':0,'failed':0,'skipped':0}

    if manifest_path is None:
        manifest_path = str(output_path / BATCH_MANIFEST)
    processed_set = set()
    if resume and os.path.exists(manifest_path):
        m = load_manifest(manifest_path)
        for item in m.get('processed', []):
            if item.get('status') == 'success': processed_set.add(item['input'])
        log_info(f"Resume: 已有 {len(processed_set)} 条记录")

    log_info(f"发现 {len(files)} 个文件")
    results = {'success': 0, 'failed': 0, 'skipped': 0}
    manifest = load_manifest(manifest_path) if resume else {'version':'3.2','source':source_name,'processed':[]}
    manifest['source'] = source_name

    for i, fpath in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {fpath.name}")
        if resume and str(fpath) in processed_set:
            log_info("已处理，跳过"); results['skipped'] += 1; continue

        try:
            log_step("标注中...")
            out_file = output_path / f"{fpath.stem}_标注版.html"
            html, total, matched = annotate_file(str(fpath), char_first, source_name, theme)

            with open(out_file, 'w', encoding='utf-8') as f: f.write(html)
            pct = (matched/total*100) if total > 0 else 0
            log_ok(f"{out_file.name} ({matched}/{total}, {pct:.1f}%)")
            results['success'] += 1
            manifest['processed'].append({
                'input': str(fpath), 'output': str(out_file),
                'total': total, 'matched': matched, 'status': 'success',
                'timestamp': datetime.now().isoformat()
            })
            save_manifest(manifest_path, manifest)
        except Exception as e:
            log_err(f"失败: {e}"); results['failed'] += 1
            manifest['processed'].append({
                'input': str(fpath), 'status': 'failed', 'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            save_manifest(manifest_path, manifest)

    save_manifest(manifest_path, manifest)
    print(f"\n{'='*60}\n批量完成: 成功{results['success']} 失败{results['failed']} 跳过{results['skipped']}\n{'='*60}")
    return results


# ============================================================
# 命令行入口
# ============================================================

def main():
    # 输出编码设置
    if sys.version_info < (3, 7):
        print("错误: 需要 Python 3.7 或更高版本"); sys.exit(1)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
    if sys.platform == 'win32':
        try:
            os.system('')
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description='碑文字标注器 v4.2 — 多字典、共有字标识、段落保留、简繁转换、多主题',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 从任意文件构建字典
  python stele_annotator.py --save-dict 张迁碑.doc 张迁碑.json

  # 单字典标注
  python stele_annotator.py --dict 张迁碑.json 肥致碑.doc -o 肥致碑_标注版.html

  # 多字典标注（逗号分隔）
  python stele_annotator.py --dict 张迁碑.json,曹全碑.json 肥致碑.doc -o 肥致碑_多字典版.html

  # 启用简繁转换匹配
  python stele_annotator.py --dict 张迁碑.json 肥致碑.doc --convert

  # 输出简繁对照
  python stele_annotator.py --dict 张迁碑.json 肥致碑.doc --output-encoding dual

  # 典雅主题
  python stele_annotator.py --dict 张迁碑.json 肥致碑.doc --theme elegant

  # 批量处理
  python stele_annotator.py --dict 张迁碑.json --batch ./input/ --output-dir ./output/

  # 检查环境
  python stele_annotator.py --check

主题:
  classic  - 经典黄（默认）：温暖黄底、古铜金边
  elegant  - 典雅红：朱砂红、温暖纸色

转换选项:
  --convert          启用简繁转换匹配（简体字可匹配繁体字典）
  --output-encoding  输出编码: none(原样)/simplified(简体)/traditional(繁体)/dual(对照)
'''
    )

    parser.add_argument('source', nargs='?', help='字典源文件 (HTML/TXT/DOC/DOCX)')
    parser.add_argument('input', nargs='?', help='待标注文件 (HTML/TXT/DOC/DOCX)')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--dict', dest='dict_file', help='使用字典 JSON 文件（多字典用逗号分隔）')
    parser.add_argument('--save-dict', dest='save_dict', metavar='FILE', help='从源文件构建字典并保存为 JSON')
    parser.add_argument('--batch', metavar='DIR', help='批量处理输入目录')
    parser.add_argument('--output-dir', default='./output/', help='批量处理输出目录')
    parser.add_argument('--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('--resume', action='store_true', help='断点续处理（跳过已成功文件）')
    parser.add_argument('--check', action='store_true', help='检查环境和 Word 读取能力')
    parser.add_argument('--no-verify', action='store_true', help='跳过三轮校验')
    parser.add_argument('--theme', choices=['classic', 'elegant'], default='classic',
                        help='输出主题: classic（经典黄）或 elegant（典雅红）')
    parser.add_argument('--convert', action='store_true',
                        help='启用简繁转换匹配（简体字可匹配繁体字典，反之亦然）')
    parser.add_argument('--output-encoding', choices=['none', 'simplified', 'traditional', 'dual'],
                        default='none', help='输出编码: none(原样)/simplified(简体)/traditional(繁体)/dual(对照)')

    args = parser.parse_args()

    theme_name = {'classic': '经典黄', 'elegant': '典雅红'}
    print(f"\n{C.BOLD}{'='*60}")
    print(f"  碑文字标注器 v4.2")
    print(f"  平台: {platform.system()} {platform.release()}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  主题: {theme_name.get(args.theme, args.theme)}")
    if args.convert:
        print(f"  简繁转换: 启用")
    print(f"{'='*60}{C.END}\n")

    if args.check:
        print("环境检查:")
        avail = None
        try:
            from word_reader import WordReader
            avail = WordReader.check_availability()
        except ImportError:
            avail = {'doc': False, 'docx': False, 'methods': [], 'missing': ['word_reader.py 未找到']}
        print(f"  .doc  支持: {avail['doc']}")
        print(f"  .docx 支持: {avail['docx']}")
        if avail['methods']: print(f"  可用方法: {', '.join(avail['methods'])}")
        if avail['missing']:
            print(f"  缺少依赖:")
            for dep in avail['missing']: print(f"    - {dep}")
        print(f"\n  chardet: {'已安装' if HAS_CHARDET else '未安装（可选）'}")
        print(f"  简繁转换: {'可用 (opencc)' if HAS_CONVERTER else '可用 (内置映射)'}")
        return

    if args.save_dict:
        if not args.source:
            log_err("请指定字典源文件"); sys.exit(1)
        log_step(f"构建字典: {args.source}")
        char_first, char_all, source_name = build_dict(args.source)
        log_ok(f"收录 {len(char_first)} 个不同汉字")
        save_dictionary(char_first, args.save_dict, source_name)
        return

    # 检测是否多字典模式
    is_multi_dict = args.dict_file and ',' in args.dict_file

    if args.batch:
        if not args.source and not args.dict_file:
            log_err("批量处理需要指定源文件或 --dict"); sys.exit(1)

        if is_multi_dict:
            log_step("加载多字典...")
            dict_list, dict_info = load_multiple_dictionaries(args.dict_file, args.convert)
            # 多字典批量处理暂不支持，回退单字典
            log_warn("批量处理暂不支持多字典，使用第一个字典")
            char_first = dict_list[0]['mappings']
            source_name = dict_list[0]['source']
        elif args.dict_file:
            log_step("加载字典...")
            char_first, source_name = load_dictionary(args.dict_file)
        else:
            log_step("构建字典...")
            char_first, _, source_name = build_dict(args.source)
        log_ok(f"字典就绪: {len(char_first)} 个汉字（{source_name}）")

        process_batch(args.batch, args.output_dir, char_first, source_name,
                      recursive=args.recursive, resume=args.resume, theme=args.theme)
        return

    # 参数智能处理：当使用 --dict 时，source 参数作为 input 使用
    if args.dict_file:
        if args.source and not args.input:
            args.input = args.source
            args.source = None
        elif not args.input:
            parser.print_help(); sys.exit(1)

    if not args.input:
        parser.print_help(); sys.exit(1)

    log_step(f"标注: {args.input}")
    output_file = args.output or args.input.rsplit('.', 1)[0] + '_标注版.html'

    # 多字典模式
    if is_multi_dict:
        log_step("加载多字典...")
        dict_list, dict_info = load_multiple_dictionaries(args.dict_file, args.convert)

        # 读取文本 - 根据文件类型处理
        ext = Path(args.input).suffix.lower()
        if ext in ('.doc', '.docx', '.txt'):
            text = read_any_file(args.input, Path(args.input).name)
        elif ext in ('.html', '.htm'):
            # HTML 文件：检查是否已有标注结构
            content = read_file_safe(args.input, Path(args.input).name)
            if parse_html_chars(content):
                # 已有标注结构，从 char-wrap 中提取纯文本
                log_info("检测到已有标注结构，提取文字重新标注...")
                # 提取所有 char class 中的汉字
                char_matches = re.findall(r'<span class="char(?:\s+ztb)?">([^<]+)</span>', content)
                text = ''.join(char_matches)
                if not text:
                    # 回退：提取所有汉字
                    text = ''.join(re.findall(r'[\u4e00-\u9fff]', content))
            else:
                # 无标注结构，提取 body 内容或所有汉字
                body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
                if body_match:
                    body_content = body_match.group(1)
                    # 移除 script 和 style 标签及其内容
                    body_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', body_content, flags=re.DOTALL | re.IGNORECASE)
                    # 提取汉字
                    text = ''.join(re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', body_content))
                else:
                    text = ''.join(re.findall(r'[\u4e00-\u9fff]', content))
        else:
            text = read_file_safe(args.input, Path(args.input).name)

        # 构建多字典 HTML
        html, total, matched = build_full_html_multi(
            Path(args.input).stem,
            text,
            dict_list,
            theme=args.theme,
            enable_conversion=args.convert,
            convert_mode=args.output_encoding
        )

    # 单字典模式
    else:
        if args.dict_file:
            log_step("加载字典...")
            char_first, source_name = load_dictionary(args.dict_file)
        else:
            if not args.source:
                log_err("请指定源文件或使用 --dict"); sys.exit(1)
            log_step("构建字典...")
            char_first, _, source_name = build_dict(args.source)

        log_ok(f"字典: {source_name}，{len(char_first)} 个汉字")

        # 单字典支持简繁转换匹配
        if args.convert and HAS_CONVERTER:
            log_info("简繁转换匹配已启用")

        html, total, matched = annotate_file(args.input, char_first, source_name, args.theme)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    pct = (matched/total*100) if total > 0 else 0
    log_ok(f"输出: {output_file} ({matched}/{total}, {pct:.1f}%)")

    if not args.no_verify and not is_multi_dict:
        log_step("三轮校验...")
        errors, is_valid = verify_html(html, char_first)
        print_verify_report(errors, is_valid, source_name)

    print(f"\n{C.GREEN}完成！{C.END}")
    log_info(f"输出: {output_file}")
    log_info(f"主题: {theme_name.get(args.theme, args.theme)}")
    if is_multi_dict:
        log_info(f"字典数: {len(dict_list)}")


if __name__ == '__main__':
    main()
