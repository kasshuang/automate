"""
Task Parser - 自然语言任务解析器
Phase 3: 将自然语言转换为结构化任务
"""
import json
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    UNKNOWN = "unknown"
    PUBLISH_ARTICLE = "publish_article"      # 发布文章
    LIST_PRODUCT = "list_product"            # 上架商品
    FILL_FORM = "fill_form"                 # 填写表单
    CLICK_SEQUENCE = "click_sequence"       # 点击序列
    BROWSER_CONTROL = "browser_control"     # 浏览器控制
    FILE_OPERATION = "file_operation"       # 文件操作
    DATA_ENTRY = "data_entry"               # 数据录入


@dataclass
class ParsedParam:
    """解析后的参数"""
    name: str
    value: Any
    confidence: float = 1.0  # 置信度 0-1
    source: str = "inferred"  # extracted, inferred, default


@dataclass
class ParsedStep:
    """解析后的步骤"""
    order: int
    action: str
    target: str = ""          # 操作目标
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    requires_screenshot: bool = False


@dataclass
class ParsedTask:
    """解析后的任务"""
    task_type: TaskType
    intent: str               # 原始意图
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    price: Optional[float] = None
    params: Dict[str, ParsedParam] = field(default_factory=dict)
    steps: List[ParsedStep] = field(default_factory=list)
    raw_output: str = ""      # 原始 LLM 输出
    confidence: float = 0.0  # 整体置信度


