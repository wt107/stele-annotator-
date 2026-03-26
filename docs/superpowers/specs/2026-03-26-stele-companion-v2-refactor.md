# stele-companion v2.0 重构设计

**创建日期**: 2026-03-26
**状态**: 已批准，待实施

## 目标

将 stele-companion 从单文件脚本重构为标准 Python 包，并添加集成测试以保证稳定性和可用性。

## 架构

### 项目结构

```
stele-companion/
├── stele_companion/           # 主包
│   ├── __init__.py           # 包入口，导出主要函数
│   ├── network.py            # 网络获取模块
│   ├── io.py                 # 文件读写模块
│   ├── core.py               # 核心业务模块
│   ├── render.py             # HTML 渲染模块
│   ├── cli.py                # 命令行入口
│   └── utils.py              # 工具函数和常量
├── tests/                     # 测试目录
│   ├── __init__.py
│   ├── test_integration.py   # 集成测试
│   └── fixtures/             # 测试数据
├── docs/
│   └── SKILL.md              # 使用文档
├── pyproject.toml            # 包配置
├── requirements.txt
└── README.md
```

### 模块职责

| 模块 | 职责 | 主要函数 |
|------|------|----------|
| `network.py` | 从权威来源获取碑帖原文段落信息 | `fetch_stele_text`, `_fetch_wikisource`, `_fetch_yamoke` |
| `io.py` | 文件读写 | `read_input`, `_read_txt`, `_read_word`, `_read_docx` |
| `core.py` | 核心业务逻辑 | `build_dict`, `annotate`, `_merge_paragraphs`, `_split_stele_paragraphs` |
| `render.py` | HTML 渲染 | `render_html`, `_render_horizontal`, `_render_vertical` |
| `cli.py` | 命令行接口 | `main`, `run_all` |
| `utils.py` | 工具函数和常量 | `log_*`, `to_traditional`, `to_simplified`, `_is_cjk_char`, `VARIANT_MAP` |

### 数据流

```
CLI 入口 (cli.py)
      │
      ├─────────────────────────────────┐
      ▼                                 ▼
网络层 (network.py)              IO 层 (io.py)
获取权威碑帖原文段落             读取本地文件内容
      │                                 │
      │   input_paragraphs              │   paragraphs
      │   (网络段落 or None)             │   (本地文件段落)
      └───────────────┬─────────────────┘
                      ▼
              核心层 (core.py)
        ┌───────────────────────────────┐
        │ annotate() 数据源选择逻辑:     │
        │   if input_paragraphs:        │
        │       使用网络获取的权威段落   │
        │   else:                       │
        │       使用本地文件读取的段落   │
        └───────────────────────────────┘
        build_dict() → 字典 JSON
        annotate()   → 标注数据 JSON
                      │
                      ▼
              渲染层 (render.py)
        render_html() → 横版/竖版 HTML
```

## 技术栈

- Python 3.8+
- python-docx: Word 文件读取
- chardet: 编码检测
- requests: 网络请求
- pytest: 测试框架

## 测试设计

### 测试数据

使用真实碑帖数据：
- 张迁碑.docx / 张迁碑_dict.json
- 肥致碑.docx / 肥致碑_dict.json

### 集成测试用例

```python
class TestBuildDict:
    - test_build_dict_from_docx
    - test_build_dict_from_txt
    - test_start_marker
    - test_dict_structure

class TestAnnotate:
    - test_annotate_single_dict
    - test_annotate_multi_dict
    - test_shared_chars
    - test_simplified_traditional_convert

class TestRender:
    - test_render_horizontal
    - test_render_vertical
    - test_html_escaping
    - test_font_sizes

class TestFullWorkflow:
    - test_full_workflow_all_command
    - test_fetch_mode
```

## 安装方式

```bash
pip install stele-companion
stele-companion all 肥致碑.docx --dict 张迁碑_dict.json
```

## 实施步骤

1. 创建新包结构
2. 拆分代码到各模块
3. 创建测试目录和测试数据
4. 编写集成测试
5. 配置 pyproject.toml
6. 验证安装和测试

## 兼容性

- 仅支持新接口
- 不保留旧版命令行入口
- 版本号升级为 2.0.0
