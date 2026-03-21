# 碑文字标注器 Stele Annotator

碑文字标号与标注工具，支持多字典对照标注、简繁转换、批量处理。

## 功能特性

- **多字典对照** - 同时使用多个字典标注，颜色区分
- **简繁转换** - 简体字匹配繁体字典，反之亦然
- **多格式支持** - HTML、TXT、DOC、DOCX
- **批量处理** - 目录批量处理，断点续传
- **打印优化** - A4纸张适配，颜色打印可见

## 安装

```bash
pip install chardet
pip install opencc-python-reimplemented  # 可选，简繁转换
pip install python-docx                   # 可选，DOCX支持
```

## 快速开始

```bash
# 构建字典
python scripts/stele_annotator.py "张迁碑.doc" --save-dict zhangqian_dict.json

# 单字典标注
python scripts/stele_annotator.py --dict zhangqian_dict.json 肥致碑.doc -o 肥致碑_标注版.html

# 多字典标注
python scripts/stele_annotator.py --dict 张迁碑.json,鲜于璜碑.json 肥致碑.doc -o 肥致碑_多字典版.html
```

## 文件结构

```
stele-annotator-v3/
├── SKILL.md                    # 详细文档
├── README.md                   # 本文件
└── scripts/
    ├── stele_annotator.py      # 主脚本
    ├── word_reader.py          # Word读取模块
    ├── converter.py            # 简繁转换模块
    └── data/
        ├── s2t.json            # 简转繁映射
        └── t2s.json            # 繁转简映射
```

## 文档

详细使用说明请参阅 [SKILL.md](./SKILL.md)

## License

MIT
