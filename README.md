# 碑帖学习伴侣 stele-companion

碑文字典对照 + 标注排版工具，支持多字典彩色对照、简繁转换、横版/竖版HTML输出、A4打印优化。

## 安装

```bash
pip install stele-companion
```

## 快速开始

```bash
# 完整流程（推荐）
stele-companion all 碑文.doc \
    --dict 字典.json \
    --output-horizontal 横版.html \
    --output-vertical 竖版.html \
    --start-marker "正文起始标记"
```

## 功能

- **build-dict**: 从标准碑帖文档建立字-编号字典
- **annotate**: 多字典彩色对照标注
- **render**: 横版/竖版 HTML 输出（A4 打印优化）
- **fetch**: 自动获取权威碑帖原文

## 文档

详细使用说明请参阅 [SKILL.md](docs/SKILL.md)

## 许可证

MIT License
