---
name: stele-companion
description: |
  碑帖学习伴侣 v1.4。碑文字典对照 + 标注排版工具，支持多字典彩色对照、简繁转换、横版/竖版HTML输出、A4打印优化、自动获取权威碑帖原文。触发词：
  碑文标注、碑帖学习、字典对照、字-标号对照、简繁转换、碑文排版、横版输出、竖版输出、
  标注碑文、碑文字典、学习书法、碑刻对照、多字典对照、碑文打印版、打印临摹、碑帖临摹、字帖打印。
compatibility: Python 3.8+, python-docx, chardet, requests
---

# 碑帖学习伴侣 stele-companion v1.4

合并自 stele-annotator (v4.2) × stele-vertical-layout (v1.1)

## 核心定位

为碑文书法学习者提供**标准化的字-编号对照标注流程**，输出稳定、格式一致、可打印。

```
输入：碑文文件(.doc/.docx/.txt) + 字典JSON
        ↓
处理：三步标准化流程（建字典→标注文本→渲染输出）
        ↓
输出：横版 HTML + 竖版 HTML（含 A4 打印优化）
```

---

## 工作流程

| 步骤 | 命令 | 说明 |
|:---:|:---|:---|
| **建字典** | `build-dict` | 从标准碑帖文档建立字-编号字典 |
| **标注文本** | `annotate` | 多字典彩色对照标注 |
| **渲染输出** | `render` | 横版/竖版 HTML |
| **完整流程** | `all` | 一步完成（推荐） |

---

## 快速开始

### 推荐用法：`all` 一步完成

```bash
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json \
    --output-horizontal 肥致碑_横版.html \
    --output-vertical 肥致碑_竖版.html \
    --start-marker "从事君之元嗣" \
    --font-size medium \
    --theme classic
```

### 第一步：建字典

```bash
python stele_companion.py build-dict 张迁碑.docx \
    -o zhangqian_dict.json \
    --start-marker "君讳迁"
```

### 第二步：标注文本

```bash
python stele_companion.py annotate 肥致碑.doc \
    --dict zhangqian_dict.json \
    -o annotated.json
```

### 第三步：渲染 HTML

```bash
# 横版（现代阅读顺序，A4纵向）
python stele_companion.py render \
    --annotated annotated.json \
    --format horizontal \
    --font-size medium \
    -o 肥致碑_横版.html

# 竖版（古文阅读顺序，A4横向）
python stele_companion.py render \
    --annotated annotated.json \
    --format vertical \
    --font-size medium \
    -o 肥致碑_竖版.html
```

---

## 命令行选项详解

### `build-dict`（建字典）

| 选项 | 必选 | 说明 |
|:---|:---:|:---|
| `input` | ✅ | 输入文件（.doc/.docx/.txt） |
| `-o, --output` | ✅ | 输出字典文件（.json） |
| `--start-line N` | | 正文起始行号（1-based） |
| `--start-marker TEXT` | | 正文起始关键字（与start-line二选一） |
| `--variant` | | `simplified`（默认）/ `traditional` |

### `annotate`（标注）

| 选项 | 必选 | 说明 |
|:---|:---:|:---|
| `input` | ✅ | 待标注文件（.doc/.docx/.txt） |
| `--dict` | ✅ | 字典文件（多个用逗号分隔） |
| `-o, --output` | ✅ | 输出标注数据（.json） |
| `--start-line N` | | 正文起始行号 |
| `--start-marker TEXT` | | 正文起始关键字 |
| `--convert` | | 启用简繁转换匹配 |

### `render`（渲染）

| 选项 | 必选 | 说明 |
|:---|:---:|:---|
| `--annotated` | ✅ | 标注数据文件（.json） |
| `-o, --output` | ✅ | 输出 HTML 文件 |
| `--format` | | `horizontal`（默认）/ `vertical` |
| `--font-size` | | `small`(22px) / `medium`(28px) / `large`(34px) |
| `--theme` | | `classic`（金色系）/ `elegant`（红色系） |

