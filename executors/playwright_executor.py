# -*- coding: utf-8 -*-
"""
Playwright Executor - Browser Automation
Using Playwright for browser operations
"""
import time
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PlaywrightExecutor:
    """Playwright Executor - Browser Automation"""
    
    def __init__(self, browser_type: str = "chromium", headless: bool = False, executable_path: str = None):
        """
        Initialize Playwright Executor
        
        Args:
            browser_type: browser type (chromium/firefox/webkit)
            headless: run in headless mode
            executable_path: path to browser executable
        """
        self.browser_type = browser_type
        self.headless = headless
        self.executable_path = executable_path or r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def _ensure_browser(self):
        """Ensure browser is started"""
        if self.browser is None:
            try:
                from playwright.sync_api import sync_playwright
                self.playwright = sync_playwright().start()
                browser_attr = getattr(self.playwright, self.browser_type)
                
                launch_opts = {"headless": self.headless}
                if self.executable_path and not self.headless:
                    launch_opts["executable_path"] = self.executable_path
                
                self.browser = browser_attr.launch(**launch_opts)
                self.context = self.browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                self.page = self.context.new_page()
                logger.info(f"Playwright {self.browser_type} started")
            except Exception as e:
                logger.error(f"Playwright launch failed: {e}")
                raise
    
    def goto(self, url: str, wait_until: str = "domcontentloaded") -> Dict:
        """Open URL"""
        self._ensure_browser()
        try:
            self.page.goto(url, wait_until=wait_until)
            return {"action": "goto", "url": url, "status": "success"}
        except Exception as e:
            return {"action": "goto", "url": url, "error": str(e)}
    
    def click(self, selector: str = None, x: int = None, y: int = None) -> Dict:
        """Click element or coordinates"""
        self._ensure_browser()
        try:
            if selector:
                self.page.click(selector)
                return {"action": "click", "selector": selector}
            elif x is not None and y is not None:
                self.page.mouse.click(x, y)
                return {"action": "click", "x": x, "y": y}
            else:
                return {"error": "Need selector or x,y coordinates"}
        except Exception as e:
            return {"error": str(e), "action": "click"}
    
    def type_text(self, selector: str, text: str, delay: int = 0) -> Dict:
        """Type text"""
        self._ensure_browser()
        try:
            self.page.fill(selector, text)
            return {"action": "type_text", "selector": selector, "text": text}
        except Exception as e:
            try:
                self.page.click(selector)
                self.page.keyboard.type(text, delay=delay)
                return {"action": "type_text", "selector": selector, "text": text, "fallback": True}
            except Exception as e2:
                return {"error": str(e2), "action": "type_text"}
    
    def press_key(self, key: str) -> Dict:
        """Press key"""
        self._ensure_browser()
        try:
            self.page.keyboard.press(key)
            return {"action": "press_key", "key": key}
        except Exception as e:
            return {"error": str(e), "action": "press_key"}
    
    def hotkey(self, *keys) -> Dict:
        """Hotkey"""
        self._ensure_browser()
        try:
            self.page.keyboard.press("+".join(keys))
            return {"action": "hotkey", "keys": list(keys)}
        except Exception as e:
            return {"error": str(e), "action": "hotkey"}
    
    def screenshot(self, filename: str = None, full_page: bool = False) -> Dict:
        """Screenshot"""
        self._ensure_browser()
        try:
            if filename:
                self.page.screenshot(path=filename, full_page=full_page)
                return {"action": "screenshot", "filename": filename}
            else:
                img = self.page.screenshot(full_page=full_page)
                b64 = base64.b64encode(img).decode()
                return {"action": "screenshot", "base64": b64}
        except Exception as e:
            return {"error": str(e), "action": "screenshot"}
    
    def get_text(self, selector: str) -> Dict:
        """Get element text"""
        self._ensure_browser()
        try:
            text = self.page.text_content(selector)
            return {"action": "get_text", "selector": selector, "text": text}
        except Exception as e:
            return {"error": str(e), "action": "get_text"}
    
    def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict:
        """Wait for element"""
        self._ensure_browser()
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return {"action": "wait_for_selector", "selector": selector}
        except Exception as e:
            return {"error": str(e), "action": "wait_for_selector"}
    
    def evaluate(self, script: str) -> Dict:
        """Execute JavaScript"""
        self._ensure_browser()
        try:
            result = self.page.evaluate(script)
            return {"action": "evaluate", "result": result}
        except Exception as e:
            return {"error": str(e), "action": "evaluate"}
    
    def close(self):
        """Close browser"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        logger.info("Playwright closed")
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict:
        """Execute action"""
        action_map = {
            "goto": lambda: self.goto(
                params.get("url", "about:blank"),
                params.get("wait_until", "domcontentloaded")
            ),
            "click": lambda: self.click(
                params.get("selector"),
                params.get("x"),
                params.get("y")
            ),
            "type_text": lambda: self.type_text(
                params.get("selector", ""),
                params.get("text", ""),
                params.get("delay", 0)
            ),
            "press_key": lambda: self.press_key(params.get("key", "")),
            "hotkey": lambda: self.hotkey(*params.get("keys", [])),
            "screenshot": lambda: self.screenshot(
                params.get("filename"),
                params.get("full_page", False)
            ),
            "get_text": lambda: self.get_text(params.get("selector", "")),
            "wait_for_selector": lambda: self.wait_for_selector(
                params.get("selector", ""),
                params.get("timeout", 30000)
            ),
            "evaluate": lambda: self.evaluate(params.get("script", "")),
        }
        
        if action in action_map:
            try:
                return action_map[action]()
            except Exception as e:
                return {"error": str(e), "action": action}
        else:
            return {"error": f"Unknown action: {action}", "action": action}


def create_browser_executor(headless: bool = False) -> PlaywrightExecutor:
    """Create browser executor"""
    return PlaywrightExecutor(headless=headless)
