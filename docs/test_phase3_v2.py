# -*- coding: utf-8 -*-
"""AutoMate Phase 3 完整测试脚本 v2"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import py_compile
import traceback

os.environ['OPENAI_API_KEY'] = 'test'

results = {}

# ============================================================
# 1. 语法检查
# ============================================================
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

# ============================================================
# 2. config.yaml 检查
# ============================================================
print("\n" + "=" * 60)
print("2. config.yaml 格式检查")
print("=" * 60)

try:
    import yaml
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print(f"  [PASS] config.yaml 解析成功")
    print(f"  配置项: {list(config.keys())}")
    # 检查必需配置
    if 'llm' in config:
        print(f"  LLM配置: {config['llm']}")
    if 'agent' in config:
        print(f"  Agent配置: {list(config['agent'].keys())}")
    if 'tools' in config:
        print(f"  工具数: {len(config['tools'])}")
    results['config.yaml'] = 'PASS'
except Exception as e:
    print(f"  [FAIL] config.yaml: {e}")
    results['config.yaml'] = f'FAIL: {e}'

# ============================================================
# 3. 模块导入检查
# ============================================================
print("\n" + "=" * 60)
print("3. 模块导入检查")
print("=" * 60)

from task_parser import TaskParser, ParsedTask, TaskType
print(f"  [PASS] from task_parser import TaskParser, ParsedTask, TaskType")
results['import:task_parser'] = 'PASS'

from agent import TaskAgent, ConversationAgent, LLMClient, LLMProvider
print(f"  [PASS] from agent import TaskAgent, ConversationAgent, LLMClient")
results['import:agent'] = 'PASS'

from task_parser import *
print(f"  [PASS] task_parser 全部导出检查")
results['import:task_parser_all'] = 'PASS'

from agent import *
print(f"  [PASS] agent 全部导出检查")
results['import:agent_all'] = 'PASS'

# ============================================================
# 4. TaskParser 功能测试
# ============================================================
print("\n" + "=" * 60)
print("4. TaskParser 任务解析功能测试")
print("=" * 60)

try:
    parser = TaskParser(config)
    print(f"  [PASS] TaskParser 初始化成功")
    results['TaskParser:init'] = 'PASS'
except Exception as e:
    print(f"  [FAIL] TaskParser 初始化失败: {e}")
    results['TaskParser:init'] = f'FAIL: {e}'
    parser = None

if parser:
    test_tasks = [
        "帮我创建一个新的 GitHub 仓库叫 test-repo",
        "给这个项目添加一个 README 文件",
        "查看我有哪些仓库",
        "在闲鱼发布商品，标题iPhone 13，价格3999",
        "发布文章到公众号",
    ]

    for task in test_tasks:
        try:
            result = parser.parse(task)
            print(f"\n  [PASS] 解析: '{task}'")
            print(f"         task_type: {result.task_type}")
            print(f"         intent: {result.intent}")
            print(f"         steps: {len(result.steps)} 个")
            print(f"         params: {list(result.params.keys()) if result.params else '无'}")
            print(f"         confidence: {result.confidence:.2f}")
            results[f'parse:{task[:25]}'] = 'PASS'
        except Exception as e:
            print(f"\n  [FAIL] 解析失败: '{task}'")
            print(f"         错误: {e}")
            traceback.print_exc()
            results[f'parse:{task[:25]}'] = f'FAIL: {e}'

# ============================================================
# 5. TaskAgent 初始化测试
# ============================================================
print("\n" + "=" * 60)
print("5. TaskAgent 初始化测试")
print("=" * 60)

try:
    # 检查 TaskAgent 签名
    import inspect
    sig = inspect.signature(TaskAgent.__init__)
    print(f"  TaskAgent.__init__ 参数: {list(sig.parameters.keys())}")
    
    agent = TaskAgent(config)
    print(f"  [PASS] TaskAgent 初始化成功")
    print(f"  Agent属性: {[a for a in dir(agent) if not a.startswith('_')]}")
    results['TaskAgent:init'] = 'PASS'
except Exception as e:
    print(f"  [FAIL] TaskAgent 初始化失败:")
    traceback.print_exc()
    results['TaskAgent:init'] = f'FAIL: {e}'

# ============================================================
# 6. ConversationAgent 初始化测试
# ============================================================
print("\n" + "=" * 60)
print("6. ConversationAgent 初始化测试")
print("=" * 60)

try:
    conv_agent = ConversationAgent(config)
    print(f"  [PASS] ConversationAgent 初始化成功")
    results['ConversationAgent:init'] = 'PASS'
except Exception as e:
    print(f"  [FAIL] ConversationAgent 初始化失败:")
    traceback.print_exc()
    results['ConversationAgent:init'] = f'FAIL: {e}'

# ============================================================
# 7. 其他依赖检查
# ============================================================
print("\n" + "=" * 60)
print("7. 依赖模块检查")
print("=" * 60)

deps = ['json', 're', 'logging', 'pathlib', 'dataclasses', 'enum', 'yaml', 'base64', 'typing']
for dep in deps:
    try:
        __import__(dep)
        print(f"  [PASS] import {dep}")
        results[f'dep:{dep}'] = 'PASS'
    except Exception as e:
        print(f"  [FAIL] import {dep}: {e}")
        results[f'dep:{dep}'] = f'FAIL: {e}'

# ============================================================
# 8. 文件结构检查
# ============================================================
print("\n" + "=" * 60)
print("8. 项目文件结构检查")
print("=" * 60)

project_files = [
    'agent.py',
    'automate.py',
    'task_parser.py',
    'config.yaml',
    'setup.py',
    'SKILL.md',
    'README.md',
    'PROJECT_PLAN.md',
    'executor.py',
    'browser_control.py',
    'gui.py',
    'test_agent.py',
]

for f in project_files:
    exists = os.path.exists(f)
    status = '[PASS]' if exists else '[WARN]'
    print(f"  {status} {f}")
    results[f'file:{f}'] = 'PASS' if exists else f'MISSING'

# 检查目录
for d in ['core', 'tasks', 'docs']:
    exists = os.path.isdir(d)
    status = '[PASS]' if exists else '[WARN]'
    print(f"  {status} {d}/")
    results[f'dir:{d}'] = 'PASS' if exists else f'MISSING'

# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 60)
print("测试汇总")
print("=" * 60)

pass_count = sum(1 for v in results.values() if v == 'PASS')
fail_count = sum(1 for v in results.values() if str(v).startswith('FAIL'))
warn_count = sum(1 for v in results.values() if 'MISSING' in str(v))
total = len(results)

print(f"\n总计: {total} 项")
print(f"  通过: {pass_count}")
print(f"  失败: {fail_count}")
print(f"  缺失: {warn_count}")

print("\n详细结果:")
for k, v in sorted(results.items()):
    if v == 'PASS':
        print(f"  ✓ {k}")
    elif str(v).startswith('FAIL'):
        print(f"  ✗ {k}: {v}")
    else:
        print(f"  ? {k}: {v}")

print("\n" + "=" * 60)
print("Phase 3 测试完成")
print("=" * 60)
