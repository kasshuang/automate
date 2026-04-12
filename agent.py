"""
Agent Module - LLM 调用与任务执行
Phase 3: 实现自然语言 → 任务拆解 → 执行的完整链路
"""
import json
import os
import re
import time
import base64
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    AZURE = "azure"


@dataclass
class ToolCall:
    """工具调用结果"""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = ""


@dataclass
class Step:
    """执行步骤"""
    action: str
    params: Dict[str, Any]
    description: str = ""
    screenshot: bool = False
    delay: float = 0.5
    retry: int = 0


@dataclass
class TaskResult:
    """任务执行结果"""
    status: str  # success, error, partial
    steps_executed: int = 0
    steps_total: int = 0
    results: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


class LLMClient:
    """
    LLM 客户端 - 支持 OpenAI / Ollama / Azure
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化 LLM 客户端
        
        Args:
            config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config = self._load_config(config_path)
        self.llm_config = self.config.get("llm", {})
        self._client = None
        self._init_client()
    
    def _load_config(self, path: Path) -> Dict:
        """加载配置文件，支持环境变量"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 替换环境变量 ${VAR_NAME}
        for match in re.finditer(r'\$\{([^}]+)\}', content):
            var_name = match.group(1)
            var_value = os.environ.get(var_name, "")
            content = content.replace(match.group(0), var_value)
        
        return yaml.safe_load(content)
    
    def _init_client(self):
        """初始化 API 客户端"""
        provider = self.llm_config.get("provider", "openai")
        
        if provider == "openai":
            self._init_openai()
        elif provider == "ollama":
            self._init_ollama()
        elif provider == "azure":
            self._init_azure()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def _init_openai(self):
        """初始化 OpenAI 客户端"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
        
        cfg = self.llm_config.get("openai", {})
        api_key = cfg.get("api_key", "")
        if api_key.startswith("${") or not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")
        
        self._client = OpenAI(
            api_key=api_key,
            base_url=cfg.get("base_url", "https://api.openai.com/v1"),
            timeout=cfg.get("timeout", 120)
        )
        self._model = cfg.get("model", "gpt-4o-mini")
        self._model_vision = cfg.get("model_vision", "gpt-4o")
        self._provider = LLMProvider.OPENAI
    
    def _init_ollama(self):
        """初始化 Ollama 客户端"""
        import openai  # Ollama 使用 OpenAI 兼容 API
        
        cfg = self.llm_config.get("ollama", {})
        base_url = cfg.get("base_url", "http://localhost:11434")
        
        self._client = openai.OpenAI(
            base_url=f"{base_url}/v1",
            api_key="ollama",  # Ollama 不需要真实 API key
            timeout=cfg.get("timeout", 300)
        )
        self._model = cfg.get("model", "llama3.2")
        self._model_vision = cfg.get("model_vision", "llama3.2-vision")
        self._provider = LLMProvider.OLLAMA
    
    def _init_azure(self):
        """初始化 Azure OpenAI 客户端"""
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
        
        cfg = self.llm_config.get("azure", {})
        self._client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_KEY", ""),
            api_version=cfg.get("api_version", "2024-02-01"),
            azure_endpoint=cfg.get("base_url", "")
        )
        self._model = cfg.get("deployment_name", "gpt-4o-mini")
        self._provider = LLMProvider.AZURE
    
    def chat(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict:
        """
        发送对话请求
        
        Args:
            messages: 消息列表
            tools: 工具定义列表（OpenAI format）
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            API 响应
        """
        if model is None:
            model = self._model
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        try:
            response = self._client.chat.completions.create(**params)
            return response
        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}")
            raise
    
    def chat_with_image(
        self,
        messages: List[Dict],
        image_data: bytes = None,
        image_url: str = None,
        **kwargs
    ) -> Dict:
        """
        发送带图片的对话请求
        
        Args:
            messages: 消息列表
            image_data: 图片二进制数据
            image_url: 图片 URL
            **kwargs: 其他参数
        """
        # 处理消息中的图片
        for msg in messages:
            if isinstance(msg.get("content"), list):
                for item in msg["content"]:
                    if item.get("type") == "image_url":
                        if image_url:
                            item["image_url"]["url"] = image_url
                        elif image_data:
                            b64_image = base64.b64encode(image_data).decode("utf-8")
                            item["image_url"]["url"] = f"data:image/jpeg;base64,{b64_image}"
        
        # 如果消息没有图片上下文，手动添加
        if image_data:
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    msg["content"] = [
                        {"type": "text", "text": msg["content"]},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
                            }
                        }
                    ]
                    break
        
        model = kwargs.pop("model", self._model_vision)
        return self.chat(messages, model=model, **kwargs)
    
    @property
    def provider(self) -> LLMProvider:
        return self._provider


class TaskAgent:
    """
    任务 Agent - 负责任务拆解与执行
    """
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的电脑自动化助手。用户会用自然语言描述想要完成的自动化任务。

你的职责是：
1. 理解用户的自然语言指令
2. 将任务拆解成具体的操作步骤
3. 使用提供的工具来执行每个步骤

**重要约束**：
- 坐标必须在用户当前屏幕上有效
- 每个步骤必须明确描述要做什么
- 遇到错误要尝试修复或提供替代方案
- 如果任务无法完成，明确告知原因

**可用工具**：
- click(x, y, button): 点击坐标
- double_click(x, y): 双击
- right_click(x, y): 右键
- move_mouse(x, y, duration): 移动鼠标
- type_text(text, interval): 输入文字
- press_key(key): 按键（enter, tab, esc, space 等）
- hotkey(keys): 组合键（['ctrl', 'c'] 表示 Ctrl+C）
- screenshot(region): 截图
- find_image(image_path, confidence): 查找图片位置
- get_clipboard(): 读取剪贴板
- set_clipboard(text): 设置剪贴板
- wait(seconds): 等待

**执行策略**：
1. 先截图了解当前屏幕状态
2. 根据屏幕内容决定下一步操作
3. 每次操作后验证结果
4. 循环直到任务完成

请始终使用工具调用来完成任务，不要只是输出文字描述。"""
    
    def __init__(
        self,
        pc_controller,
        config_path: str = None,
        on_step: Callable = None,
        on_error: Callable = None
    ):
        """
        初始化 Task Agent
        
        Args:
            pc_controller: PC 自动化控制器实例
            config_path: 配置文件路径
            on_step: 每步执行后的回调 (step_result) -> None
            on_error: 出错时的回调 (error) -> None
        """
        self.pc = pc_controller
        self.llm = LLMClient(config_path)
        self.config = self.llm.config
        
        # 回调函数
        self.on_step = on_step
        self.on_error = on_error
        
        # Agent 配置
        agent_config = self.config.get("agent", {})
        self.max_steps = agent_config.get("max_steps", 20)
        self.max_retries = agent_config.get("max_retries", 3)
        self.retry_delay = agent_config.get("retry_delay", 2)
        self.screenshot_on_step = agent_config.get("screenshot_on_step", True)
        self.screenshot_on_error = agent_config.get("screenshot_on_error", True)
        self.verbose = agent_config.get("verbose", True)
        
        # 工具定义
        self.tools = self.config.get("tools", [])
        self._tool_map = self._build_tool_map()
    
    def _build_tool_map(self) -> Dict[str, Callable]:
        """构建工具名称到执行函数的映射"""
        return {
            "click": lambda **kw: self.pc.mouse.click(kw["x"], kw["y"], kw.get("button", "left")),
            "double_click": lambda **kw: self.pc.mouse.double_click(kw["x"], kw["y"]),
            "right_click": lambda **kw: self.pc.mouse.right_click(kw["x"], kw["y"]),
            "move_mouse": lambda **kw: self.pc.mouse.move_to(kw["x"], kw["y"], kw.get("duration", 0.5)),
            "type_text": lambda **kw: self.pc.keyboard.type(kw["text"], kw.get("interval", 0.05)),
            "press_key": lambda **kw: self.pc.keyboard.press(kw["key"]),
            "hotkey": lambda **kw: self.pc.keyboard.hotkey(*kw["keys"]),
            "screenshot": lambda **kw: self._do_screenshot(kw.get("region")),
            "find_image": lambda **kw: self.pc.screen.find_on_screen(kw["image_path"], kw.get("confidence", 0.8)),
            "get_clipboard": lambda **kw: {"text": self.pc.clipboard.get_text()},
            "set_clipboard": lambda **kw: self.pc.clipboard.set_text(kw["text"]),
            "wait": lambda **kw: time.sleep(kw["seconds"]) or {"waited": kw["seconds"]},
        }
    
    def _do_screenshot(self, region: Dict = None) -> Dict:
        """执行截图"""
        if region:
            x = region.get("x", 0)
            y = region.get("y", 0)
            w = region.get("width", 1920)
            h = region.get("height", 1080)
            img = self.pc.screen.capture_region(x, y, w, h)
        else:
            img = self.pc.screenshot()
        return {"screenshot": str(img)}
    
    def _get_tools_definition(self) -> List[Dict]:
        """获取 OpenAI 格式的工具定义"""
        tools = []
        for tool in self.tools:
            params = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param_info in tool.get("params", {}).items():
                param_def = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", "")
                }
                if "default" in param_info:
                    param_def["default"] = param_info["default"]
                
                params["properties"][param_name] = param_def
                
                if param_info.get("required", False):
                    params["required"].append(param_name)
            
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": params
                }
            })
        
        return tools
    
    def _build_messages(
        self,
        user_input: str,
        context: Dict = None
    ) -> List[Dict]:
        """
        构建消息列表
        
        Args:
            user_input: 用户输入
            context: 额外上下文（截图、鼠标位置等）
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]
        
        # 添加上下文
        if context:
            if context.get("screenshot"):
                # 添加截图
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "当前屏幕截图："},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{context['screenshot']}"}
                        }
                    ]
                })
            
            if context.get("mouse_position"):
                pos = context["mouse_position"]
                messages.append({
                    "role": "user",
                    "content": f"当前鼠标位置: ({pos['x']}, {pos['y']})"
                })
            
            if context.get("last_result"):
                messages.append({
                    "role": "user",
                    "content": f"上一步结果: {context['last_result']}"
                })
        
        # 添加用户输入
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _parse_tool_calls(self, response) -> List[ToolCall]:
        """解析 LLM 返回的工具调用"""
        tool_calls = []
        
        if not response.choices:
            return tool_calls
        
        choice = response.choices[0]
        
        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(ToolCall(
                    tool_name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                    call_id=tc.id
                ))
        
        return tool_calls
    
    def _execute_tool(self, tool_call: ToolCall) -> Dict:
        """
        执行单个工具调用
        
        Args:
            tool_call: 工具调用对象
        
        Returns:
            执行结果
        """
        tool_name = tool_call.tool_name
        args = tool_call.arguments
        
        if tool_name not in self._tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            func = self._tool_map[tool_name]
            result = func(**args)
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {"error": str(e), "tool": tool_name}
    
    def _extract_steps_from_response(self, text: str) -> List[Step]:
        """
        从 LLM 响应中提取步骤（用于不支持 function calling 的模型）
        
        Args:
            text: LLM 响应文本
        
        Returns:
            步骤列表
        """
        steps = []
        
        # 匹配类似 "1. click(x=100, y=200)" 的模式
        pattern = r'(\d+)\.\s*(\w+)\s*\(([^)]*)\)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            step_num, action, args_str = match
            args = {}
            
            # 解析参数
            for arg in args_str.split(","):
                arg = arg.strip()
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 类型转换
                    if value.isdigit():
                        value = int(value)
                    elif value.replace(".", "", 1).isdigit():
                        value = float(value)
                    elif value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.startswith("[") and value.endswith("]"):
                        value = json.loads(value.replace("'", '"'))
                    
                    args[key] = value
            
            steps.append(Step(
                action=action,
                params=args,
                description=f"Step {step_num}"
            ))
        
        return steps
    
    def run(
        self,
        task: str,
        max_iterations: int = None,
        screenshot_base64: str = None
    ) -> TaskResult:
        """
        运行任务 - 主入口
        
        Args:
            task: 自然语言任务描述
            max_iterations: 最大迭代次数，默认使用配置
            screenshot_base64: 初始截图（base64 编码）
        
        Returns:
            TaskResult: 任务执行结果
        """
        if max_iterations is None:
            max_iterations = self.max_steps
        
        result = TaskResult(status="success", steps_total=0)
        
        if self.verbose:
            print(f"[Agent] 开始执行任务: {task}")
        
        # 构建初始上下文
        context = {}
        if screenshot_base64:
            context["screenshot"] = screenshot_base64
        if self.config.get("agent", {}).get("include_mouse_position", True):
            try:
                context["mouse_position"] = self.pc.mouse.get_position()
            except:
                pass
        
        # 构建消息
        messages = self._build_messages(task, context)
        
        # 获取工具定义
        tools_def = self._get_tools_definition()
        
        # 主循环：LLM 决策 + 执行
        for iteration in range(max_iterations):
            result.steps_total += 1
            
            try:
                # 调用 LLM
                response = self.llm.chat(
                    messages=messages,
                    tools=tools_def if tools_def else None
                )
                
                # 检查是否需要函数调用
                tool_calls = self._parse_tool_calls(response)
                
                if not tool_calls:
                    # LLM 没有调用工具，检查是否完成任务
                    if response.choices:
                        final_text = response.choices[0].message.content
                        messages.append({"role": "assistant", "content": final_text})
                        
                        # 检查是否包含完成标记
                        if any(mark in final_text.lower() for mark in ["完成", "success", "done", "finished"]):
                            break
                        elif any(mark in final_text.lower() for mark in ["无法", "不能", "失败", "error", "cannot", "unable"]):
                            result.status = "error"
                            result.error = final_text
                            break
                
                # 执行工具调用
                for tc in tool_calls:
                    if self.verbose:
                        print(f"[Agent] 执行: {tc.tool_name}({tc.arguments})")
                    
                    tool_result = self._execute_tool(tc)
                    result.results.append(tool_result)
                    result.steps_executed += 1
                    
                    # 回调
                    if self.on_step:
                        self.on_step(tool_result)
                    
                    # 添加结果到消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.call_id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                    
                    # 如果是截图，保存到上下文
                    if tc.tool_name == "screenshot":
                        try:
                            img_path = tool_result.get("screenshot")
                            if img_path and Path(img_path).exists():
                                with open(img_path, "rb") as f:
                                    context["screenshot"] = base64.b64encode(f.read()).decode()
                        except:
                            pass
                    
                    # 出错检查
                    if "error" in tool_result:
                        if self.screenshot_on_error:
                            self.pc.screenshot(f"error_step_{iteration}.png")
                        
                        if self.on_error:
                            self.on_error(tool_result["error"])
                        
                        # 尝试恢复或报告
                        if iteration < max_iterations - 1:
                            messages.append({
                                "role": "user",
                                "content": f"上一步出错: {tool_result['error']}，请尝试修复或使用替代方案。"
                            })
                        else:
                            result.status = "error"
                            result.error = tool_result["error"]
                
            except Exception as e:
                logger.error(f"Iteration error: {e}")
                result.status = "error"
                result.error = str(e)
                break
        
        if result.steps_total >= max_iterations:
            result.status = "partial"
            result.error = f"达到最大迭代次数 {max_iterations}"
        
        return result
    
    def plan(self, task: str) -> List[Step]:
        """
        仅规划步骤，不执行
        
        Args:
            task: 自然语言任务描述
        
        Returns:
            步骤列表
        """
        prompt_text = (
            "你是一个任务规划助手。请将用户的任务拆解成具体步骤，输出 JSON 数组格式。\n"
            "请拆解以下任务:\n"
            + task +
            "\n\n输出格式示例:\n"
            '[{"action": "click", "params": {"x": 100, "y": 200}, "desc": "描述"}]'
        )
        messages = [
            {"role": "system", "content": "你是一个任务规划助手。"},
            {"role": "user", "content": prompt_text}
        ]
        
        try:
            response = self.llm.chat(messages, max_tokens=2048)
            
            if response.choices:
                content = response.choices[0].message.content
                
                # 提取 JSON
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    steps_data = json.loads(json_match.group())
                    return [Step(
                        action=s["action"],
                        params=s.get("params", {}),
                        description=s.get("desc", s.get("description", "")),
                        delay=s.get("delay", 0.5),
                        screenshot=s.get("screenshot", False)
                    ) for s in steps_data]
        except Exception as e:
            logger.error(f"Planning error: {e}")
        
        return []


class ConversationAgent:
    """
    对话式 Agent - 支持多轮交互
    """
    
    def __init__(self, pc_controller, config_path: str = None):
        self.pc = pc_controller
        self.llm = LLMClient(config_path)
        self.messages = [
            {"role": "system", "content": TaskAgent.SYSTEM_PROMPT}
        ]
        self.tools_def = None
    
    def send(self, user_input: str, screenshot_base64: str = None) -> str:
        """
        发送用户消息并获取回复
        
        Args:
            user_input: 用户输入
            screenshot_base64: 可选的截图
        
        Returns:
            Agent 回复
        """
        # 添加截图到消息
        if screenshot_base64:
            self.messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_input},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"}
                    }
                ]
            })
        else:
            self.messages.append({"role": "user", "content": user_input})
        
        # 获取工具定义
        if self.tools_def is None:
            config_path = Path(__file__).parent / "config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self.tools_def = config.get("tools", [])
        
        # 构建工具定义
        tools = []
        for tool in self.tools_def:
            params = {
                "type": "object",
                "properties": {},
                "required": []
            }
            for param_name, param_info in tool.get("params", {}).items():
                params["properties"][param_name] = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", "")
                }
                if param_info.get("required"):
                    params["required"].append(param_name)
            
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": params
                }
            })
        
        # 调用 LLM
        response = self.llm.chat(self.messages, tools=tools if tools else None)
        
        # 解析响应
        if response.choices:
            message = response.choices[0].message
            
            # 检查工具调用
            if hasattr(message, "tool_calls") and message.tool_calls:
                self.messages.append({
                    "role": "assistant",
                    "content": message.content or "我来执行操作...",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # 执行工具并返回结果
                results = []
                tool_map = self._build_tool_map()
                
                for tc in message.tool_calls:
                    if tc.function.name in tool_map:
                        args = json.loads(tc.function.arguments)
                        result = tool_map[tc.function.name](**args)
                        results.append(f"{tc.function.name}: {result}")
                        
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                
                return f"已执行操作:\n" + "\n".join(results)
            else:
                self.messages.append({"role": "assistant", "content": message.content})
                return message.content or "收到。"
        
        return "抱歉，我没有收到回复。"
    
    def _build_tool_map(self) -> Dict:
        return {
            "click": lambda **kw: self.pc.mouse.click(kw["x"], kw["y"], kw.get("button", "left")),
            "double_click": lambda **kw: self.pc.mouse.double_click(kw["x"], kw["y"]),
            "right_click": lambda **kw: self.pc.mouse.right_click(kw["x"], kw["y"]),
            "move_mouse": lambda **kw: self.pc.mouse.move_to(kw["x"], kw["y"], kw.get("duration", 0.5)),
            "type_text": lambda **kw: self.pc.keyboard.type(kw["text"], kw.get("interval", 0.05)),
            "press_key": lambda **kw: self.pc.keyboard.press(kw["key"]),
            "hotkey": lambda **kw: self.pc.keyboard.hotkey(*kw["keys"]),
            "screenshot": lambda **kw: str(self.pc.screenshot()),
            "get_clipboard": lambda **kw: {"text": self.pc.clipboard.get_text()},
            "set_clipboard": lambda **kw: self.pc.clipboard.set_text(kw["text"]),
            "wait": lambda **kw: time.sleep(kw["seconds"]),
        }
    
    def reset(self):
        """重置对话"""
        self.messages = [
            {"role": "system", "content": TaskAgent.SYSTEM_PROMPT}
        ]


# 测试
if __name__ == "__main__":
    print("=== LLM Client Test ===")
    
    try:
        client = LLMClient()
        print(f"Provider: {client.provider}")
        
        # 测试调用
        messages = [{"role": "user", "content": "你好，2+2等于几？"}]
        response = client.chat(messages, max_tokens=100)
        
        if response.choices:
            print(f"Response: {response.choices[0].message.content}")
        else:
            print("No response")
            
    except FileNotFoundError:
        print("config.yaml not found, skipping LLM test")
    except Exception as e:
        print(f"Test error: {e}")
