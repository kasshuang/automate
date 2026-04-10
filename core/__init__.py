"""
PC Automation Core Interface
统一接口层 - 封装所有底层执行能力
"""
import subprocess
import os

# 自动安装依赖
def ensure_dependencies():
    packages = ['pyautogui', 'Pillow', 'mss']
    for pkg in packages:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.run(['pip', 'install', pkg, '-q'], check=True)

ensure_dependencies()

import pyautogui
import mss
import base64
import time
import json
from PIL import Image

pyautogui.FAILSAFE = True  # 鼠标移到角落自动停止
pyautogui.PAUSE = 0.5      # 每次操作后暂停0.5秒

class Mouse:
    """鼠标控制"""
    
    @staticmethod
    def click(x, y, button='left'):
        """点击坐标"""
        pyautogui.click(x, y, button=button)
        return {'action': 'click', 'x': x, 'y': y, 'button': button}
    
    @staticmethod
    def double_click(x, y):
        """双击"""
        pyautogui.doubleClick(x, y)
        return {'action': 'double_click', 'x': x, 'y': y}
    
    @staticmethod
    def right_click(x, y):
        """右键"""
        pyautogui.click(x, y, button='right')
        return {'action': 'right_click', 'x': x, 'y': y}
    
    @staticmethod
    def move_to(x, y, duration=0.5):
        """移动鼠标"""
        pyautogui.moveTo(x, y, duration=duration)
        return {'action': 'move_to', 'x': x, 'y': y}
    
    @staticmethod
    def get_position():
        """获取当前位置"""
        pos = pyautogui.position()
        return {'x': pos.x, 'y': pos.y}

class Keyboard:
    """键盘控制"""
    
    @staticmethod
    def type(text, interval=0.05):
        """输入文字"""
        pyautogui.write(text, interval=interval)
        return {'action': 'type', 'text': text[:20]}
    
    @staticmethod
    def press(key):
        """按键"""
        pyautogui.press(key)
        return {'action': 'press', 'key': key}
    
    @staticmethod
    def hotkey(*keys):
        """组合键"""
        pyautogui.hotkey(*keys)
        return {'action': 'hotkey', 'keys': list(keys)}
    
    @staticmethod
    def select_all():
        """全选 Ctrl+A"""
        pyautogui.hotkey('ctrl', 'a')
        return {'action': 'select_all'}
    
    @staticmethod
    def copy():
        """复制 Ctrl+C"""
        pyautogui.hotkey('ctrl', 'c')
        return {'action': 'copy'}
    
    @staticmethod
    def paste():
        """粘贴 Ctrl+V"""
        pyautogui.hotkey('ctrl', 'v')
        return {'action': 'paste'}

class Screen:
    """屏幕截图"""
    
    @staticmethod
    def capture(file_path=None):
        """截取全屏"""
        with mss.mss() as sct:
            img = sct.shot()
            if file_path:
                sct.shot(output=file_path)
            return img
    
    @staticmethod
    def capture_region(x, y, width, height, file_path=None):
        """截取区域"""
        monitor = {"x": x, "y": y, "width": width, "height": height}
        with mss.mss() as sct:
            img = sct.grab(monitor)
            if file_path:
                mss.tools.to_png(img.rgb, img.size, output=file_path)
            return img
    
    @staticmethod
    def find_on_screen(image_path, confidence=0.8):
        """在屏幕上查找图片位置"""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                return {'found': True, 'x': center.x, 'y': center.y, 'region': location}
            return {'found': False}
        except Exception as e:
            return {'found': False, 'error': str(e)}

class Clipboard:
    """剪贴板"""
    
    @staticmethod
    def get_text():
        """获取剪贴板文本"""
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            text = win32clipboard.GetClipboardData()
        except:
            text = ''
        win32clipboard.CloseClipboard()
        return text
    
    @staticmethod
    def set_text(text):
        """设置剪贴板文本"""
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return {'action': 'set_clipboard', 'length': len(text)}

class Window:
    """窗口控制"""
    
    @staticmethod
    def find_window(title_contains):
        """查找窗口"""
        import win32gui
        import win32con
        
        result = []
        
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and title_contains.lower() in title.lower():
                    windows.append({'hwnd': hwnd, 'title': title})
            return True
        
        win32gui.EnumWindows(callback, result)
        return result if result else None
    
    @staticmethod
    def activate(hwnd):
        """激活窗口"""
        import win32gui
        import win32con
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return {'action': 'activate', 'hwnd': hwnd}
    
    @staticmethod
    def maximize(hwnd):
        """最大化窗口"""
        import win32gui
        import win32con
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return {'action': 'maximize', 'hwnd': hwnd}

class PCAutomation:
    """
    PC自动化主类
    统一接口，组合所有能力
    """
    
    def __init__(self):
        self.mouse = Mouse()
        self.keyboard = Keyboard()
        self.screen = Screen()
        self.clipboard = Clipboard()
        self.window = Window()
        self._last_screenshot = None
    
    def screenshot(self, file_path=None):
        """截图"""
        self._last_screenshot = self.screen.capture(file_path)
        return self._last_screenshot
    
    def execute_step(self, action, **params):
        """
        执行单步操作
        action: click, type, press, hotkey, screenshot, find_image, get_text, set_text
        """
        if action == 'click':
            return self.mouse.click(params['x'], params['y'], params.get('button', 'left'))
        elif action == 'double_click':
            return self.mouse.double_click(params['x'], params['y'])
        elif action == 'right_click':
            return self.mouse.right_click(params['x'], params['y'])
        elif action == 'move':
            self.mouse.move_to(params['x'], params['y'], params.get('duration', 0.5))
            return {'action': 'move', 'x': params['x'], 'y': params['y']}
        elif action == 'type':
            return self.keyboard.type(params['text'], params.get('interval', 0.05))
        elif action == 'press':
            return self.keyboard.press(params['key'])
        elif action == 'hotkey':
            return self.keyboard.hotkey(*params['keys'])
        elif action == 'select_all':
            return self.keyboard.select_all()
        elif action == 'copy':
            return self.keyboard.copy()
        elif action == 'paste':
            return self.keyboard.paste()
        elif action == 'screenshot':
            return self.screenshot(params.get('path'))
        elif action == 'find_image':
            return self.screen.find_on_screen(params['image_path'], params.get('confidence', 0.8))
        elif action == 'get_clipboard':
            return {'text': self.clipboard.get_text()}
        elif action == 'set_clipboard':
            return self.clipboard.set_text(params['text'])
        elif action == 'find_window':
            return self.window.find_window(params['title'])
        elif action == 'activate_window':
            return self.window.activate(params['hwnd'])
        else:
            return {'error': f'Unknown action: {action}'}

# 导出单例
pc = PCAutomation()
