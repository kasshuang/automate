# AutoMate PyPI 包描述

> 用于 `setup.py` / `pyproject.toml` 的 `long_description`
> 格式：Markdown，PyPI 支持完整 Markdown 渲染
> 目标：搜索关键词命中 + 第一眼说服用户安装

---

## 文件内容（直接复制到 README.md 或 PyPI Description 字段）

---

# AutoMate 🤖 — AI驱动的PC自动化工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://pypi.org/project/automatelib/)
[![Platform](https://img.shields.io/badge/Platform-Windows-orange.svg)](https://github.com/kasshuang/automate)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-v0.1.0-purple.svg)](https://pypi.org/project/automatelib/)

> **用自然语言控制电脑，让AI帮你完成重复性工作。**

比 RPA 更智能，比纯 AI Agent 更落地。

---

## ✨ 特性

| 特性 | 说明 |
|------|------|
| 💬 **自然语言驱动** | 一句话，AI 自动规划并执行操作 |
| 👁️ **智能UI识别** | 视觉模型定位按钮、输入框、下拉菜单 |
| 🎬 **录制备忘** | 手动操作一遍，永久回放自动化 |
| 🔌 **插件市场** | 电商、内容、办公垂直场景一键安装 |
| 🤝 **多Agent协作** | 多个AI专家分工合作完成复杂任务 |
| 🖥️ **跨应用支持** | 浏览器、桌面应用、文件系统全覆盖 |

---

## 🚀 快速开始

### 安装

```bash
pip install automatelib
```

### 三种使用方式

**方式 1：命令行**

```bash
# 执行预设任务
automate run "上架闲鱼商品"

# 指定参数
automate run publish_xianyu --title "二手iPhone 13" --price 3999

# 查看帮助
automate --help
```

**方式 2：图形界面（GUI）**

```bash
automate gui
```
启动可视化界面，点点点就能用。

**方式 3：Python API**

```python
from automatelib import AutoMate

am = AutoMate()

# 自然语言任务
am.execute("帮我上架闲鱼商品，标题：二手iPhone 13，价格：3999")

# 指定步骤
am.run_steps([
    {"action": "open_url", "url": "https://www.xianyu.com"},
    {"action": "click", "target": "发布按钮"},
    {"action": "type", "target": "标题输入框", "text": "二手iPhone 13"},
    {"action": "type", "target": "价格输入框", "text": "3999"},
    {"action": "click", "target": "发布按钮"},
])
```

---

## 💼 典型使用场景

### 电商运营

```bash
# 闲鱼商品上架
automate run list_xianyu \
  --title "iPhone 13 99新" \
  --price 3999 \
  --description "使用3个月，无划痕，原装充电器"

# 批量发布
automate run batch_publish \
  --platform xianyu \
  --file products.csv
```

### 内容创作

```bash
# 公众号文章发布
automate run publish_wechat \
  --title "深度好文" \
  --content "$(cat article.md)" \
  --cover "$(cat cover.png)"

# 批量图片处理
automate run batch_watermark \
  --dir ./images \
  --watermark "© YourBrand"
```

### 办公自动化

```bash
# Excel 数据填充
automate run fill_excel \
  --file data.xlsx \
  --template template.json

# 文件批量整理
automate run organize_files \
  --source ./downloads \
  --rule "按类型分类"
```

---

## 🏗️ 架构

```
AutoMate 架构

┌─────────────────────────────────────────────┐
│           🧠 AutoMate Agent                 │
│   (自然语言理解 → 任务拆解 → 智能规划)       │
└────────────────────┬────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Browser  │  │ Desktop  │  │  File    │
│ Executor │  │ Executor │  │ Executor │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │
     └──────────────┴──────────────┘
                     │
                🖥️ Windows PC
```

**三大执行器：**

- **Browser Executor**：浏览器自动化，元素识别，表单填写，页面操作
- **Desktop Executor**：Windows GUI 自动化，鼠标键盘控制，窗口管理
- **File Executor**：文件系统操作，文件读写，批量处理

---

## 🔧 配置

创建 `automaterc.yaml` 配置文件：

```yaml
# automaterc.yaml
executor:
  desktop:
    delay: 0.5        # 操作间隔（秒）
    failsafe: true    # 紧急情况下鼠标移到角落中止
    screenshot_on_error: true
  browser:
    headless: false  # 是否无头模式运行
    timeout: 30

agent:
  provider: openai   # openai / claude / 本地模型
  model: gpt-4
  api_key: your-api-key
  temperature: 0.1

logging:
  level: INFO
  file: automate.log
```

---

## 📦 插件系统

```bash
# 安装插件
automate install ecommerce   # 电商插件（闲鱼/淘宝/拼多多）
automate install content    # 内容运营插件（公众号/小红书）
automate install office     # 办公自动化插件（Excel/Word/PPT）

# 查看已安装插件
automate plugin list

# 卸载插件
automate uninstall ecommerce
```

---

## 📋 支持的环境

| 组件 | 要求 |
|------|------|
| Python | 3.8+ |
| 操作系统 | Windows 10/11 |
| 依赖库 | pywin32, pyautogui, Pillow, mss |
| 可选（AI） | openai, anthropic |

---

## 🔒 安全说明

- `failsafe: true` 时，移动鼠标到屏幕四角可立即停止所有操作
- 所有操作均在本地执行，无数据上传
- API Key 仅用于调用 LLM，不存储或传输到第三方

---

## 🤝 参与贡献

```bash
# 克隆项目
git clone https://github.com/kasshuang/automate.git
cd automate

# 安装开发版本
pip install -e ".[dev]"

# 运行测试
pytest

# 启动 GUI
python -m automatelib.gui
```

Issues 和 Pull Requests 欢迎！

---

## 📄 许可证

MIT License — 可免费商用，欢迎贡献。

---

**GitHub**: [github.com/kasshuang/automate](https://github.com/kasshuang/automate)
**PyPI**: [pypi.org/project/automatelib/](https://pypi.org/project/automatelib/)

---

*用AI释放双手，让电脑自动干活 🚀*
