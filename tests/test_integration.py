# -*- coding: utf-8 -*-
"""
集成测试 - 端到端测试完整工作流
"""

import os
import sys
import json
import tempfile
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stele_companion import build_dict, annotate, render_html, __version__
from stele_companion.core import _merge_paragraphs, _split_stele_paragraphs, _is_cjk_char
from stele_companion.utils import VARIANT_MAP, to_traditional, to_simplified


class TestUtils:
    """测试工具函数"""

    def test_version(self):
        """测试版本号"""
        assert __version__ == "2.0.0"

    def test_variant_map_no_duplicates(self):
        """测试简繁映射表无重复键"""
        # VARIANT_MAP 中每个键应该唯一
        keys = list(VARIANT_MAP.keys())
        assert len(keys) == len(set(keys)), "VARIANT_MAP 存在重复键"

    def test_to_traditional(self):
        """测试简体转繁体"""
        assert to_traditional("国") == "國"
        assert to_traditional("学") == "學"

    def test_to_simplified(self):
        """测试繁体转简体"""
        assert to_simplified("國") == "国"
        assert to_simplified("學") == "学"

    def test_is_cjk_char(self):
        """测试 CJK 汉字检测"""
        # 基本汉字
        assert _is_cjk_char("汉") is True
        assert _is_cjk_char("字") is True
        # 标点符号
        assert _is_cjk_char("。") is False
        assert _is_cjk_char("，") is False
        # 英文
        assert _is_cjk_char("a") is False
        assert _is_cjk_char("A") is False
        # 数字
        assert _is_cjk_char("1") is False


class TestCoreFunctions:
    """测试核心函数"""

    def test_merge_paragraphs(self):
        """测试段落合并"""
        paragraphs = [
            "第一段开头",
            "没有句末标点的段落",
            "第二段开头。",
            "第三段内容",
        ]
        result = _merge_paragraphs(paragraphs)
        # 第一段和第二段应该合并（因为第二段没有句末标点）
        assert len(result) < len(paragraphs)

    def test_split_stele_paragraphs(self):
        """测试碑文段落拆分"""
        text = "君讳迁字公方其颂曰穆穆我君延熹八年造。"
        result = _split_stele_paragraphs([text])
        # 应该能识别出赞词和落款
        assert len(result) >= 1


