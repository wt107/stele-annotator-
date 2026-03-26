# -*- coding: utf-8 -*-
"""
文件读写模块 - 读取 .doc/.docx/.txt 文件
"""

import os
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path

from .utils import log_warn


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
