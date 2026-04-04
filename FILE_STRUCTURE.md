# stele-companion 项目文件结构说明

## 📁 文件分类总览

| 分类 | 文件数 | 大小 | 用途 |
|:---:|:---:|:---:|:---|
| **项目文档** | 4个 | ~3KB | 项目说明、许可证、配置 |
| **使用文档** | 1个 | ~18KB | AI技能使用指南 |
| **源代码** | 7个 | ~63KB | 程序核心功能 |
| **测试文件** | 6个 | ~17KB | 开发测试用（用户不需要）|

---

## 【第一类】项目文档（必需）

| 文件 | 大小 | 说明 |
|:---|:---:|:---|
| `README.md` | 766B | 📘 项目说明、快速开始 |
| `LICENSE` | 1.0KB | 📄 MIT 许可证 |
| `pyproject.toml` | 1.2KB | ⚙️ 包配置（包名、依赖、入口）|
| `requirements.txt` | 175B | 📋 依赖列表 |

**用途**：安装和使用必需的文件

---

## 【第二类】使用文档（必需）

| 文件 | 大小 | 说明 |
|:---|:---:|:---|
| `docs/SKILL.md` | 18KB | 📖 详细使用指南、命令参考 |

**用途**：AI 助手加载技能时使用的文档，包含完整的功能说明和命令示例

---

## 【第三类】源代码（核心）

| 文件 | 大小 | 功能说明 |
|:---|:---:|:---|
| `stele_companion/__init__.py` | 644B | 📦 包入口，导出主要函数 |
| `stele_companion/cli.py` | 9.6KB | 🖥️ 命令行入口，参数解析 |
| `stele_companion/core.py` | 14KB | 🧠 核心逻辑（字典构建、标注）|
| `stele_companion/io.py` | 4.5KB | 📁 文件读写模块 |
| `stele_companion/network.py` | 4.7KB | 🌐 网络获取碑帖原文 |
| `stele_companion/render.py` | 18KB | 🎨 HTML 渲染（横版/竖版）|
| `stele_companion/utils.py` | 12KB | 🛠️ 工具函数和常量 |

**用途**：程序的核心功能实现

---

## 【第四类】测试文件（可选）

| 文件 | 大小 | 说明 |
|:---|:---:|:---|
| `tests/__init__.py` | 0B | 测试包标记 |
| `tests/test_integration.py` | 12KB | 集成测试代码 |
| `tests/fixtures/张迁碑.txt` | 399B | 测试数据（碑文）|
| `tests/fixtures/肥致碑.txt` | 315B | 测试数据（碑文）|
| `tests/fixtures/张迁碑_dict.json` | 2.5KB | 测试数据（字典）|
| `tests/fixtures/肥致碑_dict.json` | 2.2KB | 测试数据（字典）|

**用途**：开发时运行测试，确保功能正常

**普通用户不需要这些文件**

---

## 🚀 用户使用方式

### 方式一：pip 安装（推荐）

**需要文件**：第一、二、三类（除 tests）

```bash
pip install .
stele-companion all 碑文.doc --dict 字典.json
```

### 方式二：直接运行（开发）

**需要文件**：第一、二、三类全部

```bash
python -m stele_companion.cli all 碑文.doc --dict 字典.json
```

---

## 📊 统计

| 场景 | 所需文件 | 总大小 |
|:---|:---|:---:|
| **pip 安装使用** | 项目文档 + 使用文档 + 源代码 | ~66KB |
| **开发测试** | 全部文件 | ~83KB |
| **仅发布包** | 项目文档 + 源代码 | ~48KB |

---

*最后更新：2026-04-04*
