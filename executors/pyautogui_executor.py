"""
PyAutoGUI Executor - 桌面操作执行器
使用 pyautogui 进行桌面自动化
"""
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PyAutoGUIExecutor:
    """PyAutoGUI 执行器 - 桌面操作"""
    
    def __init__(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.5
            self.pyautogui = pyautogui
        except ImportError:
            logger.error("PyAutoGUI 未安装: pip install pyautogui")
            raise
    
    def click(self, x: int, y: int, button: str = "left") -> Dict:
        """点击坐标"""
        self.pyautogui.click(x, y, button=button)
        return {"action": "click", "x": x, "y": y, "button": button}
    
    def double_click(self, x: int, y: int) -> Dict:
        """双击"""
        self.pyautogui.doubleClick(x, y)
        return {"action": "double_click", "x": x, "y": y}
    
    def right_click(self, x: int, y: int) -> Dict:
        """右键"""
        self.pyautogui.click(x, y, button="right")
        return {"action": "right_click", "x": x, "y": y}
    
    def move_to(self, x: int, y: int, duration: float = 0.5) -> Dict:
        """移动鼠标"""
        self.pyautogui.moveTo(x, y, duration=duration)
        return {"action": "move_to", "x": x, "y": y}
    
    def type_text(self, text: str, interval: float = 0.05) -> Dict:
        """输入文字"""
        self.pyautogui.write(text, interval=interval)
        return {"action": "type_text", "text": text}
    
    def press_key(self, key: str) -> Dict:
        """按键"""
        self.pyautogui.press(key)
        return {"action": "press_key", "key": key}
    
    def hotkey(self, *keys) -> Dict:
        """组合键"""
        self.pyautogui.hotkey(*keys)
        return {"action": "hotkey", "keys": list(keys)}
    
    def screenshot(self, filename: str = None) -> Dict:
        """截图"""
        if filename:
            self.pyautogui.screenshot(filename)
            return {"action": "screenshot", "filename": filename}
        else:
            return self.pyautogui.screenshot()
    
    def get_position(self) -> Dict:
        """获取鼠标位置"""
        pos = self.pyautogui.position()
        return {"x": pos.x, "y": pos.y}
    
    def scroll(self, clicks: int) -> Dict:
        """滚动"""
        self.pyautogui.scroll(clicks)
        return {"action": "scroll", "clicks": clicks}
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict:
        """执行动作"""
        action_map = {
            "click": lambda: self.click(
                params.get("x", 0), 
                params.get("y", 0), 
                params.get("button", "left")
            ),
            "double_click": lambda: self.double_click(
                params.get("x", 0), 
                params.get("y", 0)
            ),
            "right_click": lambda: self.right_click(
                params.get("x", 0), 
                params.get("y", 0)
            ),
            "move_mouse": lambda: self.move_to(
                params.get("x", 0),
                params.get("y", 0),
                params.get("duration", 0.5)
            ),
            "type_text": lambda: self.type_text(
                params.get("text", ""),
                params.get("interval", 0.05)
            ),
            "press_key": lambda: self.press_key(params.get("key", "enter")),
            "hotkey": lambda: self.hotkey(*params.get("keys", ["ctrl", "c"])),
            "screenshot": lambda: self.screenshot(params.get("filename")),
            "scroll": lambda: self.scroll(params.get("clicks", 100)),
        }
        
        if action in action_map:
            try:
                return action_map[action]()
            except Exception as e:
                logger.error(f"执行失败: {action} - {e}")
                return {"error": str(e), "action": action}
        else:
            return {"error": f"未知动作: {action}", "action": action}
