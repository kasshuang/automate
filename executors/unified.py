# -*- coding: utf-8 -*-
"""
统一执行引擎 - AutoMate Phase 3 核心
HybridAgent 的执行层，负责把 ExecutionStep 路由到正确的执行器

策略：
- 浏览器任务（URL、打开网页）→ Playwright
- 桌面任务（坐标点击、键盘）→ PyAutoGUI
- 视觉任务（找图点击）→ 截图 + pyautogui
"""
import os
import re
import time
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 执行器懒加载（避免启动时依赖全加载）
# ─────────────────────────────────────────────

_pyautogui_executor = None
_playwright_executor = None


def _get_pyautogui():
    """懒加载 pyautogui"""
    global _pyautogui_executor
    if _pyautogui_executor is None:
        import pyautogui
        pyautogui.FAILSAFE = False  # AutoMate受控环境，关掉FAILSAFE防止误触发
        pyautogui.PAUSE = 0.3
        _pyautogui_executor = pyautogui
    return _pyautogui_executor


def _get_playwright():
    """懒加载 Playwright"""
    global _playwright_executor
    if _playwright_executor is None:
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            
            # 尝试使用系统Chrome（非headless模式）
            chrome_path = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
            
            try:
                browser = pw.chromium.launch(
                    headless=False,
                    executable_path=chrome_path if os.path.exists(chrome_path) else None,
                    args=["--disable-blink-features=AutomationControlled"]
                )
            except Exception:
                # 降级为headless
                browser = pw.chromium.launch(headless=True)
            
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            _playwright_executor = {
                "playwright": pw,
                "browser": browser,
                "context": context,
                "page": page,
            }
            logger.info("Playwright 浏览器启动成功（headless=False）")
        except Exception as e:
            logger.error(f"Playwright 启动失败: {e}")
            _playwright_executor = {"error": str(e)}
    return _playwright_executor


# ─────────────────────────────────────────────
# 任务类型判断
# ─────────────────────────────────────────────

def _is_browser_task(step) -> bool:
    """判断是否为浏览器任务"""
    task_desc = (
        step.description.lower() if step.description else ""
    ) + (step.action.lower() if step.action else "")
    
    # 明确是浏览器任务
    browser_signals = [
        "浏览器", "网页", "打开网页", "访问",
        "搜索", "baidu", "google", "bing", "http",
        "小红书", "抖音", "微博", "知乎", "b站",
        "douyin", "weibo", "zhihu", "bilibili",
        "登录", "注册", "网站",
    ]
    
    # 检查URL
    if re.match(r'^https?://', step.action) or (step.params.get("url") and re.match(r'^https?://', str(step.params.get("url")))):
        return True
    
    # 检查描述中是否包含浏览器信号
    if any(s in task_desc for s in browser_signals):
        return True
    
    # 打开浏览器应用
    if "打开" in task_desc and any(b in task_desc for b in ["浏览器", "edge", "chrome", "网页"]):
        return True
    
    return False


def _is_desktop_task(step) -> bool:
    """判断是否为桌面任务"""
    desktop_actions = [
        "click", "type_text", "press_key", "hotkey",
        "open_app", "screenshot", "move", "double_click", "right_click",
        "wait", "scroll"
    ]
    return step.action in desktop_actions


# ─────────────────────────────────────────────
# 浏览器执行
# ─────────────────────────────────────────────

