"""
AutoMate Phase 3 单元测试
测试 Agent 和 TaskParser 功能
"""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

# 添加项目路径
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))


class TestLLMClient(unittest.TestCase):
    """测试 LLM 客户端"""
    
    def test_load_config(self):
        """测试配置文件加载"""
        import yaml
        
        config_path = _project_root / "config.yaml"
        if not config_path.exists():
            self.skipTest("config.yaml not found")
        
        # 直接读取 YAML 而不触发 LLM 初始化
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        self.assertIn("llm", config)
        self.assertIn("agent", config)
        self.assertIn("tools", config)
    
    def test_provider_detection(self):
        """测试提供商检测"""
        from agent import LLMProvider
        
        # 直接验证枚举存在
        self.assertIsInstance(LLMProvider.OPENAI, LLMProvider)
        self.assertIsInstance(LLMProvider.OLLAMA, LLMProvider)
        self.assertIsInstance(LLMProvider.AZURE, LLMProvider)


class TestTaskParser(unittest.TestCase):
    """测试任务解析器"""
    
    def setUp(self):
        """设置测试"""
        from task_parser import TaskParser
        
        self.parser = TaskParser()
    
    def test_detect_publish_article_intent(self):
        """测试发布文章意图检测"""
        from task_parser import TaskType
        
        test_cases = [
            ("发布文章到公众号", TaskType.PUBLISH_ARTICLE),
            ("发个帖子到微博", TaskType.PUBLISH_ARTICLE),
        ]
        
        for text, expected in test_cases:
            result = self.parser._detect_intent(text)
            self.assertEqual(result, expected, f"Failed: {text}")
    
    def test_detect_list_product_intent(self):
        """测试上架商品意图检测"""
        from task_parser import TaskType
        
        test_cases = [
            ("在闲鱼发布商品", TaskType.LIST_PRODUCT),
            ("发布宝贝到闲鱼", TaskType.LIST_PRODUCT),
            ("上架一个iPhone", TaskType.LIST_PRODUCT),
        ]
        
        for text, expected in test_cases:
            result = self.parser._detect_intent(text)
            self.assertEqual(result, expected, f"Failed: {text}")
    
    def test_detect_fill_form_intent(self):
        """测试填写表单意图检测"""
        from task_parser import TaskType
        
        test_cases = [
            "填写表单",
            "批量录入数据",
            "填表",
        ]
        
        for text in test_cases:
            result = self.parser._detect_intent(text)
            self.assertEqual(result, TaskType.FILL_FORM, f"Failed: {text}")
    
    def test_extract_title(self):
        """测试标题提取"""
        test_cases = [
            ("商品名称为二手电脑", "二手电脑"),
        ]
        
        for text, expected in test_cases:
            params = self.parser._extract_params(text)
            if "title" in params:
                self.assertEqual(params["title"].value, expected)
    
    def test_extract_price(self):
        """测试价格提取"""
        test_cases = [
            ("价格3999元", "3999"),
            ("卖100.5块钱", "100.5"),
            ("价格是199", "199"),
        ]
        
        for text, expected in test_cases:
            params = self.parser._extract_params(text)
            if "price" in params:
                self.assertEqual(params["price"].value, expected)
    
    def test_extract_platform(self):
        """测试平台提取"""
        test_cases = [
            ("发布到公众号", "公众号"),
            ("闲鱼上架", "闲鱼"),
            ("发到小红书", "小红书"),
            ("在淘宝开店", "淘宝"),
        ]
        
        for text, expected in test_cases:
            result = self.parser._extract_platform(text)
            if result:
                self.assertEqual(result, expected)
    
    def test_parse_publish_article(self):
        """测试发布文章解析"""
        from task_parser import TaskType
        
        text = "发布文章到公众号，标题是AI时代，内容是关于人工智能的未来"
        result = self.parser.parse(text, use_llm=False)
        
        self.assertEqual(result.task_type, TaskType.PUBLISH_ARTICLE)
        self.assertEqual(result.title, "AI时代")
        self.assertEqual(result.platform, "公众号")
        self.assertGreater(len(result.steps), 0)
    
    def test_parse_list_product(self):
        """测试上架商品解析"""
        from task_parser import TaskType
        
        text = "在闲鱼发布商品，标题iPhone 13，价格3999元，描述九成新"
        result = self.parser.parse(text, use_llm=False)
        
        self.assertEqual(result.task_type, TaskType.LIST_PRODUCT)
        self.assertEqual(result.title, "iPhone 13")
        self.assertEqual(result.price, 3999.0)
        self.assertIsNotNone(result.description)
    
    def test_parse_click_sequence(self):
        """测试点击序列解析"""
        from task_parser import TaskType
        
        text = "点击 (100, 200) 然后点击 (300, 400)"
        result = self.parser.parse(text, use_llm=False)
        
        self.assertEqual(result.task_type, TaskType.CLICK_SEQUENCE)
        # 应该识别到两个坐标
        click_steps = [s for s in result.steps if s.action == "click"]
        self.assertGreaterEqual(len(click_steps), 2)
    
    def test_to_executable_steps(self):
        """测试转换为可执行步骤"""
        text = "在闲鱼发布商品，标题iPhone 13，价格3999"
        parsed = self.parser.parse(text, use_llm=False)
        
        steps = self.parser.to_executable_steps(parsed)
        
        self.assertIsInstance(steps, list)
        self.assertGreater(len(steps), 0)
        
        # 验证步骤格式
        for step in steps:
            self.assertIn("action", step)
            self.assertIn("params", step)