### `all`（完整流程）

| 选项 | 必选 | 说明 |
|:---|:---:|:---|
| `input` | ✅ | 待标注碑文文件（支持碑帖名称自动获取正文） |
| `--dict` | ✅ | 字典文件（多个用逗号分隔） |
| `--output-horizontal` | | 横版 HTML 输出路径 |
| `--output-vertical` | | 竖版 HTML 输出路径 |
| `--annotated` | | 标注数据 JSON 路径（可选） |
| `--start-marker` | | 正文起始关键字 |
| `--font-size` | | `small` / `medium`（默认） / `large` |
| `--theme` | | `classic`（默认） / `elegant` |
| `--convert` | | 启用简繁转换匹配 |
| `--fetch` | | 自动从网络获取权威碑帖原文（替代文件内段落） |
| `--source` | | 数据源：`wikisource` / `yamoke` / `auto`（默认） |

---

## 多字典彩色对照

多个字典用逗号分隔，自动分配不同颜色：

```bash
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json,鲜于璜碑_dict.json \
    --output-horizontal 肥致碑_多字典.html
```

**颜色分配规则：**

| 序号 | 颜色 | 名称 |
|:---:|:---|:---|
| 1 | #b8860b | 古铜金 |
| 2 | #a63d2f | 朱砂红 |
| 3 | #2d5a27 | 松石绿 |
| 4 | #1a4a7a | 靛青蓝 |

**多字典共有字**（同一字在多个字典中都出现）：使用 `#4a0080` 深紫色标识，视觉最突出。

---

## 自动获取碑帖原文（--fetch）

使用 `--fetch` 参数时，技能会从网络获取权威的碑帖原文，自动替代文件内可能不准确的段落。

### 用法

```bash
# 自动获取权威原文（推荐）
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json \
    --fetch \
    --output-horizontal 肥致碑_横版.html

# 指定数据源
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json \
    --fetch --source wikisource \
    --output-horizontal 肥致碑_横版.html
```

### 数据源

| 源 | 说明 | 适用碑帖 |
|:---|:---|:---|
| `auto`（默认） | 自动选择最优源 | 自动匹配 |
| `wikisource` | 维基文库，开放版权 | 张迁碑等 |
| `yamoke` | 雅墨客网，书法专业 | 肥致碑等 |

### 工作原理

1. 从文件名或用户输入提取碑帖名称（如"肥致碑"、"张迁碑"）
2. 在预置权威源中搜索匹配
3. 解析HTML获取原始分段
4. 自动清理无关内容，保留纯正文
5. 使用权威分段替代原文件内容

> **注意**：如果网络获取失败，会自动回退使用原文件内容。

---

## 字典 JSON 格式

```json
{
  "source": "张迁碑",
  "variant_base": "simplified",
  "paragraph_count": 15,
  "char_count": 375,
  "unique_chars": 300,
  "mappings": {
    "君": "1-1",
    "讳": "1-2",
    "迁": "1-3"
  },
  "variant_pairs": {
    "国": ["国", "國"]
  },
  "created": "2026-03-22T18:00:00",
  "version": "1.0"
}
```

---

## 标注数据 JSON 格式

```json
{
  "source": "肥致碑",
  "dicts": [
    {"source": "张迁碑", "color": "#b8860b", "matched_count": 120}
  ],
  "shared_chars": ["君", "讳"],
  "shared_color": "#4a0080",
  "paragraphs": [
    {
      "para_id": 1,
      "is_main": true,
      "chars": [
        {"char": "从", "matched": true, "labels": [{"dict_idx": 0, "label": "5-1", "color": "#b8860b"}]}
      ]
    }
  ],
  "stats": {
    "total": 500,
    "matched": 420,
    "match_rate": "84.0%"
  }
}
```

---

## HTML 输出样式规范

### 通用参数（medium 字号）

