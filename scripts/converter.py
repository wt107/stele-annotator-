#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简繁体转换模块 v1.0

支持：
- 自动检测 opencc 库（专业级转换）
- 回退到内置映射表
- 单字和文本批量转换
- 简繁对照显示
"""

import json
from pathlib import Path

# 尝试导入 opencc
try:
    import opencc
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False

# 映射表缓存
_s2t_map = None
_t2s_map = None


def _load_mapping(filename):
    """加载映射表"""
    global _s2t_map, _t2s_map

    if filename == 's2t' and _s2t_map is None:
        map_path = Path(__file__).parent / 'data' / 's2t.json'
        if map_path.exists():
            with open(map_path, 'r', encoding='utf-8') as f:
                _s2t_map = json.load(f)
        else:
            _s2t_map = {}

    if filename == 't2s' and _t2s_map is None:
        map_path = Path(__file__).parent / 'data' / 't2s.json'
        if map_path.exists():
            with open(map_path, 'r', encoding='utf-8') as f:
                _t2s_map = json.load(f)
        else:
            _t2s_map = {}

    return _s2t_map if filename == 's2t' else _t2s_map


class ChineseConverter:
    """简繁体转换器

    使用方法：
        converter = ChineseConverter()

        # 简转繁
        traditional = converter.to_traditional("简体字")

        # 繁转简
        simplified = converter.to_simplified("繁體字")

        # 获取对照
        sim, tra = converter.get_dual_text("汉字")

        # 检查是否相同
        if converter.is_same_char("国", "國"):
            print("是同一个字的简繁体")
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._opencc_s2t = None
        self._opencc_t2s = None

        if HAS_OPENCC:
            try:
                self._opencc_s2t = opencc.OpenCC('s2t.json')
                self._opencc_t2s = opencc.OpenCC('t2s.json')
            except Exception:
                pass

        self._initialized = True

    @property
    def has_opencc(self):
        """是否可用 opencc"""
        return self._opencc_s2t is not None

    def to_traditional(self, text):
        """简体转繁体

        Args:
            text: 简体文本

        Returns:
            繁体文本
        """
        if not text:
            return text

        if self._opencc_s2t:
            return self._opencc_s2t.convert(text)

        # 回退到映射表
        s2t = _load_mapping('s2t')
        result = []
        for char in text:
            result.append(s2t.get(char, char))
        return ''.join(result)

    def to_simplified(self, text):
        """繁体转简体

        Args:
            text: 繁体文本

        Returns:
            简体文本
        """
        if not text:
            return text

        if self._opencc_t2s:
            return self._opencc_t2s.convert(text)

        # 回退到映射表
        t2s = _load_mapping('t2s')
        result = []
        for char in text:
            result.append(t2s.get(char, char))
        return ''.join(result)

    def get_dual_text(self, text):
        """获取简繁对照

        Args:
            text: 任意文本

        Returns:
            (简体文本, 繁体文本) 元组
        """
        if not text:
            return (text, text)

        # 先转繁体
        traditional = self.to_traditional(text)
        # 再转简体
        simplified = self.to_simplified(traditional)

        return (simplified, traditional)

    def is_same_char(self, char1, char2):
        """检查两个字是否是同一字的简繁体

        Args:
            char1: 第一个字
            char2: 第二个字

        Returns:
            是否是同一字的简繁体
        """
        if char1 == char2:
            return True

        # 检查简转繁
        if self.to_traditional(char1) == char2:
            return True

        # 检查繁转简
        if self.to_simplified(char1) == char2:
            return True

        return False

    def get_char_variants(self, char):
        """获取一个字的所有变体（简体、繁体）

        Args:
            char: 单个字符

        Returns:
            set 包含简体和繁体
        """
        variants = {char}
        variants.add(self.to_traditional(char))
        variants.add(self.to_simplified(char))
        return variants

    def find_in_variants(self, char, text):
        """在文本中查找字符的简繁变体

        Args:
            char: 要查找的字符
            text: 目标文本

        Returns:
            匹配的位置列表
        """
        variants = self.get_char_variants(char)
        positions = []
        for i, c in enumerate(text):
            if c in variants:
                positions.append(i)
        return positions


def create_converter():
    """创建转换器实例（工厂函数）"""
    return ChineseConverter()


# 便捷函数
_converter = None

def _get_converter():
    global _converter
    if _converter is None:
        _converter = ChineseConverter()
    return _converter


def to_traditional(text):
    """简体转繁体（便捷函数）"""
    return _get_converter().to_traditional(text)


def to_simplified(text):
    """繁体转简体（便捷函数）"""
    return _get_converter().to_simplified(text)


def get_dual_text(text):
    """获取简繁对照（便捷函数）"""
    return _get_converter().get_dual_text(text)


def is_same_char(char1, char2):
    """检查是否是同一字的简繁体（便捷函数）"""
    return _get_converter().is_same_char(char1, char2)


# 测试代码
if __name__ == '__main__':
    converter = ChineseConverter()

    print(f"OpenCC 可用: {converter.has_opencc}")

    # 测试简转繁
    test_cases = [
        "汉字简化",
        "书法练习",
        "碑文标注",
        "张迁碑",
        "国风",
    ]

    print("\n简转繁测试:")
    for text in test_cases:
        trad = converter.to_traditional(text)
        print(f"  {text} -> {trad}")

    # 测试繁转简
    trad_cases = [
        "漢字簡化",
        "書法練習",
        "碑文標注",
        "張遷碑",
    ]

    print("\n繁转简测试:")
    for text in trad_cases:
        simp = converter.to_simplified(text)
        print(f"  {text} -> {simp}")

    # 测试对照
    print("\n简繁对照测试:")
    for text in test_cases[:3]:
        sim, tra = converter.get_dual_text(text)
        print(f"  简体: {sim}, 繁体: {tra}")

    # 测试简繁匹配
    print("\n简繁匹配测试:")
    print(f"  国 == 國: {converter.is_same_char('国', '國')}")
    print(f"  汉 == 漢: {converter.is_same_char('汉', '漢')}")
    print(f"  书 == 書: {converter.is_same_char('书', '書')}")
