"""
HybridAgent - 分层混合Agent架构
Phase 3+: 高级模型规划 + 简单模型执行 + 规则兜底

核心理念：
- 高级模型（大脑）：只做复杂分析、任务拆解、策略规划（调用1次）
- 简单模型（执行器）：执行具体操作步骤（调用N次）
- 规则引擎（兜底）：极简单任务直接规则匹配（0成本）

目标：用最低成本完成最高价值的PC自动化任务
"""
import json
import os
import re
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

import yaml
import pyautogui

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """任务复杂度等级"""
    TRIVIAL = "trivial"      # 极简单：规则直接匹配
    SIMPLE = "simple"        # 简单：少量步骤，小模型可处理
    COMPLEX = "complex"      # 复杂：多步骤、需要规划
    VERY_COMPLEX = "very_complex"  # 极复杂：多阶段、跨应用、需要战略思考


@dataclass
class ExecutionStep:
    """执行步骤"""
    order: int
    action: str              # click, type, press, hotkey, wait...
    target: str = ""         # 操作目标描述
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 置信度
    model_used: str = ""     # 用什么模型/规则执行
    description: str = ""    # 人类可读描述


@dataclass
class TaskPlan:
    """任务执行计划"""
    task: str                 # 原始任务描述
    complexity: TaskComplexity
    intent: str               # 意图理解
    steps: List[ExecutionStep] = field(default_factory=list)
    skills_needed: List[str] = field(default_factory=list)  # 需要调用的Skill
    estimated_steps: int = 0
    planning_model: str = ""
    execution_cost: str = ""  # 预估成本描述
    raw_plan: str = ""        # 原始规划输出


@dataclass
class HybridResult:
    """混合执行结果"""
    status: str               # success, partial, error
    task: str
    complexity: TaskComplexity
    steps_planned: int = 0
    steps_executed: int = 0
    results: List[Dict] = field(default_factory=list)
    cost_used: str = ""      # 实际使用的成本
    error: Optional[str] = None
    execution_log: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# 规则引擎 - 极简单任务兜底（0成本）
# ─────────────────────────────────────────────

