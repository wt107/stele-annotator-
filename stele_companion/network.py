# -*- coding: utf-8 -*-
"""
网络获取模块 - 从权威来源获取碑帖原文段落信息
"""

import re
from pathlib import Path

from .utils import STELE_SOURCES, log_warn, log_info, log_ok


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
