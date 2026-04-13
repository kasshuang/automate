# -*- coding: utf-8 -*-
"""
AutoMate End-to-End Test
AI-driven PC control via Alibaba Cloud DashScope (qwen-plus)
"""
import sys
import os
import json
import time

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_agent import HybridAgent, LayeredLLMClient, RuleEngine, TaskComplexity


class MockPC:
    """Mock PC controller for testing"""
    def click(self, x, y, button='left'): return f"click({x},{y},{button})"
    def double_click(self, x, y): return f"dblclick({x},{y})"
    def right_click(self, x, y): return f"rclick({x},{y})"
    def type_text(self, text, interval=0.05): return f"type({text})"
    def press_key(self, key): return f"press({key})"
    def hotkey(self, *keys): return f"hotkey({'+'.join(keys)})"
    def screenshot(self, region=None): return "screenshot_saved"
    def move_mouse(self, x, y, duration=0.5): return f"move({x},{y})"
    def wait(self, seconds): return f"wait({seconds}s)"


def test_e2e():
    print("=" * 60)
    print("AutoMate E2E Test - AI PC Control (DashScope)")
    print("=" * 60)
    
    # 1. Test LLM client directly
    print("\n[1] Testing LLM Client (qwen-plus)...")
    try:
        llm = LayeredLLMClient()
        print("    LLM Client initialized OK")
        
        # Quick test
        print("    Sending test message to qwen-plus...")
        r = llm.chat(
            messages=[{"role": "user", "content": "Reply with only: OK"}],
            client_type="planner",
            max_tokens=10
        )
        print(f"    Response: {r.choices[0].message.content}")
        print(f"    Model: {r.model}")
        print(f"    Tokens: {r.usage.total_tokens}")
    except Exception as e:
        print(f"    FAIL: {e}")
        return
    
    # 2. Test rule engine
    print("\n[2] Testing Rule Engine...")
    engine = RuleEngine()
    rule_tasks = [
        "open notepad",
        "take screenshot",
        "press enter",
        "copy text with ctrl+c",
    ]
    for task in rule_tasks:
        steps = engine.parse(task)
        if steps:
            print(f"    '{task}' -> {len(steps)} steps (rule)")
            for s in steps:
                print(f"      {s.order}. {s.action}: {s.description}")
        else:
            print(f"    '{task}' -> no match, needs LLM")
    
    # 3. Test HybridAgent with LLM planning
    print("\n[3] Testing HybridAgent (plan with qwen-plus)...")
    try:
        pc = MockPC()
        agent = HybridAgent(pc_controller=pc)
        print("    Agent initialized OK")
    except Exception as e:
        print(f"    Agent init FAIL: {e}")
        return
    
    # Test complexity
    print("\n[4] Complexity Classification...")
    for task, expected in [
        ("open notepad", "simple"),
        ("search weather on baidu and save screenshot", "complex"),
        ("batch publish 10 articles to 3 platforms", "very_complex"),
    ]:
        complexity = agent._classify_complexity(task)
        print(f"    '{task}' -> {complexity.name} (expected: {expected})")
    
    # Test LLM planning
    print("\n[5] LLM Planning (qwen-plus)...")
    test_tasks = [
        "open notepad and type hello world",
        "open baidu and search for today's weather in fuzhou",
    ]
    
    for task in test_tasks:
        try:
            print(f"\n    Task: '{task}'")
            plan = agent.plan_only(task)
            print(f"    Intent: {plan.intent}")
            print(f"    Complexity: {plan.complexity.name}")
            print(f"    Planned {len(plan.steps)} steps:")
            for s in plan.steps:
                print(f"      {s.order}. [{s.action}] {s.description} (via {s.model_used})")
        except Exception as e:
            print(f"    FAIL: {e}")
    
    print("\n" + "=" * 60)
    print("E2E Test Complete! DashScope qwen-plus is working!")
    print("=" * 60)


if __name__ == "__main__":
    test_e2e()