class RuleEngine:
    """
    规则引擎 - 处理极简单任务
    成本：0 | 速度：最快 | 准确度：高
    """

    # 动作关键词 → 标准操作映射
    ACTION_PATTERNS = {
        # 点击类
        r"(打开?|启动|运行|开)(.+?)(?:软件|应用|程序|app)": "open_app",
        r"点击(.+)按钮": "click_button",
        r"点击(.*)图标": "click_icon",
        r"双击(.+)": "double_click",
        r"右键点击(.+)": "right_click",
        r"在(.+)上?点击": "click_element",
        
        # 输入类
        r"(在|向|往)(.+)中?输入(.+)": "type_in",
        r"输入(.+)": "type_text",
        r"在搜索框?中?输入(.+)": "search",
        
        # 键盘类
        r"按(下?)(.+?)键": "press_key",
        r"按(ctrl|cmd|alt|shift)\+(.+)": "hotkey",
        r"按回车": "press_enter",
        r"按(esc|escape|退出)": "press_esc",
        
        # 组合操作
        r"复制": "copy",
        r"粘贴": "paste",
        r"剪切": "cut",
        r"全选": "select_all",
        r"保存": "save",
        r"关闭": "close",
        r"刷新": "refresh",
        r"截图": "screenshot",
        
        # 窗口/应用
        r"切换到(.+)窗口": "switch_window",
        r"最小化": "minimize",
        r"最大化": "maximize",
        r"关闭当前窗口": "close_window",
    }

    # 常用应用快捷命令
    APP_SHORTCUTS = {
        r"记事本": "notepad",
        r"计算器": "calc",
        r"画图": "mspaint",
        r"浏览器|edge|chrome": "msedge",
        r"文件管理器|我的电脑|此电脑": "explorer",
        r"控制面板": "control",
        r"cmd|命令行|终端": "cmd",
        r"powershell": "powershell",
        r"剪映": "jianying",
        r"抖音": "douyin",
        r"小红书": "xiaohongshu",
        r"微信": "wechat",
        r"qq": "qq",
        r"钉钉": "dingtalk",
    }

    @classmethod
    def can_handle(cls, task: str) -> bool:
        """判断任务是否能被规则引擎处理"""
        task_lower = task.lower()
        
        # 检查是否匹配已知模式
        for pattern in cls.ACTION_PATTERNS:
            if re.search(pattern, task_lower):
                return True
        
        # 检查是否包含已知应用名
        for app_name in cls.APP_SHORTCUTS:
            if re.search(app_name, task_lower):
                return True
        
        return False

    @classmethod
    def _find_app(cls, task_lower: str) -> Optional[str]:
        """在任务中查找应用名称"""
        # 直接关键词匹配（避免regex复杂性问题）
        shortcuts = {
            "记事本": "notepad",
            "计算器": "calc",
            "画图": "mspaint",
            "浏览器": "msedge",
            "edge": "msedge",
            "chrome": "msedge",
            "文件管理器": "explorer",
            "我的电脑": "explorer",
            "此电脑": "explorer",
            "控制面板": "control",
            "cmd": "cmd",
            "命令行": "cmd",
            "终端": "cmd",
            "powershell": "powershell",
            "剪映": "jianying",
            "抖音": "douyin",
            "小红书": "xiaohongshu",
            "微信": "wechat",
            "qq": "qq",
            "钉钉": "dingtalk",
        }
        for name, shortcut in shortcuts.items():
            if name in task_lower:
                return shortcut
        return None
    
    @classmethod
    def _extract_action(cls, task: str) -> tuple:
        """
        提取任务的动作类型和关键参数
        返回 (action, target_text, extra_text)
        """
        task_lower = task.lower()
        
        # 打开应用: 打开/启动/运行 + 应用名
        # 匹配"打开记事本" "打开 浏览器" "打开edge" 等
        if any(kw in task_lower for kw in ["打开", "启动", "运行"]):
            # 提取"打开"后面的内容
            m = re.search(r'(?:打开|启动|运行)\s*(.+)', task_lower)
            if m:
                app_name = m.group(1).strip().rstrip("软件应用程序app")
                if app_name:
                    return ("open_app", app_name, "")
        
        # 点击按钮: 点击 + 按钮名
        click_match = re.search(r'(?:点击|点)(?:.+?)?([\w\u4e00-\u9fa5]{2,10})', task_lower)
        if click_match and "按钮" not in task_lower[:click_match.start()]:
            btn = click_match.group(1).strip()
            if btn and len(btn) > 1:
                return ("click_button", btn, "")
        
        # 输入文字: (在/向/往)...中输入 + 内容  或  直接"输入" + 内容
        type_match = re.search(r'(?:在|向|往)?(?:.+?)?输入\s*(.+?)(?:\s*$|\n)', task_lower)
        if type_match:
            text = type_match.group(1).strip()
            return ("type_text", text, "")
        # 直接"输入"开头
        if task_lower.strip().startswith("输入"):
            text = task_lower[2:].strip()
            return ("type_text", text, "")
        
        # 搜索: (在...中)?搜索 + 内容
        search_match = re.search(r'(?:在(?:.+?)?)?搜索\s*(.+?)(?:\s*$|\n)', task_lower)
        if search_match:
            return ("search", search_match.group(1).strip(), "")
        
        # 按键: 按 + 键名
        key_map = {
            "回车": "enter", "回车键": "enter",
            "esc": "esc", "escape": "esc", "退出": "esc",
            "空格": "space", "space": "space",
            "tab": "tab",
            "删除": "delete", "del": "delete",
            "上": "up", "下": "down", "左": "left", "右": "right",
            "page up": "pageup", "page down": "pagedown",
        }
        for name, key in key_map.items():
            if f"按{name}" in task_lower or f"按{name}键" in task_lower:
                return ("press_key", key, "")
        
        # 组合键: Ctrl/Alt/Shift + X
        hotkey_match = re.search(r'(ctrl|cmd|alt|shift)\s*\+\s*(\w)', task_lower)
        if hotkey_match:
            mod = hotkey_match.group(1)
            key = hotkey_match.group(2)
            key = {"c": "c", "v": "v", "a": "a", "x": "x", "z": "z", "s": "s", "f": "f"}.get(key, key)
            return ("hotkey", f"{mod}+{key}", {"ctrl": ["ctrl", "c"], "cmd": ["win", "c"], "alt": ["alt", "c"]}.get(f"{mod}+{key}", [mod, key]))
        
        # Ctrl+C / Ctrl+V 等（无+号）
        ctrl_match = re.search(r'ctrl\s*([cvza])', task_lower)
        if ctrl_match:
            key_map = {"c": "复制", "v": "粘贴", "a": "全选", "z": "撤销", "s": "保存"}
            action = {"c": "hotkey", "v": "hotkey", "a": "hotkey", "z": "hotkey", "s": "hotkey"}.get(ctrl_match.group(1), "hotkey")
            if action == "hotkey":
                return ("hotkey", key_map.get(ctrl_match.group(1), ""), ["ctrl", ctrl_match.group(1)])
        
        # 关闭当前窗口
        if any(x in task_lower for x in ["关闭当前", "关闭窗口", "关掉当前", "关掉窗口"]):
            return ("hotkey", "alt+f4", ["alt", "f4"])
        
        # 截图
        if "截图" in task_lower:
            return ("screenshot", "", "")
        
        # 保存
        if "保存" in task_lower:
            return ("hotkey", "ctrl+s", ["ctrl", "s"])
        
        # 刷新
        if "刷新" in task_lower:
            return ("hotkey", "f5", ["f5"])
        
        # 最小化
        if "最小化" in task_lower:
            return ("hotkey", "win+down", ["win", "down"])
        
        # 最大化/还原
        if "最大化" in task_lower or "还原" in task_lower:
            return ("hotkey", "win+up", ["win", "up"])
        
        # 粘贴
        if "粘贴" in task_lower:
            return ("hotkey", "ctrl+v", ["ctrl", "v"])
        
        # 复制
        if "复制" in task_lower:
            return ("hotkey", "ctrl+c", ["ctrl", "c"])
        
        # 全选
        if "全选" in task_lower:
            return ("hotkey", "ctrl+a", ["ctrl", "a"])
        
        # 撤销
        if "撤销" in task_lower:
            return ("hotkey", "ctrl+z", ["ctrl", "z"])
        
        # 搜索框输入
        search_box = re.search(r'搜索框.*?输入\s*(.+)', task_lower)
        if search_box:
            return ("type_text", search_box.group(1).strip(), "")
        
        return (None, None, None)
    
    @classmethod
    def parse(cls, task: str) -> List[ExecutionStep]:
        """解析任务为执行步骤"""
        action, target, extra = cls._extract_action(task)
        if action is None:
            return []
        
        steps = []
        order = 1
        
        if action == "open_app":
            # Win+R 打开应用
            app_id = cls._find_app(target) or cls._find_app(task_lower)
            if app_id:
                steps.append(ExecutionStep(
                    order=order, action="hotkey",
                    params={"keys": ["win", "r"]},
                    description=f"打开运行对话框",
                    confidence=0.9, model_used="rule"
                ))
                steps.append(ExecutionStep(
                    order=order+1, action="type_text",
                    params={"text": app_id},
                    description=f"输入: {app_id}",
                    confidence=0.9, model_used="rule"
                ))
                steps.append(ExecutionStep(
                    order=order+2, action="press_key",
                    params={"key": "enter"},
                    description="确认打开",
                    confidence=0.9, model_used="rule"
                ))
        
        elif action == "type_text" and target:
            steps.append(ExecutionStep(
                order=order, action="type_text",
                params={"text": target},
                description=f"输入: {target}",
                confidence=0.9, model_used="rule"
            ))
        
        elif action == "search" and target:
            steps.append(ExecutionStep(
                order=order, action="type_text",
                params={"text": target},
                description=f"搜索: {target}",
                confidence=0.85, model_used="rule"
            ))
            steps.append(ExecutionStep(
                order=order+1, action="press_key",
                params={"key": "enter"},
                description="确认搜索",
                confidence=0.85, model_used="rule"
            ))
        
        elif action == "press_key" and target:
            steps.append(ExecutionStep(
                order=order, action="press_key",
                params={"key": target},
                description=f"按键: {target}",
                confidence=0.9, model_used="rule"
            ))
        
        elif action == "hotkey" and isinstance(extra, list):
            steps.append(ExecutionStep(
                order=order, action="hotkey",
                params={"keys": extra},
                description=f"组合键: {'+'.join(extra)}",
                confidence=0.9, model_used="rule"
            ))
        
        elif action == "screenshot":
            steps.append(ExecutionStep(
                order=order, action="screenshot",
                params={},
                description="截图",
                confidence=0.9, model_used="rule"
            ))
        
        return steps


