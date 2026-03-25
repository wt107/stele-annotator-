#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
碑帖学习伴侣 stele-companion v1.0
================================
合并自 stele-annotator (v4.2) 和 stele-vertical-layout (v1.1)

核心功能：
  1. build-dict   - 从标准文档构建字典（保留原始编号）
  2. annotate     - 文本比对标注（多字典彩色对照）
  3. render       - 输出横版/竖版 HTML（支持 A4 打印优化）

输出稳定、格式一致、流程标准化。
"""

import sys
import os
import re
import json
import argparse
import platform
import colorsys
import html as html_mod
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ───────────────────────────────────────────────
# 路径设置
# ───────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# ───────────────────────────────────────────────
# 内置简繁映射表（约500+常用字，摘自 stele-vertical-layout）
# ───────────────────────────────────────────────
VARIANT_MAP = {
    "国": "國",
    "学": "學",
    "后": "後",
    "干": ["乾", "幹", "干"],
    "发": ["發", "髮"],
    "历": ["歷", "曆"],
    "复": ["復", "複", "覆"],
    "里": "裏",
    "面": "麵",
    "台": "臺",
    "云": "雲",
    "系": "係",
    "只": ["隻", "衹"],
    "才": "纔",
    "丑": "醜",
    "出": "齣",
    "斗": "鬥",
    "谷": "穀",
    "划": "劃",
    "几": "幾",
    "价": "價",
    "借": "藉",
    "卷": "捲",
    "克": "剋",
    "夸": "誇",
    "蜡": "蠟",
    "累": "纍",
    "蔑": "衊",
    "签": "籤",
    "纤": ["纖", "縴"],
    "苏": "蘇",
    "坛": "壇",
    "团": "團",
    "向": "嚮",
    "须": ["須", "鬚"],
    "余": "餘",
    "御": "禦",
    "愿": "願",
    "折": "摺",
    "征": "徵",
    "志": "誌",
    "制": "製",
    "致": "緻",
    "钟": "鐘",
    "种": "種",
    "朱": "硃",
    "筑": "築",
    "准": "準",
    "厂": "廠",
    "广": "廣",
    "宁": "寧",
    "摆": "擺",
    "板": "闆",
    "表": "錶",
    "别": "彆",
    "卜": "蔔",
    "布": "佈",
    "沈": "瀋",
    "称": "稱",
    "吃": "呑",
    "仇": "讎",
    "处": "處",
    "触": "觸",
    "辞": "辭",
    "呆": "獃",
    "担": "擔",
    "当": "當",
    "党": "黨",
    "调": "調",
    "丢": "丟",
    "东": "東",
    "动": "動",
    "冻": "凍",
    "范": "範",
    "丰": "豐",
    "佛": "彿",
    "夫": "伕",
    "父": "爺",
    "妇": "婦",
    "复": "複",
    "盖": "蓋",
    "干": "乾",
    "赶": "趕",
    "个": "個",
    "巩": "鞏",
    "勾": "鉤",
    "构": "構",
    "购": "購",
    "谷": "穀",
    "顾": "顧",
    "刮": "颳",
    "关": "關",
    "观": "觀",
    "冠": "冠",
    "馆": "館",
    "广": "廣",
    "归": "歸",
    "龟": "龜",
    "柜": "櫃",
    "汉": "漢",
    "号": "號",
    "合": "閤",
    "轰": "轟",
    "后": "後",
    "胡": "鬍",
    "壶": "壺",
    "划": "劃",
    "怀": "懷",
    "坏": "壞",
    "欢": "歡",
    "环": "環",
    "还": "還",
    "会": "會",
    "伙": "夥",
    "获": "獲",
    "击": "擊",
    "机": "機",
    "积": "積",
    "极": "極",
    "几": "幾",
    "夹": "夾",
    "简": "簡",
    "见": "見",
    "将": "將",
    "节": "節",
    "尽": ["儘", "盡"],
    "进": "進",
    "京": "亰",
    "径": "徑",
    "举": "擧",
    "据": "據",
    "卷": "捲",
    "开": "開",
    "克": "剋",
    "夸": "誇",
    "块": "塊",
    "亏": "虧",
    "困": "睏",
    "腊": "臘",
    "蜡": "蠟",
    "来": "來",
    "兰": "蘭",
    "拦": "攔",
    "栏": "欄",
    "烂": "爛",
    "累": "纍",
    "垒": "壘",
    "里": "裏",
    "礼": "禮",
    "丽": "麗",
    "厉": "厲",
    "励": "勵",
    "离": "離",
    "了": "瞭",
    "俩": "倆",
    "炼": "煉",
    "练": "練",
    "粮": "糧",
    "疗": "療",
    "辽": "遼",
    "猎": "獵",
    "临": "臨",
    "邻": "鄰",
    "岭": "嶺",
    "庐": "廬",
    "芦": "蘆",
    "炉": "爐",
    "陆": "陸",
    "驴": "驢",
    "乱": "亂",
    "么": "麼",
    "霉": "黴",
    "蒙": ["矇", "濛", "懞"],
    "梦": "夢",
    "弥": ["彌", "瀰"],
    "面": "麵",
    "庙": "廟",
    "没": "沒",
    "亩": "畝",
    "恼": "惱",
    "脑": "腦",
    "拟": "擬",
    "酿": "釀",
    "疟": "瘧",
    "盘": "盤",
    "辟": "闢",
    "苹": "蘋",
    "凭": "憑",
    "扑": "撲",
    "仆": "僕",
    "朴": "樸",
    "气": "氣",
    "千": ["韆", "千"],
    "牵": "牽",
    "签": "籤",
    "纤": ["纖", "縴"],
    "窍": "竅",
    "窃": "竊",
    "寝": "寢",
    "庆": "慶",
    "琼": "瓊",
    "秋": ["鞦", "秋"],
    "曲": "麯",
    "权": "權",
    "劝": "勸",
    "确": "確",
    "让": "讓",
    "扰": "擾",
    "热": "熱",
    "认": "認",
    "洒": "灑",
    "伞": "傘",
    "丧": "喪",
    "扫": "掃",
    "涩": "澀",
    "杀": "殺",
    "晒": "曬",
    "伤": "傷",
    "舍": "捨",
    "沈": "瀋",
    "声": "聲",
    "胜": "勝",
    "湿": "濕",
    "实": "實",
    "适": "適",
    "势": "勢",
    "兽": "獸",
    "书": "書",
    "术": "術",
    "树": "樹",
    "帅": "帥",
    "松": "鬆",
    "苏": "蘇",
    "虽": "雖然",
    "随": "隨",
    "孙": "孫",
    "塔": "墖",
    "态": "態",
    "坛": ["壇", "罈"],
    "叹": "嘆",
    "誊": "謄",
    "体": "體",
    "条": "條",
    "听": "聽",
    "厅": "廳",
    "头": "頭",
    "图": "圖",
    "涂": "塗",
    "团": ["團", "糰"],
    "椭": "橢",
    "洼": "窪",
    "袜": "襪",
    "弯": "彎",
    "万": "萬",
    "网": "網",
    "为": "為",
    "韦": "韋",
    "围": "圍",
    "卫": "衛",
    "稳": "穩",
    "务": "務",
    "雾": "霧",
    "牺": "犧",
    "习": "習",
    "系": ["係", "繫"],
    "戏": "戲",
    "虾": "蝦",
    "吓": "嚇",
    "咸": "鹹",
    "显": "顯",
    "宪": "憲",
    "县": "縣",
    "向": "嚮",
    "响": "響",
    "乡": "鄉",
    "协": "協",
    "写": "寫",
    "泻": "瀉",
    "亵": "褻",
    "衅": "釁",
    "兴": "興",
    "须": ["須", "鬚"],
    "悬": "懸",
    "选": "選",
    "旋": "鏇",
    "压": "壓",
    "盐": "鹽",
    "阳": "陽",
    "养": "養",
    "样": "樣",
    "钥": "鑰",
    "药": "藥",
    "爷": "爺",
    "叶": "葉",
    "医": "醫",
    "亿": "億",
    "忆": "憶",
    "应": "應",
    "尤": "尢",
    "邮": "郵",
    "余": "餘",
    "鱼": "魚",
    "与": "與",
    "云": "雲",
    "运": "運",
    "酝": "醖",
    "杂": "雜",
    "脏": ["臟", "髒"],
    "枣": "棗",
    "灶": "竈",
    "斋": "齋",
    "毡": "氈",
    "战": "戰",
    "赵": "趙",
    "折": "摺",
    "这": "這",
    "征": "徵",
    "证": "證",
    "只": ["隻", "衹"],
    "致": "緻",
    "制": "製",
    "钟": ["鐘", "鍾"],
    "肿": "腫",
    "竹": "笁",
    "众": "眾",
    "昼": "晝",
    "朱": "硃",
    "筑": "築",
    "庄": "莊",
    "妆": "妝",
    "装": "裝",
    "壮": "壯",
    "状": "狀",
    "准": "準",
    "浊": "濁",
    "总": "總",
    "钻": "鑽",
    # 碑刻常用字
    "讳": "諱",
    "迁": "遷",
    "阳": "陽",
    "陈": "陳",
    "留": "畄",
    "县": "縣",
    "君": "君",
    "公": "公",
    "方": "方",
    "人": "人",
    "世": "世",
    "有": "有",
    "功": "功",
    "绩": "績",
    "统": "統",
    "继": "繼",
    "荒": "荒",
    "忽": "忽",
    "阐": "闡",
    "儒": "儒",
    "墨": "墨",
    "之": "之",
    "先": "先",
    "故": "故",
    "城": "城",
    "长": "長",
    "吏": "吏",
    "印": "印",
    "绶": "綬",
    "建": "建",
    "和": "和",
    "中": "中",
    "举": "舉",
    "孝": "孝",
    "廉": "廉",
    "除": "除",
    "郎": "郎",
    "谒": "謁",
    "者": "者",
    "河": "河",
    "东": "東",
    "太": "太",
    "守": "守",
    "都": "都",
    "亭": "亭",
    "侯": "侯",
}

TRAD_TO_SIMP = {}
for simp, trads in VARIANT_MAP.items():
    if isinstance(trads, str):
        TRAD_TO_SIMP[trads] = simp
    else:
        for t in trads:
            TRAD_TO_SIMP[t] = simp

# 需要旋转的标点符号（竖排时横向显示）
ROTATE_CHARS = set("《》<>()（）【】[]{}")

# 标点符号集合
PUNCTUATION = set(
    '，。、；：！？""'
    "（）【】《》〈〉…—～·「」『』"
    "\u3002\uff0c\uff0e\uff1a\uff1b\uff01\uff1f"
    "\u300c\u300d\u300e\u300f\u3010\u3011"
)

# ───────────────────────────────────────────────
# 多字典颜色分配（取自 stele-annotator v4.0）
# ───────────────────────────────────────────────
DICT_COLORS = [
    {"fg": "#b8860b", "name": "古铜金"},
    {"fg": "#a63d2f", "name": "朱砂红"},
    {"fg": "#2d5a27", "name": "松石绿"},
    {"fg": "#1a4a7a", "name": "靛青蓝"},
    {"fg": "#6a3d7a", "name": "紫藤色"},
    {"fg": "#7a4a1a", "name": "赭石色"},
    {"fg": "#1a6a5a", "name": "翠玉色"},
    {"fg": "#5a1a4a", "name": "酱紫色"},
]

# 深紫色：多字典共有字
SHARED_COLOR = "#4a0080"
SHARED_COLOR_NAME = "深紫色"


# ───────────────────────────────────────────────
# 碑帖原文获取模块
# ───────────────────────────────────────────────
STELE_SOURCES = {
    "张迁碑": [
        {"name": "wikisource", "url": "https://zh.wikisource.org/wiki/張遷碑"},
        {"name": "sohu", "url": "https://www.sohu.com/a/231540642_100106995"},
    ],
    "肥致碑": [
        {"name": "yamoke", "url": "http://www.yamoke.com/a/202210/20774.html"},
        {
            "name": "jiguzuo",
            "url": "https://www.jiguzuo.com/shufa/dong-han-fei-zhi-bei-mo-ta.html",
        },
    ],
    "鲜于璜碑": [
        {"name": "wikisource", "url": "https://zh.wikisource.org/wiki/鮮于璜碑"},
    ],
}


def _extract_stele_name(input_path):
    """从文件名提取碑帖名称"""
    stem = Path(input_path).stem
    # 移除常见后缀和修饰词
    name = re.sub(
        r"[\(（]\d+[\)）]|[一二三四五六七八九十]+版|简体|繁体|竖版|横版|碑阳|碑阴|正文|全文",
        "",
        stem,
    )
    return name.strip()


def _fetch_wikisource(url, stele_name):
    """从维基文库获取碑帖原文"""
    try:
        import requests

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.encoding = "utf-8"
        html = resp.text

        paragraphs = []

        if "張遷碑" in url or "张迁碑" in url:
            # 查找释文区域
            match = re.search(r"釋文[\\s\\S]*?<pre>([\\s\\S]*?)</pre>", html)
            if not match:
                match = re.search(r"碑陽[^<]*?<p>([\\s\\S]*?)</p>", html)
            if match:
                text = match.group(1)
                # 清理标签
                text = re.sub(r"<[^>]+>", "", text)
                text = re.sub(r"\\s+", "\\n", text)
                # 按行分割
                for line in text.split("\\n"):
                    line = line.strip()
                    if line and len(line) > 2:
                        paragraphs.append(line)

        elif "鮮于璜碑" in url:
            match = re.search(r"釋文[\\s\\S]*?<pre>([\\s\\S]*?)</pre>", html)
            if match:
                text = match.group(1)
                text = re.sub(r"<[^>]+>", "", text)
                text = re.sub(r"\\s+", "\\n", text)
                for line in text.split("\\n"):
                    line = line.strip()
                    if line and len(line) > 2:
                        paragraphs.append(line)

        return paragraphs if paragraphs else None

    except Exception as e:
        log_warn(f"从 Wikisource 获取失败: {e}")
        return None


def _fetch_yamoke(url, stele_name):
    """从雅墨客网获取碑帖原文"""
    try:
        import requests

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.encoding = "utf-8"
        html = resp.text

        paragraphs = []

        # 查找释文区域
        patterns = [
            r"释文[\\s\\S]*?<p>([\\s\\S]*?)</p>",
            r"碑刻释文[\\s\\S]*?<p>([\\s\\S]*?)</p>",
            r"【释文】([\\s\\S]*?)</div>",
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                text = match.group(1)
                text = re.sub(r"<[^>]+>", "\\n", text)
                text = re.sub(r"\\n+", "\\n", text)
                for line in text.split("\\n"):
                    line = line.strip()
                    # 过滤行号标记
                    line = re.sub(r"^\\[[\\s\\d]+\\]\\s*", "", line)
                    if line and len(line) > 3:
                        paragraphs.append(line)
                break

        return paragraphs if paragraphs else None

    except Exception as e:
        log_warn(f"从 Yamoke 获取失败: {e}")
        return None


def fetch_stele_text(stele_name, source="auto"):
    """获取碑帖权威原文

    Args:
        stele_name: 碑帖名称
        source: 数据源 ('wikisource', 'yamoke', 'auto')

    Returns:
        段落列表，获取失败返回None
    """
    # 精确匹配
    sources = STELE_SOURCES.get(stele_name, [])

    if not sources:
        # 模糊匹配
        for key, vals in STELE_SOURCES.items():
            if key in stele_name or stele_name in key:
                sources = vals
                break

    if not sources:
        log_warn(f"未找到碑帖 '{stele_name}' 的数据源")
        return None

    # 按指定源过滤
    if source != "auto":
        sources = [s for s in sources if s["name"] == source]

    for src in sources:
        log_info(f"尝试从 {src['name']} 获取碑帖原文...")

        if src["name"] == "wikisource":
            result = _fetch_wikisource(src["url"], stele_name)
        elif src["name"] in ("yamoke", "jiguzuo"):
            result = _fetch_yamoke(src["url"], stele_name)
        else:
            continue

        if result and len(result) > 5:
            log_ok(f"成功获取 {len(result)} 段权威原文")
            return result

    log_warn("所有数据源获取失败")
    return None


# ───────────────────────────────────────────────
# 终端颜色输出
# ───────────────────────────────────────────────
class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def log_err(msg):
    print(f"{C.RED}  X {msg}{C.END}")


def log_ok(msg):
    print(f"{C.GREEN}  OK {msg}{C.END}")


def log_info(msg):
    print(f"{C.BLUE}  i {msg}{C.END}")


def log_warn(msg):
    print(f"{C.YELLOW}  ! {msg}{C.END}")


def log_step(msg):
    print(f"{C.CYAN}>> {msg}{C.END}")


# ───────────────────────────────────────────────
# 简繁转换（内置备用，不依赖 opencc）
# ───────────────────────────────────────────────
def to_traditional(text):
    """简体转繁体（内置映射表）"""
    if not text:
        return text
    result = []
    for char in text:
        if char in VARIANT_MAP:
            trad = VARIANT_MAP[char]
            result.append(trad[0] if isinstance(trad, list) else trad)
        else:
            result.append(char)
    return "".join(result)


def to_simplified(text):
    """繁体转简体（内置映射表）"""
    if not text:
        return text
    result = []
    for char in text:
        result.append(TRAD_TO_SIMP.get(char, char))
    return "".join(result)


def normalize_char(char, target="simplified"):
    """统一字符到目标字形"""
    if not char or char in PUNCTUATION or char.isspace():
        return char
    if target == "simplified":
        return to_simplified(char) if char in TRAD_TO_SIMP else char
    else:
        return to_traditional(char) if char in VARIANT_MAP else char


# ───────────────────────────────────────────────
# 跨平台 Word 读取（取自 stele-annotator word_reader）
# ───────────────────────────────────────────────
def read_input(file_path, paragraphs=None):
    """根据文件扩展名读取输入文件。如果已通过其他方式获取文本（如 --fetch），直接使用。"""
    if paragraphs is not None:
        return paragraphs

    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in (".doc", ".docx"):
        return _read_word(file_path)
    elif ext == ".txt":
        return _read_txt(file_path)
    elif ext == ".json":
        # JSON 字典文件不通过此函数读取
        raise ValueError(f"无法读取 JSON 文件作为文本源: {file_path}")
    else:
        raise ValueError(f"不支持的文件格式: {ext}（支持 .doc/.docx/.txt）")


def _read_txt(file_path):
    """读取 TXT 文件，自动检测编码"""
    try:
        import chardet

        with open(file_path, "rb") as f:
            raw = f.read()
            result = chardet.detect(raw)
            encoding = result["encoding"] or "utf-8"
    except ImportError:
        encoding = "utf-8"

    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        text = f.read()

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [p for p in text.split("\n") if p.strip()]


def _read_word(file_path):
    """跨平台读取 Word 文件"""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".docx":
        return _read_docx(file_path)
    elif ext == ".doc":
        return _read_doc_platform(file_path)
    else:
        raise ValueError(f"不支持的 Word 格式: {ext}")


def _read_docx(file_path):
    """读取 .docx（跨平台）"""
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("请安装 python-docx: pip install python-docx")

    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return paragraphs


def _read_doc_platform(file_path):
    """读取 .doc（平台适配）"""
    if platform.system() == "Windows":
        return _read_doc_win32(file_path)
    else:
        return _read_doc_libreoffice(file_path)


def _read_doc_win32(file_path):
    """Windows: win32com 读取 .doc"""
    try:
        import win32com.client
    except ImportError:
        raise RuntimeError(
            "读取 .doc 需要 pywin32。\n请运行: pip install pywin32\n或改用 .docx 格式"
        )

    abs_path = os.path.abspath(file_path)
    word = None
    doc = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False
        word.AutomationSecurity = 3
        doc = word.Documents.Open(abs_path, ReadOnly=True)
        text = doc.Content.Text
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [p for p in text.split("\n") if p.strip()]
        return paragraphs
    except Exception as e:
        raise RuntimeError(f"读取 .doc 失败: {e}")
    finally:
        if doc:
            try:
                doc.Close(False)
            except Exception:
                pass
        if word:
            try:
                word.Quit()
            except Exception:
                pass


def _read_doc_libreoffice(file_path):
    """macOS/Linux: LibreOffice 读取 .doc"""
    import subprocess, tempfile, shutil

    lo_cmd = None
    for cmd_name in ["libreoffice", "soffice"]:
        if shutil.which(cmd_name):
            lo_cmd = cmd_name
            break
    if not lo_cmd:
        raise RuntimeError(
            "读取 .doc 需要 LibreOffice。\n请安装: https://www.libreoffice.org/"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            lo_cmd,
            "--headless",
            "--convert-to",
            "txt:Text",
            "--outdir",
            tmpdir,
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice 转换失败: {result.stderr}")

        txt_name = Path(file_path).stem + ".txt"
        txt_path = os.path.join(tmpdir, txt_name)
        if not os.path.exists(txt_path):
            raise RuntimeError(f"LibreOffice 转换输出文件未生成")

        with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return [p for p in text.split("\n") if p.strip()]


# ───────────────────────────────────────────────
# Phase 1: 字典构建
# ───────────────────────────────────────────────
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
            if not ("\u4e00" <= char <= "\u9fff"):
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
    import re

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
    import re

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
    1. 碑阳标题："鲜于璜碑・碑阳释文..."博物馆。"
    2. 碑阴标题："鲜于璜碑・碑阴释文..."字"
    3. 赞词标记："其颂曰："+ 赞词内容（到落款之前）
    4. 落款标记："延熹八年..."造。"

    注意：不按句号拆分！保持正文的完整性。

    Args:
        paragraphs: 段落列表

    Returns:
        拆分后的段落列表
    """
    import re

    # 碑文结构标记（精确匹配，不拆分正文）
    MARKERS = [
        # 碑阳标题（完整匹配）
        (r"鲜于璜碑・碑阳释文[^。]*?博物馆。", "stele_title_yang"),
        # 碑阴标题（完整匹配）
        (r"鲜于璜碑・碑阴释文[^。]*?\d+字", "stele_title_yin"),
        # 赞词标记（含后续内容，到落款之前）
        (r"其颂曰：[^延]*?(?=延熹)", "eulogy"),
        # 落款标记（完整句子）
        (r"延熹八年[^。]*?造。", "signature"),
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


# ───────────────────────────────────────────────
# Phase 2: 文本标注
# ───────────────────────────────────────────────
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

    # 统计多字典共有字
    shared_chars_set = set()
    if len(dicts_data) > 1:
        for dd in dicts_data:
            for char in dd["mappings"]:
                appearances = sum(1 for d in dicts_data if char in d["mappings"])
                if appearances > 1:
                    shared_chars_set.add(char)

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


# ───────────────────────────────────────────────
# Phase 3: HTML 渲染
# ───────────────────────────────────────────────
def render_html(
    annotated_path,
    output_path,
    format_type="horizontal",
    font_size="medium",
    theme="classic",
):
    """
    将标注数据渲染为 HTML。

    format_type:
      - horizontal : 横版（现代阅读顺序，左→右，A4纵向）
      - vertical    : 竖版（古文阅读顺序，上→下，右→左，A4横向）

    font_size:
      - small  : 22px（紧凑打印）
      - medium : 28px（默认，学习友好）
      - large  : 34px（大字体，老年友好）

    theme:
      - classic : 金色系（#fff3a0 淡黄底）
      - elegant : 红色系（#fde8e8 淡红底）
    """

    log_step(f"Phase 3: 渲染 HTML ({format_type})")
    log_info(f"加载标注数据: {annotated_path}")

    try:
        with open(annotated_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log_err(f"标注文件 JSON 格式错误: {annotated_path}")
        log_err(f"  错误: {e}")
        sys.exit(1)
    except Exception as e:
        log_err(f"读取标注文件失败: {annotated_path}")
        log_err(f"  错误: {e}")
        sys.exit(1)

    if format_type == "horizontal":
        html = _render_horizontal(data, font_size, theme)
    else:
        html = _render_vertical(data, font_size, theme)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    log_ok(f"HTML 已生成: {output_path}")
    if format_type == "horizontal":
        log_info(f"提示: 浏览器打开后，Ctrl+P 打印 → A4 纵向，勾选「背景图形」")
    else:
        log_info(f"提示: 浏览器打开后，Ctrl+P 打印 → A4 横向，勾选「背景图形」")


# ───────────────────────────────────────────────
# 主题颜色
# ───────────────────────────────────────────────
THEME_COLORS = {
    "classic": {
        "matched_bg": "#fff3a0",
        "matched_bg_print": "#ffd43b",
        "matched_bg_end": "#ffe066",
        "char_id_color": "#228be6",
    },
    "elegant": {
        "matched_bg": "#fde8e8",
        "matched_bg_print": "#faa0a0",
        "matched_bg_end": "#fccfcf",
        "char_id_color": "#a63d2f",
    },
}


def _font_size_css(size):
    s = {"small": "22px", "medium": "28px", "large": "34px"}.get(size, "28px")
    # line-height = 字宽(~font_size×0.96) + 字间距(1.0mm for s/m, 1.2mm for l)
    lh = {"small": "7.2mm", "medium": "8.5mm", "large": "10.2mm"}.get(size, "8.5mm")
    cid = {"small": "7px", "medium": "8px", "large": "10px"}.get(size, "8px")
    return s, lh, cid


# ───────────────────────────────────────────────
# 横版渲染
# ───────────────────────────────────────────────
def _render_horizontal(data, font_size="medium", theme="classic"):
    """渲染横版 HTML（现代阅读顺序）"""

    fs, lh, cid = _font_size_css(font_size)
    tc = THEME_COLORS.get(theme, THEME_COLORS["classic"])
    pg_color = tc["matched_bg_print"]

    # CSS
    css = f"""
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: "SimSun", "Songti SC", "Noto Serif CJK SC", serif;
        background: #f5f5f5;
        padding: 20px;
    }}
    .page {{
        width: 210mm;
        min-height: 297mm;
        padding: 15mm 15mm;
        margin: 0 auto 20px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        page-break-after: always;
    }}
    .page:last-child {{ page-break-after: avoid; }}
    .page-header {{
        height: 10mm;
        margin-bottom: 4mm;
        text-align: center;
        border-bottom: 0.5px solid #ddd;
        font-size: 9pt;
        color: #666;
        line-height: 10mm;
    }}
    .content {{
        display: flex;
        flex-wrap: wrap;
        gap: 5.0mm 1.0mm;
        align-content: flex-start;
        padding-bottom: 8mm;
    }}
    .char-wrap {{
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        vertical-align: top;
    }}
    .char, .punct {{
        font-size: {fs};
        line-height: {lh};
    }}
    .char.matched {{
        padding: 0 2px;
        margin: 0 -2px;
        background: linear-gradient(to bottom, {tc["matched_bg_end"]}, {tc["matched_bg"]});
        border-radius: 2px;
    }}
    .char.ztb {{
        /* 在字典中找到的字 */
        padding: 0 2px;
        margin: 0 -2px;
    }}
    .label {{
        font-size: {cid};
        color: {tc["char_id_color"]};
        font-family: Arial, sans-serif;
        white-space: nowrap;
        line-height: 1;
        pointer-events: none;
        margin-top: -2px;
    }}
    .punct {{
        color: #555;
    }}
    .char-id {{ display: none; }}
    .para-break {{
        width: 100%;
        height: 6mm;
        border-bottom: 0.5px dashed #ccc;
        margin: 2mm 0;
    }}
    .section-break {{
        width: 100%;
        border-bottom: 1px solid #bbb;
        padding: 4mm 0 2mm 0;
        margin-bottom: 3mm;
        text-align: center;
    }}
    .section-name {{
        font-size: 18pt;
        letter-spacing: 3px;
        color: #444;
    }}

    .stats {{
        max-width: 210mm;
        margin: 20px auto;
        padding: 15px;
        background: white;
        font-size: 10pt;
        color: #666;
        border-radius: 4px;
    }}
    .legend {{
        max-width: 210mm;
        margin: 10px auto;
        padding: 10px 15px;
        background: white;
        font-size: 9pt;
        color: #555;
        border-radius: 4px;
    }}
    .legend-item {{
        display: inline-block;
        margin-right: 16px;
    }}
    .legend-dot {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 2px;
        margin-right: 4px;
        vertical-align: middle;
    }}
    @media print {{
        @page {{ size: A4 portrait; margin: 5mm; }}
        body {{ background: white; padding: 0; }}
        .page {{ margin: 0; box-shadow: none; padding: 15mm 15mm; page-break-after: always; }}
        .page:last-child {{ page-break-after: avoid; }}
        .content {{ padding-bottom: 6mm; }}
        .char-wrap {{ overflow: visible; }}
        .stats, .legend {{ display: none; }}
        .para-break {{ border-bottom-color: #999; }}
        .char.matched {{
            background: {pg_color} !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
    }}
    """

    # 生成图例
    legend_html = '<div class="legend"><b>图例：</b>'
    for di in data.get("dicts", []):
        source_name = html_mod.escape(di.get("source", "字典"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{di["color"]};color:{di["color"]}"> </span>'
            f"{source_name}（{di.get('matched_count', 0)}字）"
            f"</span>"
        )
    if data.get("shared_chars"):
        shared_color_name = html_mod.escape(data.get("shared_color_name", "深紫色"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{data["shared_color"]};color:{data["shared_color"]}"> </span>'
            f"{shared_color_name}（{data['stats'].get('shared_count', 0)}字，共有字）"
            f"</span>"
        )
    legend_html += "</div>"

    # 生成正文
    content_parts = []
    for pi, para in enumerate(data["paragraphs"]):
        is_main = para.get("is_main", True)

        # 非主段（标题/开头）→ 居中大字 section-break + 正文开始时的分隔
        if not is_main:
            para_text = "".join(
                html_mod.escape(ci["char"])
                for ci in para["chars"]
                if not ci["char"].isspace() and ci["char"] not in PUNCTUATION
            )
            content_parts.append(
                f'<div class="section-break">'
                f'<span class="section-name">{para_text}</span>'
                f"</div>"
            )
            # 标题和正文之间加分隔
            content_parts.append('<div class="para-break"></div>')
            continue

        # 正文段落：inline 渲染
        for ci in para["chars"]:
            char = ci["char"]
            if char.isspace():
                continue

            if char in PUNCTUATION:
                content_parts.append(
                    f'<span class="punct">{html_mod.escape(char)}</span>'
                )
                continue

            if ci["matched"]:
                labels = ci.get("labels", [])
                if labels:
                    primary_color = labels[0]["color"]
                    label_text = " ".join(lb["label"] for lb in labels)
                    is_shared = len(labels) > 1
                    color_style = (
                        f"background:{data['shared_color']}"
                        if is_shared
                        else f"background: linear-gradient(to bottom, {primary_color}22, {primary_color}11)"
                    )
                    char_cls = "char matched"
                    content_parts.append(
                        f'<span class="char-wrap">'
                        f'<span class="{char_cls}" style="{color_style}">{html_mod.escape(char)}</span>'
                        f'<span class="label" style="color:{primary_color if not is_shared else data["shared_color"]}">{label_text}</span>'
                        f"</span>"
                    )
                else:
                    content_parts.append(
                        f'<span class="char matched">{html_mod.escape(char)}</span>'
                    )
            else:
                content_parts.append(
                    f'<span class="char">{html_mod.escape(char)}</span>'
                )

        # 段落分隔
        content_parts.append('<div class="para-break"></div>')

    content_html = "".join(content_parts)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{html_mod.escape(data["source"])} - 横版标注</title>
<style>{css}</style>
</head>
<body>
{legend_html}
<div class="page">
<div class="page-header">{html_mod.escape(data["source"])}</div>
<div class="content">{content_html}</div>
</div>
<div class="stats">
<p><b>来源：</b>{html_mod.escape(data["source"])} | <b>字典：</b>{", ".join(html_mod.escape(d.get("source", p)) for d, p in zip(data.get("dicts", []), data.get("dict_paths", [])))}</p>
<p><b>总字数：</b>{data["stats"]["total"]} | <b>已匹配：</b>{data["stats"]["matched"]} ({data["stats"]["match_rate"]}){f" | <b>共有字：</b>{data["stats"]["shared_count"]} ({data["stats"]["shared_rate"]})" if data.get("shared_chars") else ""}</p>
</div>
</body>
</html>"""
    return html


# ───────────────────────────────────────────────
# 竖版渲染
# ───────────────────────────────────────────────
def _render_vertical(data, font_size="medium", theme="classic"):
    """渲染竖版 HTML（古文阅读顺序）"""

    fs, lh, cid = _font_size_css(font_size)
    tc = THEME_COLORS.get(theme, THEME_COLORS["classic"])
    pg_color = tc["matched_bg_print"]

    css = f"""
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: "SimSun", "Songti SC", "Noto Serif CJK SC", serif;
        background: #f5f5f5;
        padding: 15px;
    }}
    .page {{
        width: 297mm;
        min-height: 200mm;
        padding: 10mm 4mm 10mm 4mm;
        margin: 0 auto 20px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        page-break-after: always;
    }}
    .page:last-child {{ page-break-after: avoid; }}
    .page-header {{
        display: none;
    }}
    .vertical-content {{
        display: flex;
        flex-direction: row-reverse;
        justify-content: flex-start;
        gap: 6.0mm;
    }}
    .col {{
        display: inline-flex;
        flex-direction: column;
        gap: 1.0mm;
        align-items: center;
    }}
    .char-wrap {{
        display: inline;
        position: relative;
    }}
    .char, .punct {{
        font-size: {fs};
        line-height: {lh};
        display: inline;
    }}
    .char.matched {{
        padding: 0 2px;
        margin: 0 -2px;
        background: linear-gradient(to bottom, {tc["matched_bg_end"]}, {tc["matched_bg"]});
        border-radius: 2px;
    }}
    .char.ztb {{}}
    .label {{
        position: absolute;
        font-size: {cid};
        color: {tc["char_id_color"]};
        font-family: Arial, sans-serif;
        bottom: -3px;
        left: 50%;
        transform: translateX(-50%);
        white-space: nowrap;
        line-height: 1;
        pointer-events: none;
    }}
    .punct {{
        color: #555;
        writing-mode: vertical-rl;
        text-orientation: upright;
    }}
    .para-separator {{
        display: inline-block;
        min-width: 3mm;
        border-left: 1px dashed #bbb;
        margin: 0 1mm;
    }}
    .char-id {{ display: none; }}
    .stats {{
        max-width: 297mm;
        margin: 20px auto;
        padding: 15px;
        background: white;
        font-size: 10pt;
        color: #666;
        border-radius: 4px;
    }}
    .legend {{
        max-width: 297mm;
        margin: 10px auto;
        padding: 10px 15px;
        background: white;
        font-size: 9pt;
        color: #555;
        border-radius: 4px;
    }}
    .legend-item {{
        display: inline-block;
        margin-right: 16px;
    }}
    .legend-dot {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 2px;
        margin-right: 4px;
        vertical-align: middle;
    }}
    @media print {{
        @page {{ size: A4 landscape; margin: 5mm; }}
        body {{ background: white; padding: 0; }}
        .page {{ margin: 0; box-shadow: none; padding: 10mm 4mm 10mm 4mm; min-height: auto; page-break-after: always; }}
        .page:last-child {{ page-break-after: avoid; }}
        .stats, .legend {{ display: none; }}
        .char.matched {{
            background: {pg_color} !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        .para-separator {{ border-left-color: #999; }}
    }}
    """

    # 生成图例
    legend_html = '<div class="legend"><b>图例：</b>'
    for di in data.get("dicts", []):
        source_name = html_mod.escape(di.get("source", "字典"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{di["color"]};color:{di["color"]}"> </span>'
            f"{source_name}（{di.get('matched_count', 0)}字）"
            f"</span>"
        )
    if data.get("shared_chars"):
        shared_color_name = html_mod.escape(data.get("shared_color_name", "深紫色"))
        legend_html += (
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{data["shared_color"]};color:{data["shared_color"]}"> </span>'
            f"{shared_color_name}（{data['stats'].get('shared_count', 0)}字，共有字）"
            f"</span>"
        )
    legend_html += "</div>"

    # 分列（竖排从右到左，每列从上到下）
    # 段落分隔：每个段落单独处理，段尾不足N字也强制换列，插入分隔列
    CHARS_PER_COL = 19
    columns = []
    paragraphs = data["paragraphs"]
    for pi, para in enumerate(paragraphs):
        para_chars = [ci for ci in para["chars"] if not ci["char"].isspace()]
        current_col = []
        for ci in para_chars:
            char = ci["char"]
            if char in PUNCTUATION:
                current_col.append(("punct", char, ci))
            else:
                current_col.append(("char", char, ci))
            if len(current_col) >= CHARS_PER_COL:
                columns.append(current_col)
                current_col = []
        # 段落结束：追加剩余字符（不足20字也成一列）
        if current_col:
            columns.append(current_col)
        # 段落之间加分隔列（最后一个段落不加）
        if pi < len(paragraphs) - 1:
            columns.append(None)  # None = 段落分隔列

    # 过滤掉最后的空列
    while columns and columns[-1] is None:
        columns.pop()

    # 分页（每页20列，控制在A4横向宽度内）
    COLS_PER_PAGE = 20
    pages = []
    current_page = []
    for col in columns:
        current_page.append(col)
        if len(current_page) >= COLS_PER_PAGE:
            pages.append(current_page)
            current_page = []
    if current_page:
        pages.append(current_page)

    # 生成每页 HTML
    page_parts = []
    for page_idx, page_cols in enumerate(pages, 1):
        col_htmls = []
        for col in page_cols:
            # 分隔列（段落之间）
            if col is None:
                col_htmls.append('<div class="para-separator"></div>')
                continue

            cell_htmls = []
            for cell_type, char, ci in col:
                if cell_type == "punct":
                    cell_htmls.append(
                        f'<span class="punct">{html_mod.escape(char)}</span>'
                    )
                elif ci["matched"]:
                    labels = ci.get("labels", [])
                    if labels:
                        primary_color = labels[0]["color"]
                        label_text = " ".join(lb["label"] for lb in labels)
                        is_shared = len(labels) > 1
                        color_style = (
                            f"background:{data['shared_color']}"
                            if is_shared
                            else f"background: linear-gradient(to bottom, {primary_color}22, {primary_color}11)"
                        )
                        cell_htmls.append(
                            f'<span class="char-wrap">'
                            f'<span class="char matched" style="{color_style}">{html_mod.escape(char)}</span>'
                            f'<span class="label" style="color:{primary_color if not is_shared else data["shared_color"]}">{label_text}</span>'
                            f"</span>"
                        )
                    else:
                        cell_htmls.append(
                            f'<span class="char matched">{html_mod.escape(char)}</span>'
                        )
                else:
                    cell_htmls.append(
                        f'<span class="char">{html_mod.escape(char)}</span>'
                    )

            col_htmls.append('<div class="col">' + "".join(cell_htmls) + "</div>")

        page_parts.append(
            f'<div class="page">'
            f'<div class="page-header">{data["source"]} - 第 {page_idx} 页 / 共 {len(pages)} 页</div>'
            f'<div class="vertical-content">' + "".join(col_htmls) + f"</div></div>"
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{html_mod.escape(data["source"])} - 竖版标注</title>
<style>{css}</style>
</head>
<body>
{legend_html}
{"".join(page_parts)}
<div class="stats">
<p><b>来源：</b>{html_mod.escape(data["source"])} | <b>字典：</b>{", ".join(html_mod.escape(d.get("source", p)) for d, p in zip(data.get("dicts", []), data.get("dict_paths", [])))}</p>
<p><b>总字数：</b>{data["stats"]["total"]} | <b>已匹配：</b>{data["stats"]["matched"]} ({data["stats"]["match_rate"]}){f" | <b>共有字：</b>{data["stats"]["shared_count"]} ({data["stats"]["shared_rate"]})" if data.get("shared_chars") else ""} | <b>总页数：</b>{len(pages)}</p>
</div>
</body>
</html>"""
    return html


# ───────────────────────────────────────────────
# 完整流程（all-in-one）
# ───────────────────────────────────────────────
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
    import tempfile

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


# ───────────────────────────────────────────────
# 命令行入口
# ───────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="碑帖学习伴侣 stele-companion v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用流程:
  1. build-dict : 从标准文档生成字典
  2. annotate   : 文本比对标注
  3. render     : 生成 HTML（横版/竖版）
  4. all        : 一步完成（推荐）

示例（完整流程）:
  python stele_companion.py all 肥致碑.doc \\
      --dict 张迁碑_dict.json \\
      --output-horizontal 肥致碑_横版.html \\
      --output-vertical 肥致碑_竖版.html \\
      --start-marker "从事君之元嗣"

示例（仅建字典）:
  python stele_companion.py build-dict 张迁碑.docx \\
      -o zhangqian_dict.json \\
      --start-marker "君讳迁"

示例（多字典标注）:
  python stele_companion.py annotate 肥致碑.doc \\
      --dict 张迁碑.json,鲜于璜碑.json \\
      -o annotated.json

示例（渲染竖版）:
  python stele_companion.py render \\
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
                log_warn("获取失败，将使用原文件内容")

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
