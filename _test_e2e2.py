# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\Administrator\.qclaw\workspace\automate-github')

from hybrid_agent import HybridAgent
from core import pc

agent = HybridAgent(pc, 'config.yaml')
agent.verbose = True

# 任务1: 规则引擎
print("=" * 40)
print("Task 1: 打开记事本，输入测试内容")
print("=" * 40)
task = "打开记事本，输入测试内容"
plan = agent.plan_only(task)
print(f"复杂度: {plan.complexity.value}")
print(f"步骤数: {len(plan.steps)}")
for s in plan.steps:
    print(f"  {s.order}. [{s.action}] {s.description}")

result = agent.run(task)
print(f"结果: {result.status} ({result.steps_executed}/{result.steps_planned}步)")
if result.error:
    print(f"错误: {result.error}")

# 任务2: 浏览器
print("\n" + "=" * 40)
print("Task 2: 打开百度")
print("=" * 40)
task2 = "打开百度"
plan2 = agent.plan_only(task2)
print(f"复杂度: {plan2.complexity.value}")
print(f"步骤数: {len(plan2.steps)}")
for s in plan2.steps:
    print(f"  {s.order}. [{s.action}] {s.description} | params={s.params}")

result2 = agent.run(task2)
print(f"结果: {result2.status} ({result2.steps_executed}/{result2.steps_planned}步)")

print("\n测试完成")
