"""
HybridAgent 测试脚本
测试分层架构：规则引擎 + 小模型执行
"""
import sys
import os
import json
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from core import pc
from hybrid_agent import HybridAgent, TaskComplexity, RuleEngine


def test_rule_engine():
    """测试规则引擎"""
    print("\n" + "="*60)
    print("测试1: 规则引擎")
    print("="*60)
    
    test_tasks = [
        "打开记事本",
        "按回车",
        "输入hello world",
        "按Ctrl+C",
        "关闭当前窗口",
        "打开浏览器",
        "截图",
    ]
    
    for task in test_tasks:
        print(f"\n任务: {task}")
        can_handle = RuleEngine.can_handle(task)
        print(f"  可处理: {can_handle}")
        if can_handle:
            steps = RuleEngine.parse(task)
            print(f"  解析步骤: {len(steps)}步")
            for s in steps:
                print(f"    [{s.order}] {s.action}: {s.params} ({s.model_used})")


def test_complexity_classification():
    """测试复杂度分类"""
    print("\n" + "="*60)
    print("测试2: 复杂度分类")
    print("="*60)
    
    agent = HybridAgent(pc)
    
    test_tasks = [
        "打开记事本",                       # TRIVIAL
        "按回车",                           # TRIVIAL
        "打开浏览器并搜索python",             # SIMPLE/COMPLEX
        "帮我发一条抖音视频，配上标题和话题",   # COMPLEX
        "今天发3条小红书、2条抖音、1条公众号", # VERY_COMPLEX
        "把这些视频素材批量剪辑成30条分发到各平台",  # VERY_COMPLEX
    ]
    
    for task in test_tasks:
        complexity = agent._classify_complexity(task)
        print(f"\n任务: {task}")
        print(f"  复杂度: {complexity.value}")


def test_plan_only():
    """测试仅规划（需要API Key）"""
    print("\n" + "="*60)
    print("测试3: 规划测试（需要配置API Key）")
    print("="*60)
    
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠ 未配置API Key，跳过规划测试")
        print("  请设置环境变量:")
        print("    DEEPSEEK_API_KEY=你的DeepSeek密钥")
        print("    或 OPENAI_API_KEY=你的OpenAI密钥")
        return
    
    agent = HybridAgent(pc)
    
    test_tasks = [
        "打开记事本并输入 hello",
        "打开浏览器搜索 python教程",
    ]
    
    for task in test_tasks:
        print(f"\n任务: {task}")
        plan = agent.plan_only(task)
        print(f"  复杂度: {plan.complexity.value}")
        print(f"  意图: {plan.intent}")
        print(f"  规划步骤: {len(plan.steps)}步")
        for s in plan.steps:
            print(f"    [{s.order}] {s.action}: {s.description or s.params}")
        if plan.execution_cost:
            print(f"  预估成本: {plan.execution_cost}")


def test_execution():
    """测试实际执行（谨慎！）"""
    print("\n" + "="*60)
    print("测试4: 实际执行测试（规则引擎）")
    print("="*60)
    print("⚠ 注意：这会在你的电脑上执行操作！")
    print("  3秒后开始...")
    time.sleep(3)
    
    agent = HybridAgent(pc, config_path=os.path.join(os.path.dirname(__file__), "config.yaml"))
    
    # 先截个图看看当前屏幕
    print("\n当前屏幕截图...")
    screenshot_path = pc.screenshot("test_screen.png")
    print(f"  保存到: {screenshot_path}")
    
    # 测试简单的规则匹配任务
    print("\n执行: 截图")
    result = agent.run("截图")
    print(f"  结果: {result.status}")
    print(f"  执行步数: {result.steps_executed}/{result.steps_planned}")


if __name__ == "__main__":
    print("="*60)
    print("AutoMate HybridAgent 测试套件")
    print("="*60)
    
    # 测试1: 规则引擎（不需要API Key）
    test_rule_engine()
    
    # 测试2: 复杂度分类（不需要API Key）
    test_complexity_classification()
    
    # 测试3: 规划测试（需要API Key）
    test_plan_only()
    
    # 测试4: 实际执行（谨慎）
    # 取消注释以下行来执行真实操作：
    # test_execution()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
