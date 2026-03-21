---
name: stele-annotator
description: 碑文字標注器 v4.2。支持多字典對照標注、多字典共有字深紫色標識、段落格式保留、簡繁轉換匹配、多主題輸出、打印優化。適用於：(1) 從任意碑文文件構建字-標號字典，(2) 多字典同時對照標注，(3) 多字典共有字以深紫色標識，(4) 段落格式正確保留，(5) 簡繁體智能匹配，(6) 批量處理目錄，(7) 專業打印輸出。當用戶需要對碑文文本進行字標注、構建字典、多字典對照、簡繁轉換時使用此 skill。
---

# 碑文字标注器 v4.2

## v4.2 新增功能

| 新增项 | 说明 |
|--------|------|
| **段落格式保留** | 原文段落结构正确显示，不再压缩成一行 |
| **多字典共有颜色** | 深紫色(#4a0080)，视觉最突出 |

## v4.1 功能

| 新增项 | 说明 |
|--------|------|
| **多字典共有标识** | 同一字在多个字典中同时出现时，使用第三种特殊颜色标识 |
| **共有字统计** | 统计并显示多字典共有字的数量和比例 |

## v4.0 功能

| 新增项 | 说明 |
|--------|------|
| **多字典支持** | 同时加载多个字典，颜色区分不同字典的标注 |
| **简繁转换** | 启用后简体字可匹配繁体字典，反之亦然 |
| **字典颜色自动分配** | 多字典时自动分配不同颜色，最多预定义 8 种，超出自动生成 |
| **打印优化** | 多字典紧凑布局、字号适配 A4 纸张 |

## v3.2 功能

| 特性 | 说明 |
|------|------|
| 双主题支持 | `classic`（经典黄）和 `elegant`（典雅红） |
| 打印优化 | 页眉页脚、分页控制、字号适配 |
| Google Fonts | 典雅主题使用在线书法字体 |

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 多格式支持 | HTML、TXT、DOC（Word 97-2003）、DOCX（Word 2007+） |
| 跨平台 | Windows（win32com）、macOS/Linux（LibreOffice / python-docx） |
| 自动编码检测 | UTF-8、GBK、BIG5 等 |
| 多字典对照 | 同时使用多个字典标注，颜色区分 |
| 简繁转换匹配 | 简体字匹配繁体字典，繁体字匹配简体字典 |
| 批量断点续处理 | --resume 跳过已处理文件 |
| 三轮校验 | 标记正确性、标记完整性、标号一致性 |
| 打印友好 | A4 纸张优化，多颜色打印可见 |

---

## 文件结构

```
stele-annotator-v3/
├── SKILL.md                    # 本文档
└── scripts/
    ├── stele_annotator.py      # 主脚本 v4.2
    ├── word_reader.py          # Word 文件读取模块
    ├── converter.py            # 简繁转换模块
    └── data/
        ├── s2t.json            # 简转繁映射表
        └── t2s.json            # 繁转简映射表
```

---

## 依赖

**Python 版本要求：3.7+**

```bash
# 必需
pip install chardet           # 编码检测

# 可选
pip install opencc             # 专业简繁转换（推荐）
pip install python-docx        # DOCX 支持
pip install pywin32            # DOC 支持 Windows
```

---

## 使用方法

### 1. 构建字典

```bash
# 从 Word 文件构建
python scripts/stele_annotator.py "张迁碑.doc" --save-dict zhangqian_dict.json

# 从其他格式构建
python scripts/stele_annotator.py "曹全碑.html" --save-dict caoshan_dict.json
```

### 2. 单字典标注

```bash
# 基础用法
python scripts/stele_annotator.py --dict zhangqian_dict.json 肥致碑.doc -o 肥致碑_标注版.html

# 指定主题
python scripts/stele_annotator.py --dict zhangqian_dict.json 肥致碑.doc --theme elegant
```

### 3. 多字典标注（v4.0 新功能）

```bash
# 多字典逗号分隔，自动颜色区分
python scripts/stele_annotator.py --dict 张迁碑.json,鲜于璜碑.json 肥致碑.doc -o 肥致碑_多字典版.html
```

**多字典颜色分配**:

| 序号 | 颜色 | 说明 |
|------|------|------|
| 1 | #b8860b | 古铜金 |
| 2 | #a63d2f | 朱砂红 |
| 3 | #2d5a27 | 松石绿 |
| 4 | #1a4a7a | 靛青蓝 |
| 5+ | 自动生成 | HSL 色轮 |

**多字典共有颜色**:

| 颜色 | 说明 |
|------|------|
| #4a0080 | 深紫色 - 同一字在多个字典中同时出现（视觉最突出） |

### 4. 简繁转换（v4.0 新功能）

```bash
# 启用简繁转换匹配（简体可匹配繁体字典）
python scripts/stele_annotator.py --dict 张迁碑.json 肥致碑.doc --convert

# 输出简体版本
python scripts/stele_annotator.py --dict 张迁碑.json 肥致碑.doc --output-encoding simplified

# 输出繁体版本
python scripts/stele_annotator.py --dict 张迁碑.json 肥致碑.doc --output-encoding traditional
```

### 5. 批量处理

```bash
# 批量处理目录
python scripts/stele_annotator.py --dict 张迁碑.json --batch ./input/ --output-dir ./output/

# 断点续处理
python scripts/stele_annotator.py --dict 张迁碑.json --batch ./input/ --output-dir ./output/ --resume
```

### 6. 检查环境

```bash
python scripts/stele_annotator.py --check
```

---

## 命令行选项

| 选项 | 说明 |
|------|------|
| `source` | 字典源文件（位置参数） |
| `input` | 待标注文件（位置参数） |
| `-o, --output` | 输出文件路径 |
| `--dict` | 使用字典 JSON 文件（多字典用逗号分隔） |
| `--save-dict FILE` | 从源文件构建字典并保存为 JSON |
| `--batch DIR` | 批量处理输入目录 |
| `--output-dir` | 批量处理输出目录（默认 `./output/`） |
| `--recursive` | 递归处理子目录 |
| `--resume` | 断点续处理（跳过已成功文件） |
| `--check` | 检查环境和 Word 读取能力 |
| `--no-verify` | 跳过三轮校验 |
| `--theme` | 输出主题：`classic` 或 `elegant` |
| `--convert` | 启用简繁转换匹配 |
| `--output-encoding` | 输出编码：`none`/`simplified`/`traditional`/`dual` |

---

## 简繁转换说明

### 工作原理

1. **匹配阶段**：启用 `--convert` 后，简体字可匹配繁体字典中的对应字，反之亦然
2. **转换库**：优先使用 `opencc`（专业级），未安装时回退内置映射表（约 3000 常用字）

### 转换模式

| 模式 | 说明 |
|------|------|
| `none` | 原样输出（默认） |
| `simplified` | 输出简体版本 |
| `traditional` | 输出繁体版本 |
| `dual` | 输出简繁对照版本 |

---

## 输出特性

- **多字典颜色区分**：不同字典的标注用不同颜色
- **统计信息**：显示每个字典的匹配率和总体匹配情况
- **响应式布局**：移动端适配
- **A4 打印优化**：字号自动适配，颜色打印可见
- **页眉页脚**：打印版自动添加碑名和页码

---

## 字典 JSON 格式

```json
{
  "source": "张迁碑",
  "char_count": 375,
  "version": "4.0",
  "created": "2026-03-21T15:30:00",
  "mappings": {
    "君": "1-1",
    "讳": "1-2",
    "迁": "1-3"
  }
}
```

---

## 示例输出

### 多字典标注效果

```
已标注 188 个不同汉字（28.9%），启用简繁转换匹配

图例：
  [金] 《张迁碑》
  [红] 《鲜于璜碑》
  [紫] 多字典共有

统计：
  正文总字数：651
  多字典共匹配：188 字（28.9%）
  多字典共有字：45 字（6.9%）
  《张迁碑》匹配：120 字（18.4%）
  《鲜于璜碑》匹配：156 字（24.0%）
```

### 颜色说明

- **古铜金 #b8860b**：仅在《张迁碑》中出现的字
- **朱砂红 #a63d2f**：仅在《鲜于璜碑》中出现的字
- **深紫色 #4a0080**：在两个字典中同时出现的字（多字典共有，最突出）