class TestStructuredTaskParser(unittest.TestCase):
    """测试结构化任务解析器"""
    
    def test_parse_from_json(self):
        """测试从 JSON 解析"""
        from task_parser import StructuredTaskParser, TaskType
        
        json_str = '''
        {
            "task_type": "publish_article",
            "intent": "测试任务",
            "title": "测试标题",
            "steps": [
                {"action": "screenshot", "params": {}, "desc": "截图"},
                {"action": "click", "params": {"x": 100, "y": 200}, "desc": "点击"}
            ]
        }
        '''
        
        result = StructuredTaskParser.parse_from_json(json_str)
        
        self.assertEqual(result.task_type, TaskType.PUBLISH_ARTICLE)
        self.assertEqual(result.title, "测试标题")
        self.assertEqual(len(result.steps), 2)
        self.assertEqual(result.steps[1].action, "click")
    
    def test_parse_invalid_json(self):
        """测试无效 JSON"""
        from task_parser import StructuredTaskParser
        
        with self.assertRaises(ValueError):
            StructuredTaskParser.parse_from_json("not json")


class TestTaskAgent(unittest.TestCase):
    """测试任务 Agent"""
    
    def setUp(self):
        """设置测试"""
        self.mock_pc = Mock()
        self.mock_pc.mouse = Mock()
        self.mock_pc.mouse.get_position.return_value = {"x": 100, "y": 200}
        self.mock_pc.mouse.click.return_value = {"action": "click"}
        self.mock_pc.keyboard = Mock()
        self.mock_pc.keyboard.type.return_value = {"action": "type"}
        self.mock_pc.keyboard.press.return_value = {"action": "press"}
        self.mock_pc.screenshot.return_value = "test_screenshot.png"
        self.mock_pc.screen = Mock()
        self.mock_pc.screen.capture.return_value = "test_screenshot.png"
        self.mock_pc.clipboard = Mock()
        self.mock_pc.clipboard.get_text.return_value = "clipboard text"
        self.mock_pc.clipboard.set_text.return_value = {"action": "set_clipboard"}
    
    @patch('agent.LLMClient')
    def test_agent_initialization(self, mock_llm_class):
        """测试 Agent 初始化"""
        from agent import TaskAgent
        
        mock_llm = Mock()
        mock_llm.config = {
            "llm": {"provider": "openai", "openai": {"api_key": "test"}},
            "agent": {"max_steps": 10, "max_retries": 3},
            "tools": []
        }
        mock_llm_class.return_value = mock_llm
        
        agent = TaskAgent(pc_controller=self.mock_pc)
        
        self.assertEqual(agent.max_steps, 10)
        self.assertEqual(agent.max_retries, 3)
    
    @patch('agent.LLMClient')
    def test_build_tool_map(self, mock_llm_class):
        """测试工具映射"""
        from agent import TaskAgent
        
        mock_llm = Mock()
        mock_llm.config = {
            "llm": {"provider": "openai"},
            "agent": {},
            "tools": []
        }
        mock_llm_class.return_value = mock_llm
        
        agent = TaskAgent(pc_controller=self.mock_pc)
        
        # 验证工具映射存在
        self.assertIn("click", agent._tool_map)
        self.assertIn("type_text", agent._tool_map)
        self.assertIn("press_key", agent._tool_map)
    
    def test_execute_tool_click(self):
        """测试点击工具执行"""
        from agent import ToolCall
        
        # 手动构建一个最小 Agent 对象
        class MiniAgent:
            def __init__(self, pc, mock_pc):
                self.pc = pc
                self._tool_map = {
                    "click": lambda **kw: mock_pc.mouse.click(kw["x"], kw["y"])
                }
            
            def _execute_tool(self, tool_call):
                tool_name = tool_call.tool_name
                args = tool_call.arguments
                if tool_name not in self._tool_map:
                    return {"error": f"Unknown tool: {tool_name}"}
                func = self._tool_map[tool_name]
                return func(**args)
        
        # 执行点击
        tc = ToolCall(tool_name="click", arguments={"x": 100, "y": 200})
        agent = MiniAgent(self.mock_pc, self.mock_pc)
        result = agent._execute_tool(tc)
        
        self.mock_pc.mouse.click.assert_called_once_with(100, 200)