def _execute_browser(step) -> Dict:
    """通过 Playwright 执行浏览器任务"""
    pw = _get_playwright()
    
    if isinstance(pw, dict) and "error" in pw:
        return {"action": step.action, "error": f"Playwright不可用: {pw['error']}"}
    
    page = pw["page"]
    action = step.action
    params = step.params
    result = {}
    
    try:
        # 打开URL
        if action == "goto" or action == "browser_open" or (params.get("url") and re.match(r'^https?://', str(params.get("url")))):
            url = params.get("url", step.action if re.match(r'^https?://', step.action) else f"https://{step.action}")
            if not re.match(r'^https?://', url):
                url = f"https://{url}"
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(1)  # 等渲染
            result = {"action": "goto", "url": url, "status": "success"}
            logger.info(f"打开网页: {url}")
        
        # 点击
        elif action == "click":
            x, y = params.get("x"), params.get("y")
            selector = params.get("selector")
            if selector:
                page.click(selector, timeout=5000)
                result = {"action": "click", "selector": selector}
            elif x is not None and y is not None:
                page.mouse.click(x, y)
                result = {"action": "click", "x": x, "y": y}
            else:
                result = {"action": "click", "error": "缺少坐标或selector"}
        
        # 输入文字
        elif action == "type_text":
            text = params.get("text", "")
            selector = params.get("selector", "")
            # 判断是否为URL
            is_url = bool(re.match(r'^https?://', text)) or bool(re.match(r'^[a-z0-9]+\.[a-z]+', text))
            if is_url:
                # URL → 先 Ctrl+L 定位地址栏
                page.keyboard.press("Control+l")
                time.sleep(0.3)
            elif selector:
                try:
                    page.fill(selector, text)
                except Exception:
                    page.click(selector)
                    page.keyboard.type(text, delay=50)
                result = {"action": "type_text", "selector": selector, "text": text[:20]}
                return result
            # 输入文字
            page.keyboard.type(text, delay=50)
            result = {"action": "type_text", "text": text[:20], "url_mode": is_url}
        
        # 按键
        elif action == "press_key":
            key = params.get("key", "Enter")
            # 规范化键名
            key_map = {
                "enter": "Enter", "回车": "Enter",
                "esc": "Escape", "escape": "Escape",
                "tab": "Tab",
                "space": " ", "空格": " ",
                "up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight",
                "删除": "Delete", "delete": "Delete",
            }
            key = key_map.get(key.lower(), key.title() if len(key) == 1 else key)
            page.keyboard.press(key)
            result = {"action": "press_key", "key": key}
        
        # 组合键
        elif action == "hotkey":
            keys = params.get("keys", [])
            # Playwright 键名映射
            KEY_ALIASES = {
                "ctrl": "Control", "control": "Control",
                "alt": "Alt",
                "shift": "Shift",
                "win": "Meta", "cmd": "Meta",
                "c": "c", "v": "v", "a": "a", "x": "x",
                "s": "s", "z": "z", "f": "f",
                "t": "t", "n": "n", "w": "w",
            }
            if len(keys) >= 2:
                # 先按修饰键，再按最后一个
                try:
                    for k in keys[:-1]:
                        mapped = KEY_ALIASES.get(k.lower(), k.title() if len(k) > 1 else k)
                        page.keyboard.down(mapped)
                    last_key = KEY_ALIASES.get(keys[-1].lower(), keys[-1].title() if len(keys[-1]) > 1 else keys[-1])
                    page.keyboard.down(last_key)
                    page.keyboard.up(last_key)
                    for k in reversed(keys[:-1]):
                        mapped = KEY_ALIASES.get(k.lower(), k.title() if len(k) > 1 else k)
                        page.keyboard.up(mapped)
                    result = {"action": "hotkey", "keys": keys}
                except Exception as e:
                    result = {"action": "hotkey", "keys": keys, "error": str(e)}
            else:
                k = keys[0] if keys else ""
                mapped = KEY_ALIASES.get(k.lower(), k.title() if len(k) > 1 else k)
                page.keyboard.press(mapped)
                result = {"action": "hotkey", "keys": keys}
        
        # 截图
        elif action == "screenshot":
            path = params.get("path", "browser_screenshot.png")
            page.screenshot(path=path, full_page=False)
            result = {"action": "screenshot", "filename": path}
            logger.info(f"浏览器截图: {path}")
        
        # 等待
        elif action == "wait":
            sec = params.get("seconds", 1)
            time.sleep(sec)
            result = {"action": "wait", "seconds": sec}
        
        # 等待元素
        elif action == "wait_for_selector":
            sel = params.get("selector", "")
            timeout = params.get("timeout", 30000)
            page.wait_for_selector(sel, timeout=timeout)
            result = {"action": "wait_for_selector", "selector": sel}
        
        # JS执行
        elif action == "evaluate":
            script = params.get("script", "")
            res = page.evaluate(script)
            result = {"action": "evaluate", "result": str(res)[:200]}
        
        else:
            result = {"action": action, "error": f"未知的浏览器操作: {action}"}
    
    except Exception as e:
        result = {"action": action, "error": str(e)}
        logger.error(f"浏览器执行失败 [{action}]: {e}")
    
    return result


# ─────────────────────────────────────────────
# 桌面执行
# ─────────────────────────────────────────────

