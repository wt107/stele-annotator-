# 碑帖学习伴侣 stele-companion

碑文字典对照 + 标注排版工具，支持多字典彩色对照、简繁转换、横版/竖版HTML输出、A4打印优化。

## 安装

```bash
pip install stele-companion
```

**依赖**: Python 3.8+

**可选依赖**（处理 .doc 文件时需要）：
- Windows: `pip install pywin32` 或安装 Microsoft Word
- Mac/Linux: `brew install --cask libreoffice` 或 `sudo apt install libreoffice`

## 快速开始

```bash
# 完整流程（推荐）
stele-companion all 碑文.txt \
    --dict 字典.json \
    --output-horizontal 横版.html \
    --output-vertical 竖版.html \
    --start-marker "正文起始标记"
```

## 支持格式

| 格式 | 推荐度 | 说明 |
|:---|:---:|:---|
| **.txt (UTF-8)** | ⭐⭐⭐ | **强烈推荐**，生僻字支持最好 |
| **.docx** | ⭐⭐⭐ | **推荐**，纯 Python 处理 |
| **.doc** | ⭐⭐ | 支持，需安装 LibreOffice（Mac/Linux）或 Word/pywin32（Windows）|

## 功能

- **build-dict**: 从标准碑帖文档建立字-编号字典
- **annotate**: 多字典彩色对照标注
- **render**: 横版/竖版 HTML 输出（A4 打印优化）
- **fetch**: 自动获取权威碑帖原文

## AI 使用

```bash
# AI 推荐工作流
stele-companion all 碑文.txt --dict 字典.json --json --dry-run  # 先验证
stele-companion all 碑文.txt --dict 字典.json --json             # 再执行
```

## 文档

详细使用说明请参阅 [SKILL.md](docs/SKILL.md)

## 许可证

MIT License