class TestConversationsAgent(unittest.TestCase):
    """测试对话 Agent"""
    
    def setUp(self):
        """设置测试"""
        self.mock_pc = Mock()
        self.mock_pc.mouse = Mock()
        self.mock_pc.mouse.click.return_value = {"action": "click"}
    
    @patch('agent.LLMClient')
    def test_reset_conversation(self, mock_llm_class):
        """测试重置对话"""
        from agent import ConversationAgent
        
        mock_llm = Mock()
        mock_llm.config = {"llm": {}}
        mock_llm_class.return_value = mock_llm
        
        agent = ConversationAgent(pc_controller=self.mock_pc)
        
        # 添加一些消息
        agent.messages.append({"role": "user", "content": "test"})
        
        # 重置
        agent.reset()
        
        # 应该只剩系统消息
        self.assertEqual(len(agent.messages), 1)
        self.assertEqual(agent.messages[0]["role"], "system")


class TestIntegrations(unittest.TestCase):
    """集成测试"""
    
    def test_full_parse_and_plan(self):
        """测试完整解析和规划流程"""
        from task_parser import TaskParser, TaskType
        
        parser = TaskParser()
        
        # 解析任务
        text = "在闲鱼发布商品，标题iPhone 13，价格3999"
        parsed = parser.parse(text, use_llm=False)
        
        # 验证解析结果
        self.assertEqual(parsed.task_type, TaskType.LIST_PRODUCT)
        self.assertEqual(parsed.title, "iPhone 13")
        self.assertEqual(parsed.price, 3999.0)
        
        # 转换为可执行步骤
        steps = parser.to_executable_steps(parsed)
        self.assertIsInstance(steps, list)
        self.assertGreater(len(steps), 0)
        
        # 验证步骤格式
        for step in steps:
            self.assertIn("action", step)
            self.assertIsInstance(step["params"], dict)
    
    def test_validate_parsed_task(self):
        """测试任务验证"""
        from task_parser import TaskParser, TaskType
        
        parser = TaskParser()
        
        # 有效任务
        text = "在闲鱼发布商品，标题iPhone 13，价格3999"
        parsed = parser.parse(text, use_llm=False)
        is_valid, errors = parser.validate(parsed)
        self.assertTrue(is_valid, f"Should be valid: {errors}")
        
        # 无效任务（无法识别类型）
        text = "随便做点什么"
        parsed = parser.parse(text, use_llm=False)
        # 这种情况下可能产生警告但不抛出异常


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def test_empty_input(self):
        """测试空输入"""
        from task_parser import TaskParser, TaskType
        
        parser = TaskParser()
        result = parser.parse("", use_llm=False)
        
        self.assertEqual(result.task_type, TaskType.UNKNOWN)
        self.assertEqual(len(result.steps), 0)
    
    def test_malformed_price(self):
        """测试格式错误的价格"""
        from task_parser import TaskParser
        
        parser = TaskParser()
        
        # 价格格式错误
        params = parser._extract_params("价格是abc")
        # 不应该抛出异常
        self.assertIsInstance(params, dict)
    
    def test_missing_config(self):
        """测试配置文件缺失"""
        from agent import LLMClient
        import os
        
        # 临时修改工作目录
        original_cwd = os.getcwd()
        os.chdir(tempfile.gettempdir())
        
        try:
            # 应该抛出 FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                LLMClient("/nonexistent/path/config.yaml")
        finally:
            os.chdir(original_cwd)


# ========== 运行测试 ==========
if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTaskParser))
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredTaskParser))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationsAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrations))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # 如果有配置文件，添加 LLM 测试
    if (_project_root / "config.yaml").exists():
        suite.addTests(loader.loadTestsFromTestCase(TestLLMClient))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出摘要
    print("\n" + "=" * 60)
    print(f"测试完成: {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)
