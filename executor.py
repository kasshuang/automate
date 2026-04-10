# PC Automation Executor
# 执行器 - 将任务转换为可执行脚本

import sys
import json
import argparse
from pathlib import Path

# 添加skill路径
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

from core import pc
from tasks.base import GenericTask

def execute_steps(steps_json):
    """执行步骤序列"""
    try:
        steps = json.loads(steps_json) if isinstance(steps_json, str) else steps_json
        task = GenericTask(pc)
        result = task.execute_steps(steps)
        print(json.dumps(result, ensure_ascii=False))
        return result
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def run_preset(task_name, **params):
    """运行预设任务"""
    from tasks import presets
    
    if task_name == 'publish_article':
        return presets.publish_article(pc, **params)
    elif task_name == 'list_xianyu_item':
        return presets.list_xianyu_item(pc, **params)
    elif task_name == 'fill_form':
        return presets.fill_form(pc, **params)
    else:
        return {'status': 'error', 'message': f'Unknown task: {task_name}'}

def screenshot_to_base64():
    """截图并返回base64"""
    import base64
    import mss
    
    with mss.mss() as sct:
        img = sct.shot()
        with open(img, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        return b64

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PC Automation Executor')
    parser.add_argument('--task', type=str, help='Preset task name')
    parser.add_argument('--steps', type=str, help='Steps JSON string')
    parser.add_argument('--action', type=str, help='Single action')
    parser.add_argument('--params', type=str, help='Params JSON')
    
    args = parser.parse_args()
    
    if args.action:
        params = json.loads(args.params) if args.params else {}
        result = pc.execute_step(args.action, **params)
        print(json.dumps(result, ensure_ascii=False))
    elif args.steps:
        execute_steps(args.steps)
    elif args.task:
        print("Preset tasks require params")
    else:
        print("Use --action or --steps or --task")