| 参数 | small | **medium**（默认） | large |
|:---|:---:|:---:|:---:|
| 字号 font-size | 22px | **28px** | 34px |
| 行高 line-height | 7.2mm | **8.5mm** | 10.2mm |
| 标号字号 | 7px | **8px** | 10px |

### 横版（horizontal）

- 阅读顺序：左→右，上→下（现代阅读）
- 纸张：A4 纵向 210×297mm
- 字位结构：字在上，标号在正下方（inline-flex 布局）
- `.page` padding：**15mm 四边统一**（屏幕版与打印版一致）
- `@page` margin：5mm
- 字间距：**1.0mm**（flex gap）
- 行间距：**5.0mm**（flex gap）
- 段落分隔：height 6mm + margin 2mm

### 竖版（vertical）

- 阅读顺序：上→下，右→左（古文阅读）
- 纸张：A4 横向 297×210mm
- 字位结构：字在上，标号在正下方（absolute 定位）
- `.page` padding：**10mm 上 / 10mm 左右 / 14mm 下**（屏幕版与打印版一致）
- `@page` margin：5mm
- 每列字数：**19 字**
- 每页列数：**20 列**
- 列间距：**6.0mm**（flex gap，充分填满页面宽度）
- 列内字间距：**0.5mm**（flex gap）
- 段落分隔列宽：min-width 3mm, margin 0 1mm

### 打印设置

1. 浏览器打开 HTML
2. Ctrl+P 打开打印
3. **横版**：A4 纵向，勾选「背景图形」
4. **竖版**：A4 横向，勾选「背景图形」
5. 边距设为「默认」（HTML 内部已控制边距）

> **设计原则**：屏幕版与打印版 `.page` padding 保持一致，确保所见即所得。

---

## 字号选择建议

| 字号 | 规格 | 适用场景 |
|:---:|:---|:---|
| small (22px) | 紧凑 | 多字碑文、需要打印多页 |
| **medium (28px)** | 均衡 | **一般学习用途（默认）** |
| large (34px) | 大字 | 老年学习者、打印临摹 |

---

## 简繁转换

启用 `--convert` 后，简体字可匹配繁体字典，繁体字可匹配简体字典：

```bash
python stele_companion.py all 肥致碑.doc \
    --dict 张迁碑_dict.json \
    --convert \
    -o 肥致碑_标注版.html
```

内置约 500+ 常用字简繁映射表（不依赖 opencc），覆盖碑刻常用字。

---

## 文件结构

```
stele-companion/
├── SKILL.md                    # 本文档
├── requirements.txt            # Python 依赖
└── scripts/
    └── stele_companion.py      # 统一入口脚本（v1.0）
```

---

## 依赖

```bash
# 必需
pip install python-docx chardet

# 可选（提升 .doc 读取能力）
pip install pywin32    # Windows .doc
# 或
# 安装 LibreOffice   # macOS/Linux .doc
```

---

## 踩坑经验与关键规则

> 以下规则来自实际使用中遇到的真实问题，**必须严格遵守**，否则会导致严重输出错误。

### ❌ 规则 1：禁止跨段合并 — 字典标号会全部错乱

**症状**：字典中出现 `3-104`、`1-280` 等异常标号（单段不可能有 100+ 字）。

**根因**：`_merge_paragraphs()` 未识别 `"1." "2."` 等序号标记，把末尾不是句号（如冒号 `：`、逗号 `，`）的段落和下一段错误合并。例如第 3/4/5 段（各约 30 字）被合并成 115 字的大段，导致标号全部偏移。

**强制规则**：
- `_merge_paragraphs()` **必须**检测段落序号标记（如 `1.` `2.` `10.`），遇到序号段落**立即停止合并**
- 检测正则：`r'^[\u4e00-\u9fff\u3400-\u4dbf]*\d{1,2}\.'`
- 合并后段落数必须与原始文档序号段落数一致

**校验标准**：合并后每段字数应在 20-50 字范围。出现 100+ 字的段落 = 严重错误。

### ❌ 规则 2：禁止 `@page { margin: 0 }` — 内容会被裁切

