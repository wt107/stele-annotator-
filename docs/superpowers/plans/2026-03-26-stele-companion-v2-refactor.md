# stele-companion v2.0 重构实施计划

**REQUIRED SUB-SKILL**: test-driven-development

## Goal

将 stele-companion 从单文件脚本重构为标准 Python 包，添加集成测试，确保稳定性和可用性。

## Architecture

```
stele-companion/
├── stele_companion/           # 主包
│   ├── __init__.py
│   ├── network.py
│   ├── io.py
│   ├── core.py
│   ├── render.py
│   ├── cli.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_integration.py
│   └── fixtures/
├── docs/
│   └── SKILL.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Tech Stack

- Python 3.8+
- python-docx, chardet, requests
- pytest, pytest-cov

---

## Tasks

### Phase 1: 创建包结构

#### Task 1.1: 创建 stele_companion 包目录
- 创建 `stele_companion/` 目录
- 创建 `stele_companion/__init__.py`
- 验证: 目录结构存在

#### Task 1.2: 创建 tests 目录结构
- 创建 `tests/` 目录
- 创建 `tests/__init__.py`
- 创建 `tests/fixtures/` 目录
- 验证: 目录结构存在

---

### Phase 2: 拆分代码

#### Task 2.1: 创建 utils.py
- 文件: `stele_companion/utils.py`
- 内容: 常量定义、VARIANT_MAP、TRAD_TO_SIMP、ROTATE_CHARS、PUNCTUATION、DICT_COLORS、SHARED_COLOR、STELE_SOURCES、终端颜色类 C、日志函数、简繁转换函数、`_is_cjk_char` 函数
- 验证: `python -c "from stele_companion.utils import VARIANT_MAP, log_ok"`

#### Task 2.2: 创建 network.py
- 文件: `stele_companion/network.py`
- 内容: `_extract_stele_name`, `_fetch_wikisource`, `_fetch_yamoke`, `fetch_stele_text`
- 依赖: 从 utils 导入 log_*
- 验证: `python -c "from stele_companion.network import fetch_stele_text"`

#### Task 2.3: 创建 io.py
- 文件: `stele_companion/io.py`
- 内容: `read_input`, `_read_txt`, `_read_word`, `_read_docx`, `_read_doc_platform`, `_read_doc_win32`, `_read_doc_libreoffice`
- 依赖: 从 utils 导入 log_*
- 验证: `python -c "from stele_companion.io import read_input"`

#### Task 2.4: 创建 core.py
- 文件: `stele_companion/core.py`
- 内容: `build_dict`, `annotate`, `_find_start_index`, `_merge_paragraphs`, `_clean_line_prefix`, `_split_stele_paragraphs`
- 依赖: 从 utils 导入常量和日志函数，从 io 导入 read_input
- 验证: `python -c "from stele_companion.core import build_dict, annotate"`

#### Task 2.5: 创建 render.py
- 文件: `stele_companion/render.py`
- 内容: `render_html`, `_render_horizontal`, `_render_vertical`, `_font_size_css`, `THEME_COLORS`
- 依赖: 从 utils 导入常量和日志函数
- 验证: `python -c "from stele_companion.render import render_html"`

#### Task 2.6: 创建 cli.py
- 文件: `stele_companion/cli.py`
- 内容: `main`, `run_all`
- 依赖: 导入所有其他模块
- 验证: `python -c "from stele_companion.cli import main"`

#### Task 2.7: 完善 __init__.py
- 文件: `stele_companion/__init__.py`
- 内容: 导出主要函数，定义 `__version__`
- 验证: `python -c "import stele_companion; print(stele_companion.__version__)"`

---

### Phase 3: 创建测试数据

#### Task 3.1: 创建测试碑帖文件
- 创建 `tests/fixtures/张迁碑.txt` (简化版，约50字)
- 创建 `tests/fixtures/肥致碑.txt` (简化版，约50字)
- 验证: 文件存在且可读

#### Task 3.2: 生成测试字典
- 运行 build_dict 生成 `tests/fixtures/张迁碑_dict.json`
- 运行 build_dict 生成 `tests/fixtures/肥致碑_dict.json`
- 验证: JSON 文件有效，包含 mappings 字段

---

### Phase 4: 编写集成测试

#### Task 4.1: 编写 TestBuildDict 测试类
- 文件: `tests/test_integration.py`
- 测试: `test_build_dict_from_txt`, `test_start_marker`, `test_dict_structure`
- 验证: `pytest tests/test_integration.py::TestBuildDict -v`

#### Task 4.2: 编写 TestAnnotate 测试类
- 文件: `tests/test_integration.py`
- 测试: `test_annotate_single_dict`, `test_annotate_multi_dict`, `test_shared_chars`
- 验证: `pytest tests/test_integration.py::TestAnnotate -v`

#### Task 4.3: 编写 TestRender 测试类
- 文件: `tests/test_integration.py`
- 测试: `test_render_horizontal`, `test_render_vertical`, `test_html_escaping`
- 验证: `pytest tests/test_integration.py::TestRender -v`

#### Task 4.4: 编写 TestFullWorkflow 测试类
- 文件: `tests/test_integration.py`
- 测试: `test_full_workflow_all_command`
- 验证: `pytest tests/test_integration.py::TestFullWorkflow -v`

---

### Phase 5: 配置和验证

#### Task 5.1: 创建 pyproject.toml
- 文件: `pyproject.toml`
- 内容: 包元数据、依赖、入口点配置
- 验证: `pip install -e .` 成功

#### Task 5.2: 更新 requirements.txt
- 文件: `requirements.txt`
- 内容: 运行依赖和开发依赖分离
- 验证: `pip install -r requirements.txt` 成功

#### Task 5.3: 创建 README.md
- 文件: `README.md`
- 内容: 项目介绍、安装、使用方法
- 验证: 文件存在

#### Task 5.4: 运行完整测试
- 运行 `pytest tests/ -v`
- 验证: 所有测试通过

#### Task 5.5: 验证命令行入口
- 运行 `stele-companion --help`
- 验证: 显示帮助信息

---

## 约束

- 每个任务 2-5 分钟
- 每个任务完成后验证
- 遵循 TDD: 先写测试再实现
- 频繁提交

## 验收标准

- [ ] `pip install -e .` 成功
- [ ] `stele-companion --help` 显示帮助
- [ ] `pytest tests/` 所有测试通过
- [ ] `import stele_companion` 可正常导入
