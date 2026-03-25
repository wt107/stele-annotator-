# 碑帖学习伴侣 Stele Companion

碑文字典对照 + 标注排版工具，支持多字典彩色对照、简繁转换、横版/竖版HTML输出、A4打印优化、自动获取权威碑帖原文。

## 功能特性

- **字典构建** - 从标准碑帖文档建立字-编号字典（如 1-1, 1-2...）
- **多字典对照** - 同时使用多个字典标注，颜色区分
- **共有字标识** - 多字典共有字深紫色突出显示
- **简繁转换** - 内置500+常用字映射，无外部依赖
- **横版/竖版** - 双输出格式，A4打印优化
- **自动获取原文** - `--fetch` 从权威来源获取碑帖原文
- **三种字号** - small/medium/large 适配不同需求

## 安装

```bash
pip install python-docx chardet requests
```

## 快速开始

```bash
# 一键完成（推荐）
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json \
    --output-horizontal 肥致碑_横版.html \
    --output-vertical 肥致碑_竖版.html \
    --font-size medium \
    --theme classic

# 自动获取权威原文
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json \
    --fetch \
    --output-vertical 肥致碑_竖版.html

# 构建字典
python stele_companion.py build-dict 张迁碑.docx \
    -o 张迁碑_dict.json \
    --start-marker "君讳迁"

# 多字典标注
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json,鲜于璜碑_dict.json \
    --output-vertical 肥致碑_多字典.html
```

## 文件结构

```
stele-annotator-/
├── SKILL.md                    # 详细文档
├── README.md                   # 本文件
├── requirements.txt            # 依赖
└── scripts/
    └── stele_companion.py      # 主脚本
```

## 命令

| 命令 | 说明 |
|:---|:---|
| `build-dict` | 从标准文档构建字典 |
| `annotate` | 文本比对标注 |
| `render` | 生成 HTML（横版/竖版） |
| `all` | 完整流程（推荐） |

## 文档

详细使用说明请参阅 [SKILL.md](./SKILL.md)

## 版本历史

### v1.4 (2026-03-24)
- 新增 `--fetch` 自动获取碑帖原文
- 修复 XSS 安全漏洞
- 增强健壮性

## License

MIT