# ─────────────────────────────────────────────
# LLM客户端 - 支持分层调用
# ─────────────────────────────────────────────

class LayeredLLMClient:
    """
    分层LLM客户端
    - 规划模型（高级）：DeepSeek/GPT-4o 用于复杂分析
    - 执行模型（简单）：DeepSeek-Coder/Qwen 用于简单步骤
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config = self._load_config(config_path)
        self.llm_config = self.config.get("llm", {})
        
        # 规划模型（高级）
        self.planner = self._create_client(
            provider=self.llm_config.get("planner_provider", "openai"),
            model_key="planner_model",
            default_model="deepseek-chat"
        )
        
        # 执行模型（简单/便宜）
        self.executor = self._create_client(
            provider=self.llm_config.get("executor_provider", "openai"),
            model_key="executor_model",
            default_model="deepseek-chat"
        )
        
        # 视觉模型（用于屏幕理解）
        self.vision = self._create_client(
            provider=self.llm_config.get("planner_provider", "openai"),
            model_key="vision_model",
            default_model="gpt-4o"
        )
    
    def _load_config(self, path: Path) -> Dict:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for match in re.finditer(r'\$\{([^}]+)\}', content):
            content = content.replace(match.group(0), os.environ.get(match.group(1), ""))
        return yaml.safe_load(content)
    
    def _create_client(self, provider: str, model_key: str, default_model: str):
        """创建单个模型客户端"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装: pip install openai")
        
        cfg = self.llm_config.get(provider, {})
        api_key = cfg.get("api_key", os.environ.get("OPENAI_API_KEY", ""))
        
        if provider == "deepseek":
            base_url = "https://api.deepseek.com/v1"
            model = cfg.get(model_key, default_model)
        elif provider == "openai":
            base_url = cfg.get("base_url", "https://api.openai.com/v1")
            model = cfg.get(model_key, default_model)
        elif provider == "ollama":
            base_url = cfg.get("ollama_base_url", "http://localhost:11434/v1")
            model = cfg.get(model_key, default_model)
        elif provider == "siliconflow":
            base_url = "https://api.siliconflow.cn/v1"
            model = cfg.get(model_key, default_model)
        else:
            base_url = cfg.get("base_url", "https://api.openai.com/v1")
            model = default_model
        
        client = OpenAI(api_key=api_key or "dummy", base_url=base_url, timeout=120)
        return {"client": client, "model": model, "provider": provider}
    
    def chat(self, messages: List[Dict], client_type: str = "planner", 
             tools: List[Dict] = None, **kwargs) -> Any:
        """
        发送对话请求
        
        Args:
            messages: 消息列表
            client_type: "planner"(规划) | "executor"(执行) | "vision"(视觉)
            tools: 工具定义
        """
        if client_type == "planner":
            client_cfg = self.planner
        elif client_type == "executor":
            client_cfg = self.executor
        elif client_type == "vision":
            client_cfg = self.vision
        else:
            client_cfg = self.planner
        
        client = client_cfg["client"]
        model = client_cfg["model"]
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        return client.chat.completions.create(**params)