def _execute_desktop(step) -> Dict:
    """通过 PyAutoGUI 执行桌面任务"""
    pyautogui = _get_pyautogui()
    action = step.action
    params = step.params
    result = {}
    
    try:
        # 打开应用（Win+R方式）
        if action == "open_app":
            app_id = params.get("app_id", "")
            if not app_id:
                app_id = params.get("text", "")
            pyautogui.hotkey("win", "r")
            time.sleep(0.5)
            pyautogui.write(app_id)
            time.sleep(0.3)
            pyautogui.press("enter")
            result = {"action": "open_app", "app": app_id}
            logger.info(f"打开应用: {app_id}")
        
        # 点击
        elif action == "click":
            x = params.get("x", 0)
            y = params.get("y", 0)
            button = params.get("button", "left")
            # 防止 FAILSAFE 触发（移动到角落会触发）
            x = max(5, min(x, 1910))
            y = max(5, min(y, 1070))
            pyautogui.click(x, y, button=button)
            result = {"action": "click", "x": x, "y": y, "button": button}
        
        # 双击
        elif action == "double_click":
            pyautogui.doubleClick(params.get("x", 0), params.get("y", 0))
            result = {"action": "double_click", "x": params.get("x", 0), "y": params.get("y", 0)}
        
        # 右键
        elif action == "right_click":
            pyautogui.click(params.get("x", 0), params.get("y", 0), button="right")
            result = {"action": "right_click", "x": params.get("x", 0), "y": params.get("y", 0)}
        
        # 移动鼠标
        elif action == "move":
            pyautogui.moveTo(params.get("x", 0), params.get("y", 0), duration=params.get("duration", 0.3))
            result = {"action": "move", "x": params.get("x", 0), "y": params.get("y", 0)}
        
        # 输入文字
        elif action == "type_text":
            text = params.get("text", "")
            interval = params.get("interval", 0.03)
            pyautogui.write(text, interval=interval)
            result = {"action": "type_text", "text": text[:30]}
        
        # 按键
        elif action == "press_key":
            key = params.get("key", "enter")
            pyautogui.press(key)
            result = {"action": "press_key", "key": key}
        
        # 组合键
        elif action == "hotkey":
            keys = params.get("keys", [])
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                # 防止FAILSAFE：Win键会移动鼠标到角落
                # 改为只执行非Win的组合键
                non_win_keys = [k for k in keys if k.lower() != 'win']
                if non_win_keys:
                    pyautogui.hotkey(*non_win_keys)
                else:
                    # 单独的Win键 → 打开开始菜单，手动处理
                    result = {"action": "hotkey", "keys": keys, "warning": "Win键被跳过"}
                    return result
            result = {"action": "hotkey", "keys": keys}
        
        # 截图
        elif action == "screenshot":
            import mss
            path = params.get("path", "desktop_screenshot.png")
            with mss.mss() as sct:
                sct.shot(output=path)
            result = {"action": "screenshot", "filename": path}
            logger.info(f"桌面截图: {path}")
        
        # 等待
        elif action == "wait":
            sec = params.get("seconds", 1)
            time.sleep(sec)
            result = {"action": "wait", "seconds": sec}
        
        # 滚动
        elif action == "scroll":
            amount = params.get("amount", 3)
            direction = params.get("direction", "down")
            pyautogui.scroll(-amount if direction == "down" else amount)
            result = {"action": "scroll", "direction": direction, "amount": amount}
        
        else:
            result = {"action": action, "error": f"未知的桌面操作: {action}"}
    
    except Exception as e:
        result = {"action": action, "error": str(e)}
        logger.error(f"桌面执行失败 [{action}]: {e}")
    
    return result


# ─────────────────────────────────────────────
# 视觉引导执行（找图/OCR点击）
# ─────────────────────────────────────────────

def _execute_vision(step) -> Dict:
    """视觉引导执行 - 截图后用AI识别目标位置"""
    import mss
    pyautogui = _get_pyautogui()
    action = step.action
    params = step.params
    
    # 截图
    screenshot_path = params.get("screenshot_path", "vision_screenshot.png")
    with mss.mss() as sct:
        sct.shot(output=screenshot_path)
    
    result = {"action": action, "screenshot": screenshot_path}
    
    if action == "find_and_click":
        # 尝试模板匹配
        template = params.get("template_path")
        if template and os.path.exists(template):
            try:
                loc = pyautogui.locateOnScreen(template, confidence=0.8)
                if loc:
                    center = pyautogui.center(loc)
                    pyautogui.click(center.x, center.y)
                    result.update({"found": True, "x": center.x, "y": center.y, "method": "template"})
                    return result
            except Exception:
                pass
        
        # 用描述找图标
        desc = params.get("image_desc", step.description)
        if desc:
            # 提示：需要AI视觉识别
            result.update({
                "found": False,
                "requires_vision": True,
                "image_desc": desc,
                "message": f"请手动点击: {desc}",
                "screenshot": screenshot_path
            })
        else:
            result.update({"error": "无template_path且无image_desc，无法定位"})
    
    return result


# ─────────────────────────────────────────────
# 统一执行入口
# ─────────────────────────────────────────────

def execute_step(step, verbose: bool = True) -> Dict:
    """
    统一执行入口 - 自动路由到正确的执行器
    
    路由策略：
    1. 浏览器任务 → Playwright
    2. 桌面任务 → PyAutoGUI
    3. 视觉任务 → 截图+匹配
    """
    if verbose:
        desc = step.description or step.action
        print(f"  → 执行: {desc}")
    
    # 自动路由判断
    if _is_browser_task(step):
        if verbose:
            print(f"    [浏览器] {step.action}")
        return _execute_browser(step)
    elif _is_desktop_task(step):
        if verbose:
            print(f"    [桌面] {step.action}")
        return _execute_desktop(step)
    elif step.action == "find_and_click":
        return _execute_vision(step)
    else:
        # 兜底到桌面
        return _execute_desktop(step)


def close_all():
    """关闭所有执行器资源"""
    global _playwright_executor, _pyautogui_executor
    
    if _playwright_executor and not isinstance(_playwright_executor, dict):
        try:
            _playwright_executor["page"].close()
            _playwright_executor["context"].close()
            _playwright_executor["browser"].close()
            _playwright_executor["playwright"].stop()
            logger.info("Playwright 已关闭")
        except Exception as e:
            logger.warning(f"Playwright 关闭失败: {e}")
    
    _playwright_executor = None
    _pyautogui_executor = None
