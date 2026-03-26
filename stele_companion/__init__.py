# -*- coding: utf-8 -*-
"""
碑帖学习伴侣 stele-companion v2.0
================================

核心功能：
  1. build_dict   - 从标准文档构建字典
  2. annotate     - 文本比对标注（多字典彩色对照）
  3. render_html  - 输出横版/竖版 HTML（支持 A4 打印优化）
  4. fetch_stele_text - 从权威来源获取碑帖原文段落信息
"""

__version__ = "2.0.0"
__author__ = "wt107"

from .core import build_dict, annotate
from .render import render_html
from .network import fetch_stele_text

__all__ = [
    "build_dict",
    "annotate",
    "render_html",
    "fetch_stele_text",
    "__version__",
]