class TestBuildDict:
    """测试字典构建"""

    def test_build_dict_from_txt(self):
        """从 .txt 文件构建字典"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("标题\n君讳迁，字公方。\n")
            f.flush()

            output = tempfile.mktemp(suffix='.json')
            try:
                result = build_dict(f.name, output, start_marker='君讳迁')
                assert result is not None
                assert 'mappings' in result
                assert '君' in result['mappings']
            finally:
                os.unlink(f.name)
                if os.path.exists(output):
                    os.unlink(output)

    def test_dict_structure(self):
        """验证字典 JSON 结构正确"""
        dict_path = os.path.join(os.path.dirname(__file__), 'fixtures', '张迁碑_dict.json')
        with open(dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 验证必需字段
        assert 'source' in data
        assert 'mappings' in data
        assert 'paragraph_count' in data
        assert 'char_count' in data
        assert 'unique_chars' in data

        # 验证标号格式
        for char, label in data['mappings'].items():
            assert '-' in label, f"标号格式错误: {char} -> {label}"


class TestAnnotate:
    """测试标注功能"""

    def test_annotate_single_dict(self):
        """单字典标注"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("标题\n君讳迁，字公方。\n")
            f.flush()

        dict_path = os.path.join(os.path.dirname(__file__), 'fixtures', '张迁碑_dict.json')
        output = tempfile.mktemp(suffix='.json')

        try:
            result = annotate(
                f.name,
                [dict_path],
                output,
                start_marker='君讳迁'
            )
            assert result is not None
            assert 'paragraphs' in result
            assert 'stats' in result
            assert result['stats']['total'] > 0
        finally:
            os.unlink(f.name)
            if os.path.exists(output):
                os.unlink(output)

    def test_annotate_multi_dict(self):
        """多字典标注，验证颜色分配"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("标题\n君讳迁，字公方。\n")
            f.flush()

        dict1 = os.path.join(os.path.dirname(__file__), 'fixtures', '张迁碑_dict.json')
        dict2 = os.path.join(os.path.dirname(__file__), 'fixtures', '肥致碑_dict.json')
        output = tempfile.mktemp(suffix='.json')

        try:
            result = annotate(
                f.name,
                [dict1, dict2],
                output,
                start_marker='君讳迁'
            )
            assert result is not None
            assert len(result['dicts']) == 2
            # 验证颜色分配
            colors = [d['color'] for d in result['dicts']]
            assert len(set(colors)) == len(colors)  # 颜色应该不同
        finally:
            os.unlink(f.name)
            if os.path.exists(output):
                os.unlink(output)

    def test_shared_chars(self):
        """测试共有字识别"""
        dict1 = os.path.join(os.path.dirname(__file__), 'fixtures', '张迁碑_dict.json')
        dict2 = os.path.join(os.path.dirname(__file__), 'fixtures', '肥致碑_dict.json')

        # 读取两个字典，找出共有字
        with open(dict1, 'r', encoding='utf-8') as f:
            d1 = json.load(f)
        with open(dict2, 'r', encoding='utf-8') as f:
            d2 = json.load(f)

        # 找出共有字
        shared = set(d1['mappings'].keys()) & set(d2['mappings'].keys())

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            # 写入包含共有字的文本
            text = "标题\n君讳迁，" + "".join(list(shared)[:10]) + "\n"
            f.write(text)
            f.flush()

        output = tempfile.mktemp(suffix='.json')

        try:
            result = annotate(
                f.name,
                [dict1, dict2],
                output,
                start_marker='君讳迁'
            )
            assert result is not None
            assert 'shared_chars' in result
        finally:
            os.unlink(f.name)
            if os.path.exists(output):
                os.unlink(output)


class TestRender:
    """测试渲染功能"""

    def test_render_horizontal(self):
        """横版 HTML 渲染"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("标题\n君讳迁，字公方。\n")
            f.flush()

        dict_path = os.path.join(os.path.dirname(__file__), 'fixtures', '张迁碑_dict.json')
        annotated = tempfile.mktemp(suffix='.json')
        output = tempfile.mktemp(suffix='.html')

        try:
            annotate(f.name, [dict_path], annotated, start_marker='君讳迁')
            render_html(annotated, output, format_type='horizontal')

            with open(output, 'r', encoding='utf-8') as hf:
                html = hf.read()

            assert '<!DOCTYPE html>' in html
            assert '横版' in html or 'horizontal' in html.lower()
        finally:
            os.unlink(f.name)
            if os.path.exists(annotated):
                os.unlink(annotated)
            if os.path.exists(output):
                os.unlink(output)

    def test_render_vertical(self):
        """竖版 HTML 渲染"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("标题\n君讳迁，字公方。\n")
            f.flush()

        dict_path = os.path.join(os.path.dirname(__file__), 'fixtures', '张迁碑_dict.json')
        annotated = tempfile.mktemp(suffix='.json')
        output = tempfile.mktemp(suffix='.html')

        try:
            annotate(f.name, [dict_path], annotated, start_marker='君讳迁')
            render_html(annotated, output, format_type='vertical')

            with open(output, 'r', encoding='utf-8') as hf:
                html = hf.read()

            assert '<!DOCTYPE html>' in html
            assert '竖版' in html or 'vertical' in html.lower()
        finally:
            os.unlink(f.name)
            if os.path.exists(annotated):
                os.unlink(annotated)
            if os.path.exists(output):
                os.unlink(output)

    def test_html_escaping(self):
        """验证 XSS 防护"""
        # 创建包含特殊字符的文本
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("标题\n<script>alert('xss')</script>君讳迁。\n")
            f.flush()

        dict_path = os.path.join(os.path.dirname(__file__), 'fixtures', '张迁碑_dict.json')
        annotated = tempfile.mktemp(suffix='.json')
        output = tempfile.mktemp(suffix='.html')

        try:
            annotate(f.name, [dict_path], annotated, start_marker='<script>')
            render_html(annotated, output, format_type='horizontal')

            with open(output, 'r', encoding='utf-8') as hf:
                html = hf.read()

            # 应该被转义，不应该有可执行的 script 标签
            assert '<script>alert' not in html or '&lt;script&gt;' in html
        finally:
            os.unlink(f.name)
            if os.path.exists(annotated):
                os.unlink(annotated)
            if os.path.exists(output):
                os.unlink(output)


class TestFullWorkflow:
    """端到端测试"""

    def test_full_workflow(self):
        """测试完整流程：build_dict → annotate → render"""
        # Step 1: 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("张迁碑\n君讳迁，字公方，陈留己吾人也。\n")
            f.flush()
            input_file = f.name

        dict_file = tempfile.mktemp(suffix='_dict.json')
        annotated_file = tempfile.mktemp(suffix='_annotated.json')
        horizontal_html = tempfile.mktemp(suffix='_horizontal.html')
        vertical_html = tempfile.mktemp(suffix='_vertical.html')

        try:
            # Step 2: 构建字典
            dict_result = build_dict(input_file, dict_file, start_marker='君讳迁')
            assert dict_result is not None
            assert os.path.exists(dict_file)

            # Step 3: 标注
            annotate_result = annotate(input_file, [dict_file], annotated_file, start_marker='君讳迁')
            assert annotate_result is not None
            assert os.path.exists(annotated_file)

            # Step 4: 渲染横版
            render_html(annotated_file, horizontal_html, format_type='horizontal')
            assert os.path.exists(horizontal_html)

            # Step 5: 渲染竖版
            render_html(annotated_file, vertical_html, format_type='vertical')
            assert os.path.exists(vertical_html)

            print(f"\n完整流程测试成功!")
            print(f"  字典: {dict_file}")
            print(f"  标注: {annotated_file}")
            print(f"  横版: {horizontal_html}")
            print(f"  竖版: {vertical_html}")

        finally:
            for path in [input_file, dict_file, annotated_file, horizontal_html, vertical_html]:
                if os.path.exists(path):
                    os.unlink(path)
