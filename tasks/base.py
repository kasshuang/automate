"""
Task Base Class
所有任务继承此类
"""
from abc import ABC, abstractmethod
import json
import time

class BaseTask(ABC):
    """任务基类"""
    
    def __init__(self, pc_automation):
        self.pc = pc_automation
        self.steps = []
        self.result = {}
    
    @abstractmethod
    def plan(self, **params):
        """规划步骤 - 子类实现"""
        pass
    
    def execute(self):
        """执行所有步骤"""
        for i, step in enumerate(self.steps):
            action = step['action']
            params = step.get('params', {})
            desc = step.get('desc', f'Step {i+1}')
            
            print(f"[{i+1}/{len(self.steps)}] {desc}")
            
            try:
                result = self.pc.execute_step(action, **params)
                print(f"    → {result}")
                
                # 检查是否需要截图
                if step.get('screenshot'):
                    self.pc.screenshot()
                
                # 步骤间隔
                time.sleep(step.get('delay', 0.5))
                
            except Exception as e:
                print(f"    ✗ Error: {e}")
                self.result = {'status': 'error', 'step': i+1, 'message': str(e)}
                return self.result
        
        self.result = {'status': 'success', 'steps': len(self.steps)}
        return self.result
    
    def execute_steps(self, steps):
        """执行自定义步骤列表"""
        for i, step in enumerate(steps):
            action = step['action']
            params = step.get('params', {})
            desc = step.get('desc', f'Step {i+1}')
            
            print(f"[{i+1}/{len(steps)}] {desc}")
            try:
                result = self.pc.execute_step(action, **params)
                print(f"    → {result}")
                time.sleep(step.get('delay', 0.5))
            except Exception as e:
                print(f"    ✗ Error: {e}")
                return {'status': 'error', 'step': i+1, 'message': str(e)}
        
        return {'status': 'success', 'steps': len(steps)}


class GenericTask(BaseTask):
    """
    通用任务 - 执行任意步骤序列
    最灵活的任务类型
    """
    
    def plan(self, steps=None, **params):
        """
        steps: 步骤列表，每步包含:
        {
            'action': 'click' | 'type' | 'press' | 'hotkey' | 'screenshot' | ...
            'params': {...},
            'desc': '描述',
            'delay': 0.5,
            'screenshot': True/False
        }
        """
        self.steps = steps or []
        return self


def run_task(task_class, pc_automation, **params):
    """任务运行器"""
    task = task_class(pc_automation)
    task.plan(**params)
    return task.execute()


if __name__ == '__main__':
    from . import pc
    
    # 测试：执行通用任务
    print("=== PC Automation Test ===")
    pos = pc.mouse.get_position()
    print(f"Current mouse position: {pos}")
    
    print("\nScreenshot test...")
    pc.screenshot()
    print("Screenshot saved.")
