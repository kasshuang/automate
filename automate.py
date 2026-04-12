#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AutoMate CLI - 命令行工具
支持自然语言任务执行

用法示例:
  automate run "在闲鱼发布商品，标题iPhone 13，价格3999"
  automate run --task list_xianyu_item --title "iPhone 13" --price 3999
  automate gui
  automate agent "帮我点击发布按钮"
  automate plan "发布文章到公众号"
"""
import argparse
import json
import sys
import base64
from pathlib import Path

# 确保项目路径在 sys.path
_project_root = Path(__file__).parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def _setup_imports():
    """设置导入"""
    try:
        from core import pc
        return pc
    except ImportError as e:
        print(f"警告: 核心模块导入失败 - {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="AutoMate - AI驱动的电脑自动化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自然语言任务（Phase 3 新功能）
  automate agent "在闲鱼发布商品，标题iPhone 13，价格3999"
  automate plan "发布文章到公众号"
  automate interactive
  
  # 预设任务
  automate run list_xianyu --title "iPhone 13" --price 3999
  automate run publish_article --title "文章" --content "正文"
  
  # 图形界面
  automate gui
  
  # 状态查看
  automate status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # === Phase 3: Agent 命令 ===
    agent_parser = subparsers.add_parser('agent', help='使用AI Agent执行自然语言任务')
    agent_parser.add_argument('task', nargs='?', help='自然语言任务描述')
    agent_parser.add_argument('--model', help='指定模型')
    agent_parser.add_argument('--no-screenshot', action='store_true', help='禁用截图')
    agent_parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    # === Phase 3: 规划命令 ===
    plan_parser = subparsers.add_parser('plan', help='仅规划任务步骤（不执行）')
    plan_parser.add_argument('task', help='自然语言任务描述')
    plan_parser.add_argument('--output', '-o', help='输出到文件')
    plan_parser.add_argument('--format', choices=['json', 'text'], default='text', help='输出格式')
    
    # === Phase 3: 交互模式 ===
    interactive_parser = subparsers.add_parser('interactive', help='启动交互式Agent会话')
    interactive_parser.add_argument('--screenshot', action='store_true', help='每次输入前截图')
    
    # === run 命令（原有）===
    run_parser = subparsers.add_parser('run', help='执行任务')
    run_parser.add_argument('task', nargs='?', help='任务名称')
    run_parser.add_argument('--title', help='标题')
    run_parser.add_argument('--content', help='内容/正文')
    run_parser.add_argument('--price', help='价格')
    run_parser.add_argument('--description', help='描述')
    run_parser.add_argument('--platform', default='公众号', help='平台')
    run_parser.add_argument('--fields', help='表单字段JSON')
    run_parser.add_argument('--steps', help='自定义步骤JSON文件')
    run_parser.add_argument('--params', help='通用参数JSON')
    
    # gui 命令
    gui_parser = subparsers.add_parser('gui', help='启动图形界面')
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='查看状态')
    
    # === Phase 3: 配置命令 ===
    config_parser = subparsers.add_parser('config', help='查看/修改配置')
    config_parser.add_argument('--show', action='store_true', help='显示当前配置')
    config_parser.add_argument('--provider', help='设置LLM提供者 (openai/ollama)')
    config_parser.add_argument('--model', help='设置模型名称')
    
    # version
    parser.add_argument('--version', action='version', version='AutoMate 0.3.0 (Phase 3: Agent)')
    
    args = parser.parse_args()
    
    # ========== Agent 命令 ==========
    if args.command == 'agent':
        _run_agent(args)
    
    # ========== 规划命令 ==========
    elif args.command == 'plan':
        _run_plan(args)
    
    # ========== 交互模式 ==========
    elif args.command == 'interactive':
        _run_interactive(args)
    
    # ========== GUI 命令 ==========
    elif args.command == 'gui':
        print("启动图形界面...")
        try:
            from gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"GUI 模块导入失败: {e}")
            print("请确保安装了 pygame: pip install pygame")
    
    # ========== Run 命令（原有） ==========
    elif args.command == 'run':
        _run_task(args)
    
    # ========== Status 命令 ==========
    elif args.command == 'status':
        _show_status(args)
    
    # ========== Config 命令 ==========
    elif args.command == 'config':
        _manage_config(args)
    
    else:
        parser.print_help()


def _run_agent(args):
    """执行 Agent 任务"""
    if not args.task:
        print("请提供任务描述")
        print("示例: automate agent \"在闲鱼发布商品，标题iPhone 13\"")
        return
    
    try:
        from agent import TaskAgent, LLMClient
        
        # 初始化 PC 控制器
        pc = _setup_imports()
        if not pc:
            print("错误: 无法初始化 PC 控制器")
            return
        
        # 初始化 Agent
        config_path = Path(__file__).parent / "config.yaml"
        
        def on_step(result):
            if args.verbose:
                print(f"  → {result}")
        
        def on_error(error):
            print(f"⚠ 错误: {error}")
        
        agent = TaskAgent(
            pc_controller=pc,
            config_path=str(config_path) if config_path.exists() else None,
            on_step=on_step if args.verbose else None,
            on_error=on_error
        )
        
        # 可选：添加初始截图
        screenshot_b64 = None
        if not args.no_screenshot:
            try:
                img = pc.screenshot()
                with open(img, "rb") as f:
                    screenshot_b64 = base64.b64encode(f.read()).decode()
            except Exception as e:
                if args.verbose:
                    print(f"截图失败（继续执行）: {e}")
        
        print(f"[Agent] 开始执行: {args.task}")
        print("-" * 50)
        
        # 执行任务
        result = agent.run(
            task=args.task,
            screenshot_base64=screenshot_b64
        )
        
        print("-" * 50)
        print(f"[Agent] 执行完成")
        print(f"  状态: {result.status}")
        print(f"  执行步数: {result.steps_executed}/{result.steps_total}")
        
        if result.error:
            print(f"  错误: {result.error}")
        
        if args.verbose:
            print("\n详细结果:")
            for i, r in enumerate(result.results):
                print(f"  {i+1}. {r}")
        
    except ImportError as e:
        print(f"Agent 模块导入失败: {e}")
        print("请确保已安装所需依赖: pip install pyyaml openai")
    except Exception as e:
        print(f"执行失败: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()


def _run_plan(args):
    """仅规划任务步骤"""
    try:
        from agent import TaskAgent
        from task_parser import TaskParser, StructuredTaskParser
        
        pc = _setup_imports()
        config_path = Path(__file__).parent / "config.yaml"
        
        # 使用 TaskAgent 规划
        agent = TaskAgent(pc_controller=pc, config_path=str(config_path) if config_path.exists() else None)
        
        print(f"[Plan] 分析任务: {args.task}")
        print("-" * 50)
        
        # 规划步骤
        steps = agent.plan(args.task)
        
        if not steps:
            print("无法生成步骤")
            return
        
        if args.format == 'json':
            # JSON 格式输出
            output = {
                "task": args.task,
                "steps": [
                    {
                        "action": s.action,
                        "params": s.params,
                        "description": s.description,
                        "delay": s.delay
                    }
                    for s in steps
                ]
            }
            json_str = json.dumps(output, ensure_ascii=False, indent=2)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                print(f"已保存到: {args.output}")
            else:
                print(json_str)
        else:
            # 文本格式输出
            print(f"任务: {args.task}")
            print(f"步骤数: {len(steps)}")
            print()
            for i, step in enumerate(steps):
                params_str = ", ".join(f"{k}={v}" for k, v in step.params.items())
                print(f"{i+1}. {step.action}({params_str})")
                print(f"   描述: {step.description}")
                print()
            
            if args.output:
                # 保存文本格式
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(f"任务: {args.task}\n")
                    f.write(f"步骤数: {len(steps)}\n\n")
                    for i, step in enumerate(steps):
                        params_str = ", ".join(f"{k}={v}" for k, v in step.params.items())
                        f.write(f"{i+1}. {step.action}({params_str})\n")
                        f.write(f"   描述: {step.description}\n\n")
                print(f"已保存到: {args.output}")
    
    except ImportError as e:
        print(f"模块导入失败: {e}")
    except Exception as e:
        print(f"规划失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


def _run_interactive(args):
    """交互式 Agent 会话"""
    try:
        from agent import ConversationAgent
        import readline  # 改善输入体验
        
        pc = _setup_imports()
        config_path = Path(__file__).parent / "config.yaml"
        
        agent = ConversationAgent(
            pc_controller=pc,
            config_path=str(config_path) if config_path.exists() else None
        )
        
        print("=" * 50)
        print("AutoMate 交互式 Agent")
        print("输入自然语言描述任务，输入 'quit' 或 'exit' 退出")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n你: ").strip()
            except EOFError:
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q', '退出']:
                print("再见!")
                break
            
            # 截图
            screenshot = None
            if args.screenshot:
                try:
                    img = pc.screenshot()
                    with open(img, "rb") as f:
                        screenshot = base64.b64encode(f.read()).decode()
                except:
                    pass
            
            # 发送并获取回复
            try:
                response = agent.send(user_input, screenshot_base64=screenshot)
                print(f"\nAgent: {response}")
            except KeyboardInterrupt:
                print("\n中断...")
                break
            except Exception as e:
                print(f"错误: {e}")
    
    except ImportError as e:
        print(f"模块导入失败: {e}")
        print("提示: 在 Linux/Mac 上需要 pip install readline (Windows 已内置)")


def _run_task(args):
    """执行预设任务"""
    from tasks.presets import (
        publish_article, list_xianyu_item, fill_form, auto_click_sequence
    )
    
    pc = _setup_imports()
    
    # 加载预设任务
    presets = {
        'list_xianyu_item': list_xianyu_item,
        'publish_article': publish_article,
        'fill_form': fill_form,
    }
    
    if not args.task:
        print("请指定任务名称")
        print("可用任务:", list(presets.keys()))
        return
    
    print(f"执行任务: {args.task}")
    
    params = {}
    if args.title: params['title'] = args.title
    if args.content: params['content'] = args.content
    if args.price: params['price'] = args.price
    if args.description: params['description'] = args.description
    if args.platform: params['platform'] = args.platform
    if args.fields: 
        try:
            params['fields'] = json.loads(args.fields)
        except:
            print("fields 参数必须是有效JSON")
            return
    if args.params:
        params.update(json.loads(args.params))
    
    if args.task in presets:
        result = presets[args.task](pc, **params)
        print(f"结果: {result}")
    elif args.steps:
        # 执行自定义步骤文件
        with open(args.steps, 'r', encoding='utf-8') as f:
            steps = json.load(f)
        from tasks.base import GenericTask
        task = GenericTask(pc)
        task.plan(steps=steps)
        result = task.execute()
        print(f"结果: {result}")
    else:
        print(f"未知任务: {args.task}")
        print("提示: 尝试使用 'agent' 命令进行自然语言任务")
        return
    
    print("执行完成!")


def _show_status(args):
    """显示状态"""
    print("=== AutoMate 状态 ===")
    print(f"版本: 0.3.0 (Phase 3: Agent)")
    
    # Python 版本
    print(f"✓ Python: {sys.version.split()[0]}")
    print(f"✓ 平台: Windows")
    
    # PC 控制器
    try:
        from core import pc
        pos = pc.mouse.get_position()
        print(f"✓ PC控制器: 就绪")
        print(f"  鼠标位置: ({pos['x']}, {pos['y']})")
    except Exception as e:
        print(f"✗ PC控制器: 错误 - {e}")
    
    # LLM 配置
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            llm = config.get("llm", {})
            provider = llm.get("provider", "unknown")
            print(f"✓ LLM配置: {provider}")
            
            if provider == "openai":
                model = llm.get("openai", {}).get("model", "gpt-4o-mini")
                print(f"  模型: {model}")
            elif provider == "ollama":
                model = llm.get("ollama", {}).get("model", "llama3.2")
                url = llm.get("ollama", {}).get("base_url", "localhost:11434")
                print(f"  模型: {model}")
                print(f"  URL: {url}")
            
            # 检查 API key
            if provider == "openai":
                import os
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if api_key:
                    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
                    print(f"  API Key: {masked}")
                else:
                    print(f"  ⚠ API Key: 未设置 (设置环境变量 OPENAI_API_KEY)")
        
        except Exception as e:
            print(f"✗ LLM配置: 读取失败 - {e}")
    else:
        print(f"⚠ LLM配置: config.yaml 不存在")


def _manage_config(args):
    """管理配置"""
    config_path = Path(__file__).parent / "config.yaml"
    
    if args.show or (not args.provider and not args.model):
        # 显示配置
        if not config_path.exists():
            print("config.yaml 不存在")
            return
        
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            print("=== 当前配置 ===")
            print(f"LLM Provider: {config.get('llm', {}).get('provider', 'unknown')}")
            print()
            
            # 显示各 provider 配置
            for provider in ['openai', 'ollama', 'azure']:
                if provider in config.get('llm', {}):
                    print(f"[{provider.upper()}]")
                    pcfg = config['llm'][provider]
                    for key, value in pcfg.items():
                        if 'key' in key.lower() and value:
                            value = value[:8] + "..." if len(str(value)) > 12 else "***"
                        print(f"  {key}: {value}")
                    print()
        
        except Exception as e:
            print(f"读取配置失败: {e}")
        return
    
    # 修改配置
    try:
        import yaml
        
        config = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        
        if 'llm' not in config:
            config['llm'] = {}
        
        if args.provider:
            config['llm']['provider'] = args.provider
            print(f"已设置 provider: {args.provider}")
        
        if args.model:
            provider = config['llm'].get('provider', 'openai')
            if provider not in config['llm']:
                config['llm'][provider] = {}
            config['llm'][provider]['model'] = args.model
            print(f"已设置模型: {args.model}")
        
        # 保存配置
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"配置已保存到: {config_path}")
        
    except Exception as e:
        print(f"保存配置失败: {e}")


# ========== Agent 便捷函数 ==========
def run_natural_language(task: str, **kwargs):
    """
    便捷函数：通过自然语言执行任务
    
    用法:
        from automate import run_natural_language
        result = run_natural_language("在闲鱼发布商品，标题iPhone 13，价格3999")
    """
    from agent import TaskAgent
    from pathlib import Path
    
    pc = _setup_imports()
    config_path = Path(__file__).parent / "config.yaml"
    
    agent = TaskAgent(
        pc_controller=pc,
        config_path=str(config_path) if config_path.exists() else None,
        **kwargs
    )
    
    return agent.run(task)


def plan_task(task: str) -> list:
    """
    便捷函数：规划任务步骤
    
    用法:
        from automate import plan_task
        steps = plan_task("发布文章到公众号")
        for s in steps:
            print(f"{s.action}: {s.params}")
    """
    from agent import TaskAgent
    from pathlib import Path
    
    pc = _setup_imports()
    config_path = Path(__file__).parent / "config.yaml"
    
    agent = TaskAgent(pc_controller=pc, config_path=str(config_path) if config_path.exists() else None)
    return agent.plan(task)


# 导出
__all__ = ['run_natural_language', 'plan_task']


# 安装后可通过 `automate` 命令调用
if __name__ == '__main__':
    main()
