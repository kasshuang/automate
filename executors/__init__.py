"""
AutoMate Executors - 可插拔执行器
"""
from .pyautogui_executor import PyAutoGUIExecutor
from .playwright_executor import PlaywrightExecutor

__all__ = ["PyAutoGUIExecutor", "PlaywrightExecutor"]