# ─────────────────────────────────────────────
# Skill框架 - 可插拔场景模块
# ─────────────────────────────────────────────

class Skill:
    """Skill基类 - 所有场景Skill继承"""
    
    name: str = ""           # Skill名称
    description: str = ""   # Skill描述
    keywords: List[str] = [] # 触发关键词
    
    def can_handle(self, task: str) -> bool:
        """判断此Skill是否能处理任务"""
        task_lower = task.lower()
        for kw in self.keywords:
            if kw.lower() in task_lower:
                return True
        return False
    
    def plan(self, task: str, llm: LayeredLLMClient) -> List[ExecutionStep]:
        """规划执行步骤"""
        raise NotImplementedError
    
    def execute(self, step: ExecutionStep, pc) -> Dict:
        """执行单个步骤"""
        raise NotImplementedError


class SkillRegistry:
    """Skill注册中心"""
    
    _skills: List[Skill] = []
    
    @classmethod
    def register(cls, skill: Skill):
        cls._skills.append(skill)
    
    @classmethod
    def find(cls, task: str) -> Optional[Skill]:
        """找到匹配的Skill"""
        for skill in cls._skills:
            if skill.can_handle(task):
                return skill
        return None
    
    @classmethod
    def list_all(cls) -> List[Dict]:
        """列出所有Skill"""
        return [{"name": s.name, "description": s.description, "keywords": s.keywords} for s in cls._skills]


