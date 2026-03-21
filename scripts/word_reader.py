#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台 Word 文件读取模块
支持 .doc（Word 97-2003）和 .docx（Word 2007+）格式

平台适配策略：
  - Windows: 优先 win32com（需 pywin32）
  - macOS/Linux: 优先 python-docx（.docx），回退 LibreOffice（.doc）
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path


class WordReader:
    """跨平台 Word 文件读取器"""

    @staticmethod
    def read(file_path):
        """读取 Word 文件，返回纯文本

        Args:
            file_path: Word 文件路径（.doc 或 .docx）

        Returns:
            str: 文件纯文本内容

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
            RuntimeError: 缺少必要的依赖
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = path.suffix.lower()
        if ext == '.doc':
            return WordReader._read_doc(str(path))
        elif ext == '.docx':
            return WordReader._read_docx(str(path))
        else:
            raise ValueError(f"不支持的 Word 格式: {ext}（仅支持 .doc 和 .docx）")

    @staticmethod
    def _read_doc(file_path):
        """读取 .doc 文件（自动选择平台策略）"""
        system = platform.system()
        if system == 'Windows':
            return WordReader._read_doc_win32(file_path)
        else:
            return WordReader._read_doc_libreoffice(file_path)

    @staticmethod
    def _read_doc_win32(file_path):
        """Windows: 通过 win32com COM 接口读取 .doc"""
        try:
            import win32com.client
        except ImportError:
            raise RuntimeError(
                "读取 .doc 需要 pywin32 库。\n"
                "请运行: pip install pywin32\n"
                "或改用 .docx 格式（仅需 python-docx）"
            )

        abs_path = os.path.abspath(file_path)
        word = None
        doc = None
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            word.AutomationSecurity = 3  # msoAutomationSecurityForceDisable - 禁用所有宏
            doc = word.Documents.Open(abs_path, ReadOnly=True)
            text = doc.Content.Text
            return text
        except Exception as e:
            raise RuntimeError(f"读取 .doc 失败: {e}")
        finally:
            if doc:
                try: doc.Close(False)
                except Exception: pass
            if word:
                try: word.Quit()
                except Exception: pass

    @staticmethod
    def _read_doc_libreoffice(file_path):
        """macOS/Linux: 通过 LibreOffice 将 .doc 转为纯文本"""
        lo_cmd = None
        for cmd_name in ['libreoffice', 'soffice']:
            if shutil.which(cmd_name):
                lo_cmd = cmd_name
                break
        if not lo_cmd:
            raise RuntimeError(
                "读取 .doc 需要 LibreOffice 或 python-docx。\n"
                "请安装 LibreOffice: https://www.libreoffice.org/\n"
                "或改用 .docx 格式（仅需 python-docx）"
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                lo_cmd, '--headless', '--convert-to', 'txt:Text',
                '--outdir', tmpdir, file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice 转换失败: {result.stderr}")

            txt_name = Path(file_path).stem + '.txt'
            txt_path = os.path.join(tmpdir, txt_name)
            if not os.path.exists(txt_path):
                raise RuntimeError(f"转换输出文件未生成: {txt_path}")

            with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()

    @staticmethod
    def _read_docx(file_path):
        """读取 .docx 文件（跨平台）"""
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError(
                "读取 .docx 需要 python-docx 库。\n"
                "请运行: pip install python-docx"
            )

        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return '\n'.join(paragraphs)
        except Exception as e:
            raise RuntimeError(f"读取 .docx 失败: {e}")

    @staticmethod
    def is_word_file(file_path):
        """判断文件是否为 Word 格式"""
        ext = Path(file_path).suffix.lower()
        return ext in ('.doc', '.docx')

    @staticmethod
    def check_availability():
        """检查当前环境的 Word 读取能力

        Returns:
            dict: {
                'doc': bool,   # 能否读取 .doc
                'docx': bool,  # 能否读取 .docx
                'methods': list,  # 可用方法列表
                'missing': list   # 缺少的依赖
            }
        """
        result = {
            'doc': False,
            'docx': False,
            'methods': [],
            'missing': []
        }

        # 检查 python-docx（.docx 跨平台）
        try:
            import docx  # noqa: F401
            result['docx'] = True
            result['methods'].append('python-docx (.docx)')
        except ImportError:
            result['missing'].append('python-docx (pip install python-docx)')

        # 检查 win32com（.doc Windows）
        if platform.system() == 'Windows':
            try:
                import win32com.client  # noqa: F401
                result['doc'] = True
                result['methods'].append('win32com (.doc)')
            except ImportError:
                result['missing'].append('pywin32 (pip install pywin32)')

        # 检查 LibreOffice（.doc macOS/Linux）
        for lo_name in ['libreoffice', 'soffice']:
            if shutil.which(lo_name):
                result['doc'] = True
                result['methods'].append(f'{lo_name} (.doc)')
                break

        return result


def normalize_word_text(text):
    """清理 Word 文档文本中的常见问题

    - 去除软换行（Word 段内换行符）
    - 去除连续多余空白

    Args:
        text: Word 文档原始文本

    Returns:
        str: 清理后的文本
    """
    # 替换各种换行为统一格式
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # 合并段落间多余空行
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    return text.strip()


if __name__ == '__main__':
    # 自测
    print("Word 读取能力检查:")
    avail = WordReader.check_availability()
    print(f"  .doc  支持: {avail['doc']}")
    print(f"  .docx 支持: {avail['docx']}")
    print(f"  可用方法: {', '.join(avail['methods']) or '无'}")
    if avail['missing']:
        print(f"  缺少依赖: {', '.join(avail['missing'])}")