**症状**：打印时内容上下左右贴边，文字被打印机硬件裁切。

**根因**：打印机硬件有 3-5mm 不可打印区域，`margin: 0` 导致内容落入该区域。

**强制规则**：
- 打印 `@page` 必须设置 `margin: 5mm`
- 横版 `.page` padding：`15mm` 四边统一（屏幕版与打印版一致）
- 竖版 `.page` padding：`10mm 上 / 10mm 左右 / 14mm 下`（屏幕版与打印版一致）
- **设计原则**：屏幕版与打印版 padding 必须一致，确保所见即所得

### ❌ 规则 3：禁止竖版 `min-height: 210mm` — 每页后面多一页空白

**症状**：竖版打印时，每页内容后面多出一页空白页。

**根因**：`min-height: 210mm` + `padding: 10mm上+14mm下` → 总高 234mm > A4 横向 210mm，浏览器强制分页后产生空白页。

**强制规则**：
- 屏幕版 `min-height: 200mm`
- **打印版 `.page` 必须加 `min-height: auto`**，让 `@page` 纸张尺寸控制页面高度
- 竖版排版必须满足：`chars_per_col × (line_height + col_gap) < 可用高度（~176mm）`
  - medium 字号：每列 **19 字** × (8.5mm + 0.5mm) = 171mm < 176mm ✅
  - 每页 **20 列** × (字宽~9.78mm + 列间距6.0mm) = 315.6mm > 267mm(可用宽度) ❌

> **注意**：当前 20 列 × 6.0mm 间距可能超出 A4 横向可用宽度，实际使用时可能需要调整为更少列数（如 18 列）或更小间距（如 5.0mm）。

### ❌ 规则 4：禁止横版标号 `position: absolute` — 分页时字和标号分离

**症状**：横版打印第二页顶部出现第一页末尾字的标号（字在上一页，标号跑到下一页）。

**根因**：标号使用 `position: absolute; bottom: -2px` 溢出文字下方，浏览器分页时把字留在当前页、absolute 定位的标号溢出到下一页。

**强制规则**：
- 横版 `.char-wrap` **必须**使用 `display: inline-flex; flex-direction: column; align-items: center`
- 标号作为 flex 子元素参与正常文档流，分页时字和标号不会被拆开
- **禁止** `position: relative` + `.label { position: absolute; bottom: -2px }` 的写法

### ✅ 规则 5：生成字典后必须校验标号合理性

生成字典后，自动检查以下指标，异常则报错：
1. `paragraph_count` 是否与原始文档段落数一致
2. 所有标号中 `-` 后的数字不应超过单段字数（正常 < 50）
3. 抽查 5 个字的标号，确认段号和位号合理

### ❌ 规则 6：禁止按句号拆分段落 — 破坏原文结构

**症状**：碑文被拆分成 40-50 段，段落边界混乱，正文被句号切断。

**根因**：单行碑文文本（如"鲜于璜碑...博物馆。君讳璜...其颂曰...延熹八年...造。鲜于璜碑碑阴...唯君行操..."）被错误地按句号拆分，导致：
- 原本完整的正文被切碎成 30+ 段
- 赞词、落款等结构边界丢失
- 与碑文实际段落结构不符

**强制规则**：
- **必须**按照碑文结构标记拆分，**禁止**按句号、问号、感叹号拆分
- 拆分标记优先级：
  1. **碑阳标题**：`鲜于璜碑・碑阳释文...博物馆。`
  2. **碑阴标题**：`鲜于璜碑・碑阴释文...字`
  3. **赞词标记**：`其颂曰：...`（到落款之前）
  4. **落款标记**：`延熹八年...造。`
- 拆分后段落数应为 **5-8 段**（碑阳标题 + 正文 + 赞词 + 落款 + 碑阴标题 + 正文），**禁止**超过 10 段
- 正文部分保持完整，不拆分

**校验标准**：拆分后段落数在 5-10 范围内为正常。超过 10 段 = 严重错误。

