# -*- coding: utf-8 -*-
"""
文件读写模块 - 读取 .doc/.docx/.txt 文件
支持 .doc 但需要外部工具，提供友好的降级提示
"""

import os
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path

from .utils import log_warn, log_info, log_err


def read_input(file_path, paragraphs=None):
    """
    读取输入文件
    
    支持格式：
    - .txt: 纯文本（最稳定，推荐）
    - .docx: Word 文档（推荐，纯 Python）
    - .doc: 旧版 Word（需要 LibreOffice，提供转换提示）
    """
    if paragraphs is not None:
        return paragraphs

    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in (".doc", ".docx"):
        return _read_word(file_path)
    elif ext == ".txt":
        return _read_txt(file_path)
    elif ext == ".json":
        raise ValueError(f"无法读取 JSON 文件作为文本源: {file_path}")
    else:
        raise ValueError(
            f"不支持的文件格式: {ext}\n"
            f"支持格式: .doc, .docx, .txt\n"
            f".doc 建议转换为 .txt: https://convertio.co/doc-txt/"
        )


def _read_txt(file_path):
    """读取 TXT 文件，自动检测编码（针对古籍/生僻字优化）"""
    raw = None
    with open(file_path, "rb") as f:
        raw = f.read()
    
    # 尝试常见编码
    encodings = ["utf-8", "utf-8-sig", "gb18030", "gbk", "gb2312", "big5"]
    
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            if encoding != "utf-8":
                log_info(f"检测到编码: {encoding}")
            break
        except UnicodeDecodeError:
            continue
    else:
        # 常见编码都失败，用 chardet
        try:
            import chardet
            result = chardet.detect(raw)
            encoding = result.get("encoding", "utf-8") or "utf-8"
            text = raw.decode(encoding, errors="replace")
            log_warn(f"使用自动检测编码: {encoding}")
        except ImportError:
            text = raw.decode("utf-8", errors="replace")
    
    # 检查是否有字符丢失
    if "\ufffd" in text or "�" in text:
        log_warn("检测到字符丢失（显示为�），建议用 UTF-8 重新保存文件")
    
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [p for p in text.split("\n") if p.strip()]


def _read_word(file_path):
    """读取 Word 文件"""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".docx":
        return _read_docx(file_path)
    elif ext == ".doc":
        return _read_doc_with_fallback(file_path)
    else:
        raise ValueError(f"不支持的 Word 格式: {ext}")


def _read_docx(file_path):
    """读取 .docx"""
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError(
            "缺少 python-docx\n"
            "请安装: pip install python-docx>=0.8.10"
        )

    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return paragraphs


def _read_doc_with_fallback(file_path):
    """
    读取 .doc 文件，支持多种方式
    
    优先级：
    1. Windows + win32com (如果可用)
    2. LibreOffice (如果已安装)
    3. 提供在线转换提示
    """
    system = platform.system()
    
    # 尝试 Windows COM
    if system == "Windows":
        try:
            return _read_doc_win32(file_path)
        except Exception as e:
            log_warn(f"win32com 读取失败: {e}")
    
    # 尝试 LibreOffice
    lo_cmd = None
    for cmd_name in ["libreoffice", "soffice"]:
        if shutil.which(cmd_name):
            lo_cmd = cmd_name
            break
    
    if lo_cmd:
        try:
            return _read_doc_libreoffice(file_path, lo_cmd)
        except Exception as e:
            log_warn(f"LibreOffice 读取失败: {e}")
    
    # 都失败了，提供转换提示
    raise RuntimeError(
        f"无法直接读取 .doc 文件: {file_path}\n"
        f"\n解决方法（任选其一）:\n"
        f"1. 用 Word 打开 → 另存为 → .docx 格式\n"
        f"2. 用 Word 打开 → 另存为 → 纯文本(.txt) 格式\n"
        f"3. 在线转换: https://convertio.co/doc-txt/\n"
        f"4. 安装 LibreOffice:\n"
        f"   - Mac: brew install --cask libreoffice\n"
        f"   - Ubuntu: sudo apt install libreoffice\n"
        f"   - Windows: 下载安装 https://www.libreoffice.org/"
    )


def _read_doc_win32(file_path):
    """Windows: 使用 win32com 读取 .doc"""
    try:
        import win32com.client
    except ImportError:
        raise RuntimeError(
            "读取 .doc 需要 pywin32\n"
            "请安装: pip install pywin32"
        )

    abs_path = os.path.abspath(file_path)
    word = None
    doc = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False
        doc = word.Documents.Open(abs_path, ReadOnly=True)
        text = doc.Content.Text
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [p for p in text.split("\n") if p.strip()]
        return paragraphs
    finally:
        if doc:
            try:
                doc.Close(False)
            except:
                pass
        if word:
            try:
                word.Quit()
            except:
                pass


def _read_doc_libreoffice(file_path, lo_cmd="libreoffice"):
    """使用 LibreOffice 读取 .doc"""
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
            raise RuntimeError("LibreOffice 输出文件未生成")

        return _read_txt(txt_path)


def convert_to_txt(input_path, output_path=None):
    """将文件转换为 UTF-8 编码的 .txt"""
    input_path = Path(input_path)
    
    if output_path is None:
        output_path = input_path.with_suffix(".txt")
    
    paragraphs = read_input(str(input_path))
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(paragraphs))
    
    return output_path
