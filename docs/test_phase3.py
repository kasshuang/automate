# -*- coding: utf-8 -*-
"""AutoMate Phase 3 集成测试脚本"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import py_compile
import importlib
import traceback

os.environ['OPENAI_API_KEY'] = 'test'

results = {}

# 1. 语法检查
print("=" * 60)
print("1. 语法检查 (py_compile)")
print("=" * 60)

for filename in ['agent.py', 'task_parser.py', 'automate.py']:
    try:
        py_compile.compile(filename, doraise=True)
        print(f"  [PASS] {filename}")
        results[filename] = 'PASS'
    except py_compile.PyCompileError as e:
        print(f"  [FAIL] {filename}: {e}")
        results[filename] = f'FAIL: {e}'

# 2. config.yaml 检查
print("\n" + "=" * 60)
print("2. config.yaml 格式检查")
print("=" * 60)

try:
    import yaml
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print(f"  [PASS] config.yaml 解析成功")
    print(f"  配置项: {list(config.keys())}")
    results['config.yaml'] = 'PASS'
except Exception as e:
    print(f"  [FAIL] config.yaml: {e}")
    results['config.yaml'] = f'FAIL: {e}'

# 3. 导入检查
print("\n" + "=" * 60)
print("3. 模块导入检查")
print("=" * 60)

modules_to_test = [
    ('task_parser', 'task_parser.py'),
    ('agent', 'agent.py'),
]

for module_name, filename in modules_to_test:
    try:
        # 先清除已导入的模块
        if module_name in sys.modules:
            del sys.modules[module_name]
        mod = importlib.import_module(module_name)
        print(f"  [PASS] import {module_name}")
        results[f'import:{module_name}'] = 'PASS'
    except Exception as e:
        tb = traceback.format_exc()
        print(f"  [FAIL] import {module_name}:")
        print(f"         {e}")
        # 提取关键错误行
        lines = tb.strip().split('\n')
        for line in lines[-5:]:
            print(f"         {line}")
        results[f'import:{module_name}'] = f'FAIL: {e}'

# 4. 功能测试 - 任务解析
print("\n" + "=" * 60)
print("4. 任务解析功能测试")
print("=" * 60)

try:
    from task_parser import TaskParser
    parser = TaskParser(config)
    
    test_tasks = [
        "帮我创建一个新的 GitHub 仓库叫 test-repo",
        "给这个项目添加一个 README 文件",
        "查看我有哪些仓库",
    ]
    
    for task in test_tasks:
        try:
            result = parser.parse(task)
            print(f"  [PASS] 解析成功: '{task}'")
            if result:
                print(f"         -> {result.get('action', 'N/A')}: {result.get('params', {})}")
            results[f'parse:{task[:20]}'] = 'PASS'
        except Exception as e:
            print(f"  [FAIL] 解析失败: '{task}'")
            print(f"         错误: {e}")
            results[f'parse:{task[:20]}'] = f'FAIL: {e}'
            
except Exception as e:
    print(f"  [FAIL] TaskParser 初始化失败: {e}")
    results['TaskParser'] = f'FAIL: {e}'
    traceback.print_exc()

# 5. Agent 初始化测试
print("\n" + "=" * 60)
print("5. Agent 初始化测试")
print("=" * 60)

try:
    from agent import AutoMateAgent
    agent = AutoMateAgent(config)
    print(f"  [PASS] AutoMateAgent 初始化成功")
    results['Agent'] = 'PASS'
except Exception as e:
    print(f"  [FAIL] AutoMateAgent 初始化失败:")
    print(f"         {e}")
    traceback.print_exc()
    results['Agent'] = f'FAIL: {e}'

# 汇总报告
print("\n" + "=" * 60)
print("测试汇总")
print("=" * 60)

pass_count = sum(1 for v in results.values() if v == 'PASS')
fail_count = len(results) - pass_count

for k, v in results.items():
    status = '✓' if v == 'PASS' else '✗'
    print(f"  {status} {k}: {v}")

print(f"\n通过: {pass_count}/{len(results)}")
print(f"失败: {fail_count}/{len(results)}")