---

## 版本历史

### v1.4（2026-03-24）
- **[新功能]** 自动获取碑帖原文（--fetch 参数），从权威来源获取
- **[新功能]** 支持指定数据源（--source 参数）：wikisource、yamoke、auto
- **[关键修复]** 修复 `--fetch` 参数在 `all` 命令中不生效的 bug
- **[安全修复]** 修复 XSS 安全漏洞，所有用户输入值均进行 HTML 转义
- **[健壮性]** 添加 JSON 解析异常处理，字典文件格式错误时给出明确提示
- **[健壮性]** 验证字典文件必须包含 `mappings` 字段
- **[健壮性]** 添加 `--start-line` 参数校验，必须大于 0
- **[健壮性]** 过滤空字典路径，防止尾部逗号导致的问题
- **[关键修复]** 段落合并后 main_start_idx 未同步更新bug
- **[关键修复]** 新增 `_clean_line_prefix()` 清除 `[0]` 等前缀标记

### v1.3（2026-03-24）
- **[安全修复]** 修复 XSS 安全漏洞，所有用户输入值均进行 HTML 转义
- **[健壮性]** 添加 JSON 解析异常处理，字典文件格式错误时给出明确提示
- **[健壮性]** 验证字典文件必须包含 `mappings` 字段
- **[健壮性]** 添加 `--start-line` 参数校验，必须大于 0
- **[健壮性]** 过滤空字典路径，防止尾部逗号导致的问题
- **[关键修复]** 修复段落合并/拆分后 main_start_idx 未同步更新的 bug（导致标号丢失）
- **[触发词]** 新增触发词：打印临摹、碑帖临摹、字帖打印

### v1.2（2026-03-22 ~ 03-23）
- **[关键修复]** 竖版打印 `.page` 加 `min-height: auto`，修复每页后面多一页空白
- **[关键修复]** 横版 `.char-wrap` 改为 `inline-flex` 布局，修复分页时字和标号分离
- **[段落拆分]** 新增 `_split_stele_paragraphs()` 函数，按碑文结构标记拆分单行文本
- **[段落拆分]** 禁止按句号拆分段落，避免破坏原文结构（规则6）
- **[布局优化]** 竖版列间距从 1.0mm 调整到 **6.0mm**，充分利用页面宽度
- **[布局优化]** 竖版每页列数从 26 列调整为 **20 列**
- **[布局优化]** 横版行间距从 1.0mm 调整到 **5.0mm**
- **[布局优化]** 竖版屏幕 `min-height` 从 210mm 降为 200mm
- **[排版重构]** 字间距统一为标准值 1.0mm（横版字间距），列内字间距 0.5mm
- **[排版重构]** 竖版每列 19 字
- **[排版重构]** 屏幕版与打印版 `.page` padding 完全统一（横版 15mm 四边，竖版 10/10/14/10）
- **[文档]** 踩坑经验新增规则6（禁止按句号拆分段落）
- **[文档]** 排版规范更新横版行间距、竖版列间距和列数参数
- 依赖：python-docx, chardet

### v1.1（2026-03-22）
- **[关键修复]** `_merge_paragraphs()` 增加序号段落检测，防止跨段合并导致标号异常
- **[关键修复]** 打印 `@page` 边距从 0 改为 5mm，解决内容贴边裁切问题
- **[布局优化]** medium 字号 line-height 从 9mm 调整为 8.5mm，修复竖版溢出变 2 页
- 打印时 `.page` padding 独立优化（横版 10mm、竖版 6-10mm）

### v1.0
- 合并 stele-annotator (v4.2) + stele-vertical-layout (v1.1)
- 统一输出格式：字-标号对照，标号在字正下方
- 支持多字典彩色对照 + 共有字深紫色标识
- 简繁转换内置（不依赖 opencc）
- 横版 + 竖版双输出，A4 打印优化
- 三种字号可选（small/medium/large）
- 双主题：classic（古典金）/ elegant（典雅红）
