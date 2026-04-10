#!/usr/bin/env python
"""
AutoMate CLI - 命令行工具
pip install 后可通过 `automate` 命令使用
"""
import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="AutoMate - AI驱动的电脑自动化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  automate run list_xianyu --title "iPhone 13" --price 3999
  automate run publish_article --title "文章" --content "正文"
  automate gui
  automate status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # run 命令
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
    
    # version
    parser.add_argument('--version', action='version', version='AutoMate 0.1.0')
    
    args = parser.parse_args()
    
    if args.command == 'gui':
        print("启动图形界面...")
        from gui import main as gui_main
        gui_main()
    
    elif args.command == 'run':
        from core import pc
        from tasks.presets import (
            publish_article, list_xianyu_item, fill_form, auto_click_sequence
        )
        
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
            return
        
        print("执行完成!")
    
    elif args.command == 'status':
        print("=== AutoMate 状态 ===")
        try:
            from core import pc
            pos = pc.mouse.get_position()
            print(f"✓ 核心模块: 就绪")
            print(f"✓ 鼠标位置: {pos}")
        except Exception as e:
            print(f"✗ 核心模块: 错误 - {e}")
        
        print(f"✓ Python: {sys.version.split()[0]}")
        print(f"✓ 平台: Windows")
    
    else:
        parser.print_help()


# 安装后可通过 `automate` 命令调用
if __name__ == '__main__':
    main()