class TaskParser:
    """
    自然语言任务解析器
    支持规则匹配和 LLM 辅助解析
    """
    
    # 意图关键词映射
    INTENT_PATTERNS = {
        TaskType.PUBLISH_ARTICLE: [
            r"发布.*文章", r"写.*文章", r"发.*公众号", r"写.*帖子",
            r"写.*微博", r"发布.*内容", r"投稿", r"帖子到微博",
            r"文章到"
        ],
        TaskType.LIST_PRODUCT: [
            r"上架.*商品", r"发布.*商品", r"闲鱼.*发布",
            r"发布.*宝贝", r"开店.*商品", r"挂.*卖",
            r"上架.*iPhone", r"上架一个"
        ],
        TaskType.FILL_FORM: [
            r"填写.*表单", r"填.*表", r"录入.*数据",
            r"批量.*录入", r"填.*信息", r"注册.*账号"
        ],
        TaskType.CLICK_SEQUENCE: [
            r"点击.*序列", r"连续.*点击", r"自动.*点击",
            r"批量.*点击", r"循环.*点击", r"点击 \(.*\)"
        ],
        TaskType.BROWSER_CONTROL: [
            r"打开.*网页", r"浏览器.*操作", r"搜索.*网页",
            r"访问.*网站", r"打开.*网站"
        ],
        TaskType.DATA_ENTRY: [
            r"录入.*数据", r"批量.*录入", r"导入.*数据",
            r"填写.*表格", r"复制.*粘贴.*数据"
        ]
    }
    
    # 参数提取模式
    PARAM_PATTERNS = {
        "title": [
            r"标题[是为：:]\s*(.{1,50}?)(?=\s*[,，价格]|$)",
            r"商品[名称为：:]\s*(.{1,50})",
            r"(?:叫|名称为)\s*(.{1,20}?)(?=\s*[,，价格]|$)",
            r"上架.*?[,，]([^，,价格]+)",  # "上架一个iPhone 13，价格3999" -> "iPhone 13"
        ],
        "price": [
            r"价格\s*(\d+(?:\.\d{1,2})?)\s*元?",
            r"卖\s*(\d+(?:\.\d{1,2})?)\s*元",
            r"(\d+(?:\.\d{1,2})?)\s*元",
        ],
        "description": [
            r"描述\s*(.{3,200}?)(?=\s*[,，]|$)",
            r"详情\s*(.{3,200})",
        ],
        "content": [
            r"内容\s*(.{10,}?)(?=\s*[,，]|$)",
            r"正文\s*(.{10,}?)",
            r"关于\s*(.{10,})",
        ],
        "platform": [
            r"发布.*到(.{2,10}?)[，,]",
            r"在(.{2,10}?)\s*发布",
            r"到(公众号|微信|闲鱼|淘宝|拼多多|抖音|小红书)",
        ],
    }
    
    def __init__(self, config_path: str = None, llm_client=None):
        """
        初始化解析器
        
        Args:
            config_path: 配置文件路径
            llm_client: LLM 客户端实例（可选，用于 LLM 辅助解析）
        """
        self.config = {}
        if config_path:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        self.llm_client = llm_client
        self.presets = self.config.get("presets", {})
    
    def parse(self, text: str, use_llm: bool = True) -> ParsedTask:
        """
        解析自然语言任务
        
        Args:
            text: 自然语言输入
            use_llm: 是否使用 LLM 辅助解析
        
        Returns:
            ParsedTask: 解析后的任务
        """
        # 1. 规则匹配 - 快速提取
        task_type = self._detect_intent(text)
        
        parsed = ParsedTask(
            task_type=task_type,
            intent=text,
            confidence=0.5
        )
        
        # 2. 提取参数
        params = self._extract_params(text)
        parsed.params = params
        
        # 3. 提取关键信息
        parsed.title = params.get("title").value if params.get("title") else None
        parsed.price = self._parse_price(params.get("price").value if params.get("price") else text)
        parsed.platform = self._extract_platform(text)
        parsed.description = params.get("description").value if params.get("description") else None
        parsed.content = params.get("content").value if params.get("content") else None
        
        # 4. 生成步骤（只有识别到任务类型时才生成）
        if task_type != TaskType.UNKNOWN:
            parsed.steps = self._generate_steps(parsed)
        else:
            parsed.steps = []
        
        # 5. LLM 辅助优化（可选）
        if use_llm and self.llm_client:
            parsed = self._llm_enhance(parsed, text)
        
        return parsed
    
    def _detect_intent(self, text: str) -> TaskType:
        """检测任务意图"""
        text_lower = text.lower()
        
        for task_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return task_type
        
        return TaskType.UNKNOWN
    
    def _extract_params(self, text: str) -> Dict[str, ParsedParam]:
        """提取参数"""
        params = {}
        
        for param_name, patterns in self.PARAM_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    params[param_name] = ParsedParam(
                        name=param_name,
                        value=match.group(1).strip(),
                        confidence=0.9,
                        source="extracted"
                    )
                    break
        
        return params
    
    def _extract_platform(self, text: str) -> Optional[str]:
        """提取平台"""
        platforms = ["公众号", "微信", "闲鱼", "淘宝", "拼多多", "抖音", "小红书",
                     "知乎", "微博", "B站", "bilibili", "知乎", "百度"]
        
        for platform in platforms:
            if platform in text:
                return platform
        
        return None
    
    def _parse_price(self, text: str) -> Optional[float]:
        """解析价格"""
        match = re.search(r"(\d+(?:\.\d{1,2})?)", str(text))
        if match:
            return float(match.group(1))
        return None
    
    def _generate_steps(self, parsed: ParsedTask) -> List[ParsedStep]:
        """根据任务类型生成步骤"""
        steps = []
        
        if parsed.task_type == TaskType.PUBLISH_ARTICLE:
            steps = self._generate_publish_article_steps(parsed)
        elif parsed.task_type == TaskType.LIST_PRODUCT:
            steps = self._generate_list_product_steps(parsed)
        elif parsed.task_type == TaskType.FILL_FORM:
            steps = self._generate_fill_form_steps(parsed)
        elif parsed.task_type == TaskType.CLICK_SEQUENCE:
            steps = self._generate_click_sequence_steps(parsed)
        else:
            steps = self._generate_generic_steps(parsed)
        
        return steps
    
    def _generate_publish_article_steps(self, parsed: ParsedTask) -> List[ParsedStep]:
        """生成发布文章步骤"""
        steps = [
            ParsedStep(
                order=0,
                action="screenshot",
                description="截取当前屏幕",
                requires_screenshot=True
            ),
        ]
        
        if parsed.title:
            steps.append(ParsedStep(
                order=1,
                action="set_clipboard",
                params={"text": parsed.title},
                description=f"复制标题: {parsed.title[:20]}..."
            ))
            steps.append(ParsedStep(
                order=2,
                action="paste",
                description="粘贴标题"
            ))
        
        steps.append(ParsedStep(
            order=3,
            action="press_key",
            params={"key": "tab"},
            description="切换到正文"
        ))
        
        if parsed.content:
            steps.append(ParsedStep(
                order=4,
                action="set_clipboard",
                params={"text": parsed.content},
                description=f"复制正文内容"
            ))
            steps.append(ParsedStep(
                order=5,
                action="paste",
                description="粘贴正文"
            ))
        
        return steps
    
    def _generate_list_product_steps(self, parsed: ParsedTask) -> List[ParsedStep]:
        """生成上架商品步骤"""
        steps = [
            ParsedStep(
                order=0,
                action="screenshot",
                description="截取当前屏幕",
                requires_screenshot=True
            ),
        ]
        
        if parsed.title:
            steps.append(ParsedStep(
                order=1,
                action="set_clipboard",
                params={"text": parsed.title},
                description=f"复制商品标题"
            ))
            steps.append(ParsedStep(
                order=2,
                action="paste",
                description="粘贴标题"
            ))
            steps.append(ParsedStep(
                order=3,
                action="press_key",
                params={"key": "tab"},
                description="下一个字段"
            ))
        
        if parsed.price:
            steps.append(ParsedStep(
                order=4,
                action="set_clipboard",
                params={"text": str(parsed.price)},
                description=f"复制价格: {parsed.price}"
            ))
            steps.append(ParsedStep(
                order=5,
                action="paste",
                description="粘贴价格"
            ))
            steps.append(ParsedStep(
                order=6,
                action="press_key",
                params={"key": "tab"},
                description="下一个字段"
            ))
        
        if parsed.description:
            steps.append(ParsedStep(
                order=7,
                action="set_clipboard",
                params={"text": parsed.description[:200]},
                description="复制描述（前200字）"
            ))
            steps.append(ParsedStep(
                order=8,
                action="paste",
                description="粘贴描述"
            ))
        
        return steps
    
    def _generate_fill_form_steps(self, parsed: ParsedTask) -> List[ParsedStep]:
        """生成填写表单步骤"""
        steps = [
            ParsedStep(
                order=0,
                action="screenshot",
                description="截取当前屏幕",
                requires_screenshot=True
            ),
        ]
        
        order = 1
        for name, param in parsed.params.items():
            steps.append(ParsedStep(
                order=order,
                action="set_clipboard",
                params={"text": str(param.value)},
                description=f"复制{name}"
            ))
            order += 1
            steps.append(ParsedStep(
                order=order,
                action="paste",
                description=f"填写{name}"
            ))
            order += 1
            steps.append(ParsedStep(
                order=order,
                action="press_key",
                params={"key": "tab"},
                description="下一个字段"
            ))
            order += 1
        
        return steps
    
    def _generate_click_sequence_steps(self, parsed: ParsedTask) -> List[ParsedStep]:
        """生成点击序列步骤"""
        # 尝试从文本中提取点击坐标
        steps = [
            ParsedStep(
                order=0,
                action="screenshot",
                description="截取当前屏幕",
                requires_screenshot=True
            ),
        ]
        
        # 提取坐标
        coord_pattern = r"\((\d+)[,，]\s*(\d+)\)"
        coords = re.findall(coord_pattern, parsed.intent)
        
        for i, (x, y) in enumerate(coords):
            steps.append(ParsedStep(
                order=i+1,
                action="click",
                params={"x": int(x), "y": int(y)},
                description=f"点击坐标 ({x}, {y})"
            ))
        
        return steps
    
    def _generate_generic_steps(self, parsed: ParsedTask) -> List[ParsedStep]:
        """生成通用步骤"""
        return [
            ParsedStep(
                order=0,
                action="screenshot",
                description="截取当前屏幕",
                requires_screenshot=True
            ),
            ParsedStep(
                order=1,
                action="get_clipboard",
                description="读取当前剪贴板"
            ),
        ]
    
    def _llm_enhance(self, parsed: ParsedTask, original_text: str) -> ParsedTask:
        """
        使用 LLM 增强解析结果
        
        Args:
            parsed: 当前解析结果
            original_text: 原始文本
        
        Returns:
            增强后的解析结果
        """
        if not self.llm_client:
            return parsed
        
        prompt = f"""分析以下任务描述，提取关键信息并生成详细步骤。

任务描述: {original_text}

当前解析:
- 任务类型: {parsed.task_type.value}
- 标题: {parsed.title}
- 平台: {parsed.platform}
- 价格: {parsed.price}

请补充:
1. 确认或修正任务类型
2. 提取遗漏的参数
3. 生成详细的执行步骤（JSON 格式）

输出格式:
{{
  "task_type": "任务类型",
  "params": {{"参数名": "参数值"}},
  "steps": [
    {{"action": "click", "params": {{"x": 100, "y": 200}}, "desc": "描述"}}
  ],
  "confidence": 0.0-1.0
}}"""
        
        try:
            messages = [
                {"role": "system", "content": "你是一个任务解析助手。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat(messages, max_tokens=2048)
            
            if response.choices:
                content = response.choices[0].message.content
                parsed.raw_output = content
                
                # 解析 JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        llm_result = json.loads(json_match.group())
                        
                        # 更新置信度
                        if "confidence" in llm_result:
                            parsed.confidence = llm_result["confidence"]
                        
                        # 更新步骤
                        if "steps" in llm_result:
                            parsed.steps = [
                                ParsedStep(
                                    order=i,
                                    action=s.get("action", "unknown"),
                                    params=s.get("params", {}),
                                    description=s.get("desc", s.get("description", ""))
                                )
                                for i, s in enumerate(llm_result["steps"])
                            ]
                        
                        # 更新参数
                        if "params" in llm_result:
                            for name, value in llm_result["params"].items():
                                if name not in parsed.params:
                                    parsed.params[name] = ParsedParam(
                                        name=name,
                                        value=value,
                                        confidence=0.8,
                                        source="llm"
                                    )
                        
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse LLM JSON output")
                        
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
        
        return parsed
    
    def to_executable_steps(self, parsed: ParsedTask) -> List[Dict]:
        """
        将解析结果转换为可执行步骤格式
        
        Args:
            parsed: 解析结果
        
        Returns:
            可执行的步骤列表
        """
        steps = []
        
        for step in parsed.steps:
            exec_step = {
                "action": step.action,
                "params": step.params,
                "desc": step.description,
                "screenshot": step.requires_screenshot,
                "delay": 0.5
            }
            steps.append(exec_step)
        
        return steps
    
    def validate(self, parsed: ParsedTask) -> tuple[bool, List[str]]:
        """
        验证解析结果
        
        Args:
            parsed: 解析结果
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 检查任务类型
        if parsed.task_type == TaskType.UNKNOWN:
            errors.append("无法识别任务类型")
        
        # 检查必要参数
        if parsed.task_type == TaskType.LIST_PRODUCT:
            if not parsed.title and not parsed.params.get("title"):
                errors.append("缺少标题参数")
        
        if parsed.task_type == TaskType.PUBLISH_ARTICLE:
            if not parsed.title and not parsed.content:
                if not parsed.params.get("title") and not parsed.params.get("content"):
                    errors.append("缺少标题或内容")
        
        # 检查步骤
        if not parsed.steps:
            errors.append("无法生成执行步骤")
        
        return len(errors) == 0, errors


class StructuredTaskParser:
    """
    结构化任务解析器 - 专门处理结构化输入
    """
    
    @staticmethod
    def parse_from_template(template: Dict, inputs: Dict) -> ParsedTask:
        """
        从模板解析任务
        
        Args:
            template: 任务模板
            inputs: 用户输入
        
        Returns:
            ParsedTask
        """
        parsed = ParsedTask(
            task_type=TaskType[template.get("type", "UNKNOWN").upper()],
            intent=inputs.get("intent", ""),
            title=inputs.get("title"),
            platform=inputs.get("platform"),
            description=inputs.get("description"),
            content=inputs.get("content")
        )
        
        # 从模板生成步骤
        steps = []
        for i, step_template in enumerate(template.get("steps", [])):
            params = {}
            for key, value in step_template.get("params", {}).items():
                # 支持变量引用
                if isinstance(value, str) and value.startswith("$"):
                    var_name = value[1:]
                    params[key] = inputs.get(var_name, step_template["params"].get(key))
                else:
                    params[key] = value
            
            steps.append(ParsedStep(
                order=i,
                action=step_template["action"],
                params=params,
                description=step_template.get("desc", "")
            ))
        
        parsed.steps = steps
        return parsed
    
    @staticmethod
    def parse_from_json(json_str: str) -> ParsedTask:
        """
        从 JSON 解析任务
        
        Args:
            json_str: JSON 格式的任务定义
        
        Returns:
            ParsedTask
        """
        try:
            data = json.loads(json_str)
            
            task_type_str = data.get("task_type", "unknown")
            try:
                task_type = TaskType[task_type_str.upper()]
            except KeyError:
                task_type = TaskType.UNKNOWN
            
            parsed = ParsedTask(
                task_type=task_type,
                intent=data.get("intent", ""),
                title=data.get("title"),
                platform=data.get("platform"),
                description=data.get("description"),
                content=data.get("content"),
                confidence=data.get("confidence", 1.0)
            )
            
            # 解析步骤
            steps = []
            for i, step_data in enumerate(data.get("steps", [])):
                steps.append(ParsedStep(
                    order=i,
                    action=step_data.get("action", "unknown"),
                    params=step_data.get("params", {}),
                    description=step_data.get("desc", step_data.get("description", "")),
                    requires_screenshot=step_data.get("screenshot", False)
                ))
            
            parsed.steps = steps
            
            # 解析参数
            for name, value in data.get("params", {}).items():
                parsed.params[name] = ParsedParam(
                    name=name,
                    value=value,
                    confidence=1.0,
                    source="json"
                )
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")


# 预设任务模板
PRESET_TEMPLATES = {
    "publish_xianyu": {
        "type": "list_product",
        "name": "闲鱼发布商品",
        "required_params": ["title", "price"],
        "steps": [
            {"action": "screenshot", "params": {}, "desc": "截图确认"},
            {"action": "set_clipboard", "params": {"text": "$title"}, "desc": "复制标题"},
            {"action": "paste", "params": {}, "desc": "粘贴标题"},
            {"action": "press_key", "params": {"key": "tab"}, "desc": "下一个字段"},
            {"action": "set_clipboard", "params": {"text": "$price"}, "desc": "复制价格"},
            {"action": "paste", "params": {}, "desc": "粘贴价格"},
            {"action": "press_key", "params": {"key": "tab"}, "desc": "下一个字段"},
            {"action": "set_clipboard", "params": {"text": "$description"}, "desc": "复制描述"},
            {"action": "paste", "params": {}, "desc": "粘贴描述"},
        ]
    },
    "publish_wechat": {
        "type": "publish_article",
        "name": "微信公众号发布",
        "required_params": ["title", "content"],
        "steps": [
            {"action": "screenshot", "params": {}, "desc": "截图确认"},
            {"action": "set_clipboard", "params": {"text": "$title"}, "desc": "复制标题"},
            {"action": "paste", "params": {}, "desc": "粘贴标题"},
            {"action": "press_key", "params": {"key": "tab"}, "desc": "切换到正文"},
            {"action": "set_clipboard", "params": {"text": "$content"}, "desc": "复制正文"},
            {"action": "paste", "params": {}, "desc": "粘贴正文"},
            {"action": "screenshot", "params": {}, "desc": "截图确认"},
        ]
    }
}


# 测试
if __name__ == "__main__":
    print("=== Task Parser Test ===")
    
    parser = TaskParser()
    
    test_cases = [
        "在闲鱼上发布一个商品，标题是iPhone 13，价格3999元",
        "发布文章到公众号，标题是《AI时代》，内容是关于人工智能的未来",
        "填写表单，姓名张三，电话13800138000",
        "点击 (100, 200) 然后点击 (300, 400)",
    ]
    
    for text in test_cases:
        print(f"\n输入: {text}")
        parsed = parser.parse(text, use_llm=False)
        print(f"任务类型: {parsed.task_type.value}")
        print(f"标题: {parsed.title}")
        print(f"价格: {parsed.price}")
        print(f"步骤数: {len(parsed.steps)}")
        for i, step in enumerate(parsed.steps[:3]):
            print(f"  {i+1}. {step.action} - {step.description}")
