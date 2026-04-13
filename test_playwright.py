#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 Playwright 执行器"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from executors import PlaywrightExecutor

# 测试创建 - 使用非 headless 模式 + 已有Chrome
print("创建 PlaywrightExecutor (非headless模式)...")
browser = PlaywrightExecutor(
    headless=False,
    executable_path=r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
)

# 测试打开网页
print("打开百度...")
result = browser.goto("https://www.baidu.com")
print(f"结果: {result.get('status', result.get('error', 'ok'))}")

# 截图
print("截图...")
result = browser.screenshot("test_browser.png")
print(f"截图: {result.get('action')}")

# 关闭
print("关闭浏览器...")
browser.close()
print("完成!")
