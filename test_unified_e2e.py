# -*- coding: utf-8 -*-
"""
端到端测试 - 完整链路串通
测试：LLM规划 → unified执行引擎 → Playwright/PyAutoGUI
"""
import sys
sys.path.insert(0, r"C:\Users\Administrator\.qclaw\workspace\automate-github")

from hybrid_agent import HybridAgent, ExecutionStep
from core import pc

# 测试任务（浏览器 + 桌面混合）
TEST_TASKS = [
    # 浏览器任务
    "帮我打开百度，搜索'AI自动化'",
    # 桌面任务
    "打开记事本，输入'测试内容'",
    # 混合任务
    "打开浏览器访问知乎，搜索'副业'",
]

def test_unified_executor():
    """测试统一执行引擎"""
    print("=" * 50)
    print("测试统一执行引擎")
    print("=" * 50)
    
    from executors.unified import execute_step, close_all
    
    # 测试1：浏览器任务 - 打开网页
    print("\n[测试1] 浏览器: 打开百度")
    step = ExecutionStep(
        order=1, action="goto",
        params={"url": "https://www.baidu.com"},
        description="打开百度",
        model_used="test"
    )
    result = execute_step(step)
    print(f"结果: {result}")
    
    # 测试2：桌面任务 - 截图
    print("\n[测试2] 桌面: 截图")
    step = ExecutionStep(
        order=1, action="screenshot",
        params={"path": "test_desktop.png"},
        description="截取桌面",
        model_used="test"
    )
    result = execute_step(step)
    print(f"结果: {result}")
    
    close_all()
    print("\n统一执行引擎测试完成 ✅")


def test_hybrid_agent():
    """测试HybridAgent完整链路"""
    print("\n" + "=" * 50)
    print("测试 HybridAgent 完整链路")
    print("=" * 50)
    
    agent = HybridAgent(
        pc_controller=pc,
        config_path=r"C:\Users\Administrator\.qclaw\workspace\automate-github\config.yaml",
        verbose=True
    )
    
    for task in TEST_TASKS:
        print(f"\n{'='*40}")
        print(f"任务: {task}")
        print(f"{'='*40}")
        
        # 先规划
        plan = agent.plan_only(task)
        print(f"\n规划结果:")
        print(f"  复杂度: {plan.complexity.value}")
        print(f"  意图: {plan.intent}")
        print(f"  步骤数: {len(plan.steps)}")
        
        if plan.steps:
            for s in plan.steps:
                print(f"  {s.order}. [{s.action}] {s.description}")
        
        # 执行
        print("\n开始执行...")
        result = agent.run(task, max_iterations=5)
        print(f"\n执行结果: {result.status}")
        print(f"  执行步数: {result.steps_executed}/{result.steps_planned}")
        if result.error:
            print(f"  错误: {result.error}")


if __name__ == "__main__":
    import traceback
    
    print("AutoMate Phase 3 端到端测试")
    print("目标：LLM规划 → unified执行引擎 → 实际操控电脑\n")
    
    # 先测执行引擎
    try:
        test_unified_executor()
    except Exception as e:
        print(f"\n⚠ 执行引擎测试出错: {e}")
        traceback.print_exc()
    
    # 再测完整链路
    try:
        test_hybrid_agent()
    except Exception as e:
        print(f"\n⚠ HybridAgent测试出错: {e}")
        traceback.print_exc()
    
    print("\n\n测试完成！")
