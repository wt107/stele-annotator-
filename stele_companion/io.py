# -*- coding: utf-8 -*-
"""
文件读写模块 - 读取 .docx/.txt 文件
AI友好版本：纯Python实现，无需外部依赖
"""

import os
from pathlib import Path

from .utils import log_warn


def read_input(file_path, paragraphs=None):
    """
    读取输入文件
    
    支持格式：
    - .docx: Word 文档（推荐）
    - .txt: 纯文本（最稳定，支持生僻字）
    
    不支持的格式：
    - .doc: 旧版 Word，请转换为 .docx 或 .txt
    """
    if paragraphs is not None:
        return paragraphs

    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".docx":
        return _read_docx(file_path)
    elif ext == ".txt":
        return _read_txt(file_path)
    elif ext == ".doc":
        raise ValueError(
            f"不支持 .doc 格式: {file_path}\n"
            f"请转换为 .docx 或 .txt 格式：\n"
            f"  方法1: 用 Word 打开 → 另存为 → .docx\n"
            f"  方法2: 用 Word 打开 → 另存为 → 纯文本(.txt)\n"
            f"  方法3: 在线转换工具 https://convertio.co/doc-docx/"
        )
    elif ext == ".json":
        raise ValueError(f"JSON 文件不能作为文本源: {file_path}")
    else:
        raise ValueError(
            f"不支持的文件格式: {ext}\n"
            f"支持格式: .docx, .txt\n"
            f"请转换后重试"
        )


def _read_txt(file_path):
    """
    读取 TXT 文件，自动检测编码（针对古籍/生僻字优化）
    
    编码优先级：
    1. UTF-8（推荐，支持所有生僻字）
    2. GB18030（中文Windows，支持生僻字扩展）
    3. chardet 自动检测
    """
    raw = None
    with open(file_path, "rb") as f:
        raw = f.read()
    
    # 尝试常见编码
    encodings = [
        "utf-8",
        "utf-8-sig",  # 带BOM的UTF-8
        "gb18030",    # 中文国家标准，支持生僻字
        "gbk",
        "gb2312",
        "big5",       # 繁体中文
    ]
    
    # 先尝试常见编码
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            if encoding != "utf-8":
                log_warn(f"使用非 UTF-8 编码: {encoding}，建议转换为 UTF-8")
            break
        except UnicodeDecodeError:
            continue
    else:
        # 常见编码都失败，用 chardet
        try:
            import chardet
            result = chardet.detect(raw)
            encoding = result.get("encoding", "utf-8") or "utf-8"
            confidence = result.get("confidence", 0)
            text = raw.decode(encoding, errors="replace")
            log_warn(f"编码自动检测: {encoding} (置信度: {confidence:.2%})")
        except ImportError:
            # chardet 未安装，用 utf-8 容错
            text = raw.decode("utf-8", errors="replace")
            log_warn("编码检测失败，使用 UTF-8 容错模式，可能有字符丢失")
    
    # 检查是否有字符丢失
    if "\ufffd" in text or "�" in text:
        log_warn("检测到字符丢失（显示为�），建议用 UTF-8 重新保存文件")
    
    # 处理换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p for p in text.split("\n") if p.strip()]
    
    return paragraphs


def _read_docx(file_path):
    """
    读取 .docx 文件
    
    注意：python-docx 读取的是文档文本，不保留格式
    对于含生僻字的文档，建议转换为 .txt 格式
    """
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError(
            "缺少 python-docx 依赖\n"
            "请安装: pip install python-docx>=0.8.10"
        )

    doc = Document(file_path)
    paragraphs = []
    
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            paragraphs.append(text)
            # 检查生僻字丢失
            if "\ufffd" in text or "?" in text:
                log_warn(f"段落可能包含无法读取的字符，建议转换为 .txt 格式")
    
    return paragraphs


def convert_to_txt(input_path, output_path=None):
    """
    将文件转换为 UTF-8 编码的 .txt
    
    用途：
    1. 处理含生僻字的文档
    2. 统一编码格式
    3. 去除格式，保留纯文本
    
    示例：
        convert_to_txt("碑文.docx", "碑文.txt")
    """
    input_path = Path(input_path)
    
    if output_path is None:
        output_path = input_path.with_suffix(".txt")
    
    # 读取内容
    paragraphs = read_input(str(input_path))
    
    # 写入 UTF-8 文本
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(paragraphs))
    
    return output_path
