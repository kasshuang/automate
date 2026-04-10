# AutoMate - AI驱动的电脑自动化工具

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-orange.svg" alt="Platform">
  <img src="https://img.shields.io/badge/AI-Agent-Ready-purple.svg" alt="AI Ready">
</p>

> 🤖 用自然语言控制电脑，让AI帮你完成重复性工作

## ✨ 特性

- 🖱️ **智能点击** - AI识别UI元素，自动规划点击路径
- ⌨️ **自然语言控制** - 说"帮我上架闲鱼商品"，AI自动执行
- 🎬 **录制备忘** - 录制一次，永久回放
- 🔌 **插件市场** - 电商、内容、办公...垂直场景一键安装
- 🤝 **多Agent协作** - 多个AI专家分工合作

## 🚀 快速开始

### 安装
```bash
pip install automatelib
```

### 方式1：命令行
```bash
# 执行预设任务
automate run publish_article --title "我的文章" --content "正文..."

# 执行自定义步骤
automate run --steps steps.json

# 查看帮助
automate --help
```

### 方式2：图形界面
```bash
automate gui
```

### 方式3：作为Agent工具
```python
from automatelib import AutoMate

am = AutoMate()
am.execute("帮我上架闲鱼商品，标题：二手iPhone 13，价格：3999")
```

## 📖 使用场景

### 电商运营
```bash
automate run list_xianyu \
  --title "iPhone 13 99新" \
  --price 3999 \
  --description "使用3个月，无划痕"
```

### 内容发布
```bash
automate run publish_article \
  --platform wechat \
  --title "深度好文" \
  --content "$(cat article.md)"
```

### 办公自动化
```bash
automate run fill_excel \
  --file data.xlsx \
  --template template.json
```

## 🏗️ 架构

```
┌─────────────────────────────────────────┐
│           🧠 AutoMate Agent             │
│   (理解自然语言 → 拆解任务 → 分配工作)   │
└──────────────────┬──────────────────────┘
                   │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Browser │ │ Desktop │ │  File   │
│ Executor│ │ Executor│ │ Executor │
└────┬────┘ └────┬────┘ └────┬────┘
     │            │            │
     └────────────┴────────────┘
                   │
              🖥️ Windows
```

## 📦 插件系统

安装插件：
```bash
automate install ecommerce      # 电商插件
automate install content       # 内容运营插件
automate install social        # 社交媒体插件
```

## 🔧 配置

```yaml
# automaterc.yaml
executor:
  desktop:
    delay: 0.5
    failsafe: true
  browser:
    headless: false
agent:
  provider: openai  # openai / claude / 本地
  model: gpt-4
  api_key: your-key
```

## 📝 开发

```bash
# 克隆仓库
git clone https://github.com/yourname/automate.git
cd automate

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 启动GUI
python -m automatelib.gui
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🌟 Roadmap

- [x] Phase 1: 核心框架 + CLI
- [x] Phase 2: GUI界面
- [ ] Phase 3: Agent集成（自然语言控制）
- [ ] Phase 4: 插件市场
- [ ] Phase 5: 云端Agent服务

---

<p align="center">
  <strong>用AI释放双手，让电脑自动干活 🚀</strong>
</p>