# ─────────────────────────────────────────────
# HybridAgent - 核心混合Agent
# ─────────────────────────────────────────────

class HybridAgent:
    """
    混合Agent - Phase 3 核心
    
    执行流程：
    1. 复杂度评估
    2. 选择执行路径：
       - TRIVIAL → 规则引擎（0成本）
       - SIMPLE → 小模型直接执行
       - COMPLEX → 高级模型规划 → 小模型执行
       - VERY_COMPLEX → 高级模型规划 → Skill分发 → 小模型执行
    3. 执行并返回结果
    """

    # 系统提示词 - 规划模型
    PLANNER_PROMPT = """你是一个专业的PC自动化规划助手。

你的职责是将用户的自然语言任务拆解成精确的PC操作步骤。

**重要原则**：
- 拆解要具体：每步必须是可执行的操作（点击坐标、输入文字、按键等）
- 坐标决策：除非你非常确定坐标，否则设为null，让执行时截图识别
- 步骤要精简：合并同类操作，减少总步骤数
- 描述要清晰：每步都要有中文描述，便于用户理解

**输出格式**：
请严格输出JSON格式，不要有其他内容：
{
    "intent": "任务意图的一句话概括",
    "complexity": "simple|complex|very_complex",
    "steps": [
        {
            "action": "操作类型(click/type/press/hotkey/wait/screenshot/find_and_click)",
            "params": {"参数字典"},
            "description": "这一步做什么",
            "requires_vision": false,
            "fallback_action": "如果vision失败时的备选描述"
        }
    ],
    "estimated_cost": "低成本|中成本|高成本",
    "notes": "额外说明（如有）"
}

**操作类型定义**：
- click: 点击坐标 {x, y, button: "left/right"}
- double_click: 双击 {x, y}
- right_click: 右键 {x, y}
- type_text: 输入文字 {text, interval: 0.05}
- press_key: 按键 {key: "enter/tab/esc/a/1等"}
- hotkey: 组合键 {keys: ["ctrl","c"]}
- screenshot: 截图 {region: {x,y,w,h}或null}
- find_and_click: 找图点击 {image_desc: "描述要点击的内容", template_path: "模板图路径或null"}
- wait: 等待 {seconds: 数字}
- scroll: 滚动 {direction: "up/down", amount: 像素}

请开始规划。"""

    # 系统提示词 - 执行模型（用于简单任务直接执行）
    EXECUTOR_PROMPT = """你是一个PC自动化执行助手。

给定一个任务描述和当前屏幕截图，判断下一步应该执行什么操作。

**规则**：
1. 仔细看截图，找到需要操作的目标
2. 如果目标在截图上，用pyautogui点击对应位置
3. 如果是文字输入，找到输入框并输入
4. 操作要精确，不要猜测不确定的坐标

**输出格式**（JSON）：
{
    "action": "click/type_text/press_key/hotkey/screenshot/wait",
    "params": {},
    "reasoning": "为什么这么做"
}
"""

    def __init__(
        self,
        pc_controller,
        config_path: str = None,
        on_step: Callable = None,
        on_plan: Callable = None,
    ):
        """
        初始化 HybridAgent
        
        Args:
            pc_controller: PC自动化控制器（来自core模块）
            config_path: 配置文件路径
            on_step: 每步执行后的回调
            on_plan: 规划完成后的回调
        """
        self.pc = pc_controller
        self.llm = LayeredLLMClient(config_path)
        self.config = self.llm.config
        
        self.on_step = on_step
        self.on_plan = on_plan
        
        # 从配置读取
        agent_cfg = self.config.get("agent", {})
        self.max_steps = agent_cfg.get("max_steps", 20)
        self.verbose = agent_cfg.get("verbose", True)
        
        # 工具定义（OpenAI format）
        self.tools = self.config.get("tools", [])
    
    def _classify_complexity(self, task: str) -> TaskComplexity:
        """评估任务复杂度"""
        task_lower = task.lower()
        
        # ──── 内容运营类任务（直接判定复杂，需要LLM规划）────
        content_ops = [
            "小红书", "抖音", "公众号", "视频号", "快手",
            "B站", "bilibili", "微博", "知乎",
            "发一条", "发一篇", "发一个", "发布文章",
            "短剧", "剧本", "视频剪辑", "批量剪辑",
            "视频", "上传视频", "发布视频",
        ]
        content_count = sum(1 for kw in content_ops if kw in task_lower)
        if content_count >= 1 and any(x in task_lower for x in ["发", "发布", "上传", "配", "写", "创作"]):
            # 内容运营类 → COMPLEX（需要LLM规划操作步骤）
            return TaskComplexity.COMPLEX
        
        # ──── 规则引擎能处理的简单任务 ─────
        if RuleEngine.can_handle(task):
            steps = RuleEngine.parse(task)
            if steps and len(steps) <= 2:
                return TaskComplexity.TRIVIAL
            elif steps:
                return TaskComplexity.SIMPLE
            else:
                return TaskComplexity.SIMPLE
        
        # ──── 极复杂信号 ─────
        very_complex_signals = [
            "多平台", "多个平台", "批量", "每天", "每周", "定时",
            "循环", "重复执行", "依次", "分别",
            "拆解", "编排", "规划",
            "剪辑成30条", "剪辑.*条", "批量.*分发",
        ]
        
        # ──── 复杂信号 ─────
        complex_signals = [
            "并", "然后", "接着", "之后", "再", "最后",
            "搜索", "查找",
            "打开浏览器",
            "帮我", "请帮我",
            "登录", "注册", "账号",
        ]
        
        # 动作动词计数（多步骤操作）
        action_verbs = re.findall(r'[\u4e00-\u9fa5]{1,4}(?:打开|点击|输入|搜索|按|复制|粘贴|保存|关闭)', task_lower)
        
        very_complex_count = sum(1 for s in very_complex_signals if re.search(s, task_lower))
        complex_count = sum(1 for s in complex_signals if s in task_lower)
        
        if very_complex_count >= 1:
            return TaskComplexity.VERY_COMPLEX
        elif complex_count >= 2 or len(action_verbs) >= 2:
            return TaskComplexity.COMPLEX
        elif complex_count == 1:
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.COMPLEX
        """评估任务复杂度"""
        task_lower = task.lower()
        
        # 规则引擎能处理的简单任务
        if RuleEngine.can_handle(task):
            steps = RuleEngine.parse(task)
            if steps and len(steps) <= 2:
                # 单步或双步操作 → TRIVIAL
                return TaskComplexity.TRIVIAL
            elif steps:
                # 多步但模式固定 → SIMPLE
                return TaskComplexity.SIMPLE
            else:
                # 能匹配但解析不出步骤 → 需要模型
                return TaskComplexity.SIMPLE
        
        # 强复杂信号 → 直接判定复杂
        very_complex_signals = [
            "多平台", "多个平台", "批量", "每天", "每周", "定时",
            "循环", "重复执行", "依次", "分别",
            "拆解", "编排", "规划",
        ]
        
        complex_signals = [
            "并", "然后", "接着", "之后", "再", "最后",
            "搜索", "查找", "分析", "对比",
            "发布", "上传", "下载",
            "小红书", "抖音", "公众号", "视频号", "快手",
            "剪映", "剪辑", "视频",
            "短剧", "剧本", "创作",
            "登录", "注册", "账号",
            "发一条", "发一篇", "发一个",
            "打开浏览器",
            "帮我", "请帮我",
        ]
        
        # 计数
        very_complex_count = sum(1 for s in very_complex_signals if s in task_lower)
        complex_count = sum(1 for s in complex_signals if s in task_lower)
        
        # 多步动作（如"打开浏览器并搜索"）
        action_verbs = re.findall(r'[\u4e00-\u9fa5]{1,4}(?:打开|点击|输入|搜索|按|复制|粘贴|保存|关闭)', task_lower)
        
        if very_complex_count >= 1:
            return TaskComplexity.VERY_COMPLEX
        elif complex_count >= 2:
            return TaskComplexity.COMPLEX
        elif complex_count == 1 and len(action_verbs) > 1:
            # 有多个动作动词 → COMPLEX
            return TaskComplexity.COMPLEX
        elif complex_count == 1:
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.COMPLEX
    
    def _build_tools_for_planner(self) -> List[Dict]:
        """构建规划器可用的工具"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_step",
                    "description": "执行一个PC操作步骤",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "description": "操作类型"},
                            "params": {"type": "object", "description": "操作参数"},
                        }
                    }
                }
            }
        ]
    
    def _plan_with_model(self, task: str, complexity: TaskComplexity) -> TaskPlan:
        """使用高级模型进行任务规划"""
        if self.verbose:
            print(f"[HybridAgent] 任务复杂度: {complexity.value}，调用规划模型...")
        
        messages = [
            {"role": "system", "content": self.PLANNER_PROMPT},
            {"role": "user", "content": f"请规划以下任务：\n{task}"}
        ]
        
        try:
            response = self.llm.chat(messages, client_type="planner", max_tokens=2048)
            
            if not response.choices:
                return TaskPlan(task=task, complexity=complexity, intent="规划失败")
            
            raw = response.choices[0].message.content
            
            # 解析JSON
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    plan_data = json.loads(raw)
                
                # 转换为ExecutionStep
                steps = []
                for i, s in enumerate(plan_data.get("steps", [])):
                    steps.append(ExecutionStep(
                        order=i + 1,
                        action=s.get("action", "unknown"),
                        params=s.get("params", {}),
                        description=s.get("description", ""),
                        model_used="planner_model",
                        confidence=0.9 if s.get("action") else 0.5
                    ))
                
                return TaskPlan(
                    task=task,
                    complexity=complexity,
                    intent=plan_data.get("intent", ""),
                    steps=steps,
                    estimated_steps=len(steps),
                    planning_model=self.llm.planner["model"],
                    execution_cost=plan_data.get("estimated_cost", "未知"),
                    raw_plan=raw
                )
            except json.JSONDecodeError:
                logger.warning(f"规划JSON解析失败: {raw[:200]}")
                return TaskPlan(task=task, complexity=complexity, intent="解析失败", raw_plan=raw)
                
        except Exception as e:
            logger.error(f"规划失败: {e}")
            return TaskPlan(task=task, complexity=complexity, intent=f"错误: {e}")
    
    def _execute_step(self, step: ExecutionStep, iteration: int) -> Dict:
        """执行单个步骤"""
        action = step.action
        params = step.params.copy()
        
        # 移除None的坐标，让系统自动识别
        if "x" in params and params["x"] is None:
            params.pop("x", None)
            params.pop("y", None)
        
        try:
            if action == "click":
                result = self.pc.mouse.click(params.get("x", 0), params.get("y", 0), params.get("button", "left"))
            elif action == "double_click":
                result = self.pc.mouse.double_click(params.get("x", 0), params.get("y", 0))
            elif action == "right_click":
                result = self.pc.mouse.right_click(params.get("x", 0), params.get("y", 0))
            elif action == "type_text":
                result = self.pc.keyboard.type(params.get("text", ""), params.get("interval", 0.05))
            elif action == "press_key":
                result = self.pc.keyboard.press(params.get("key", "enter"))
            elif action == "hotkey":
                result = self.pc.keyboard.hotkey(*params.get("keys", ["ctrl", "c"]))
            elif action == "wait":
                seconds = params.get("seconds", 1)
                time.sleep(seconds)
                result = {"action": "wait", "waited": seconds}
            elif action == "screenshot":
                region = params.get("region")
                result = self.pc.screenshot(f"step_{iteration}.png")
            elif action == "find_and_click":
                # 视觉引导点击
                desc = params.get("image_desc", "")
                result = {"action": "find_and_click", "target": desc, "status": "needs_vision"}
            else:
                result = {"action": "unknown", "error": f"未知操作: {action}"}
            
            if self.verbose:
                print(f"  → {action}: {result}")
            
            if self.on_step:
                self.on_step(step, result)
            
            return result
            
        except Exception as e:
            error_result = {"action": action, "error": str(e)}
            if self.verbose:
                print(f"  ✗ {action}: {e}")
            return error_result
    
    def run(self, task: str, max_iterations: int = None) -> HybridResult:
        """
        运行混合Agent
        
        Args:
            task: 自然语言任务描述
            max_iterations: 最大迭代次数
        
        Returns:
            HybridResult: 执行结果
        """
        if max_iterations is None:
            max_iterations = self.max_steps
        
        result = HybridResult(
            status="success",
            task=task,
            complexity=TaskComplexity.COMPLEX,
            execution_log=[f"开始执行: {task}"]
        )
        
        # Step 1: 复杂度评估
        complexity = self._classify_complexity(task)
        result.complexity = complexity
        log = f"复杂度评估: {complexity.value}"
        if self.verbose:
            print(f"[HybridAgent] {log}")
        result.execution_log.append(log)
        
        # Step 2: 选择执行路径
        if complexity == TaskComplexity.TRIVIAL:
            # 路径A: 规则引擎（0成本）
            log = "执行路径: 规则引擎 (成本=0)"
            if self.verbose:
                print(f"[HybridAgent] {log}")
            result.execution_log.append(log)
            result.cost_used = "规则引擎"
            
            steps = RuleEngine.parse(task)
            if not steps:
                result.status = "error"
                result.error = "规则引擎无法解析此任务"
                return result
            
            result.steps_planned = len(steps)
            for step in steps[:max_iterations]:
                step_result = self._execute_step(step, step.order)
                result.results.append(step_result)
                result.steps_executed += 1
                time.sleep(0.5)
            
        elif complexity == TaskComplexity.SIMPLE:
            # 路径B: 小模型直接执行
            log = "执行路径: 执行模型直接执行 (低成本)"
            if self.verbose:
                print(f"[HybridAgent] {log}")
            result.execution_log.append(log)
            result.cost_used = "executor_model"
            
            # 先截图获取当前状态
            screenshot_path = self.pc.screenshot()
            
            # 调用执行模型
            messages = [
                {"role": "system", "content": self.EXECUTOR_PROMPT},
                {"role": "user", "content": f"任务: {task}\n\n请根据截图决定下一步操作。"}
            ]
            
            try:
                response = self.llm.chat(messages, client_type="executor", max_tokens=512)
                if response.choices:
                    raw = response.choices[0].message.content
                    action_data = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group())
                    
                    step = ExecutionStep(
                        order=1,
                        action=action_data.get("action", "click"),
                        params=action_data.get("params", {}),
                        description=action_data.get("reasoning", ""),
                        model_used="executor_model"
                    )
                    step_result = self._execute_step(step, 1)
                    result.results.append(step_result)
                    result.steps_executed = 1
            except Exception as e:
                result.status = "error"
                result.error = str(e)
        
        else:
            # 路径C/D: 高级模型规划 → 小模型执行
            log = "执行路径: 规划模型 → 执行模型 (中等成本)"
            if self.verbose:
                print(f"[HybridAgent] {log}")
            result.execution_log.append(log)
            result.cost_used = "planner + executor"
            
            # 规划
            plan = self._plan_with_model(task, complexity)
            result.steps_planned = len(plan.steps)
            
            if self.on_plan:
                self.on_plan(plan)
            
            if not plan.steps:
                result.status = "error"
                result.error = f"规划失败: {plan.intent}"
                return result
            
            # 执行每个步骤
            for i, step in enumerate(plan.steps[:max_iterations]):
                if self.verbose:
                    print(f"[Step {i+1}/{len(plan.steps)}] {step.description or step.action}")
                
                step_result = self._execute_step(step, i)
                result.results.append(step_result)
                result.steps_executed += 1
                
                # 出错处理
                if "error" in step_result:
                    if i < len(plan.steps) - 1:
                        # 尝试继续
                        if self.verbose:
                            print(f"  ⚠ 出错，继续下一步: {step_result['error']}")
                    else:
                        result.status = "partial"
                
                time.sleep(0.5)
        
        # 结果判定
        if result.steps_executed == result.steps_planned and result.steps_planned > 0:
            result.status = "success"
        elif result.steps_executed > 0:
            result.status = "partial"
        else:
            result.status = "error"
        
        if self.verbose:
            print(f"[HybridAgent] 完成: {result.status}, 执行{result.steps_executed}/{result.steps_planned}步")
        
        return result
    
    def plan_only(self, task: str) -> TaskPlan:
        """
        仅规划，不执行（用于预览任务步骤）
        """
        complexity = self._classify_complexity(task)
        
        if complexity in [TaskComplexity.TRIVIAL]:
            steps = RuleEngine.parse(task)
            return TaskPlan(
                task=task,
                complexity=complexity,
                intent="规则匹配",
                steps=steps,
                estimated_steps=len(steps),
                execution_cost="0"
            )
        else:
            return self._plan_with_model(task, complexity)
