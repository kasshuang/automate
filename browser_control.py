# -*- coding: utf-8 -*-
"""
持久化浏览器控制框架 v2 - 基于DrissionPage
- 自带浏览器内核，无需下载driver
- 支持持久化登录态
- HTTP API接口，可被外部脚本调用
"""
import os
import sys
import json
import time
import base64
import threading
import logging
from pathlib import Path

# 日志配置
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "browser_control.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# DrissionPage
from DrissionPage import ChromiumPage, ChromiumOptions

# 配置路径
PROFILE_DIR = Path(__file__).parent / "browser_profile"
PROFILE_DIR.mkdir(exist_ok=True)
COOKIE_FILE = PROFILE_DIR / "cookies.json"
COOKIE_BACKUP = PROFILE_DIR / "cookies_backup.json"
SCREENSHOT_DIR = PROFILE_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


class PersistentBrowser:
    """持久化浏览器控制"""
    
    def __init__(self, profile_path=None):
        self.page = None
        self.profile_path = profile_path or str(PROFILE_DIR)
        self._lock = threading.Lock()
        
        # 配置
        self.options = ChromiumOptions()
        self.options.set_argument('--disable-blink-features=AutomationControlled')
        self.options.set_argument('--start-maximized')
        self.options.set_argument(f'--user-data-dir={self.profile_path}')
        self.options.set_argument('--disable-extensions')
        self.options.set_argument('--disable-popup-blocking')
        # 不加载已安装的扩展（避免检测）
        self.options.set_argument('--disable-extensions')
        self.options.set_preference('excludeSwitches', ['enable-automation'])
        
        # 无头模式可通过参数切换
        self._headless = False
    
    def launch(self, headless=False):
        """启动浏览器"""
        with self._lock:
            if self.page is not None:
                try:
                    _ = self.page.url
                    logger.info("浏览器已运行")
                    return True
                except:
                    logger.warning("浏览器已断开，重新启动")
                    self.page = None
            
            logger.info(f"启动浏览器 (headless={headless})")
            self._headless = headless
            
            if headless:
                self.options.set_argument('--headless')
                self.options.set_argument('--disable-gpu')
            else:
                self.options.set_argument('--start-maximized')
            
            try:
                self.page = ChromiumPage(addr_or_opts=self.options)
                logger.info("浏览器启动成功")
                return True
            except Exception as e:
                logger.error(f"启动失败: {e}")
                return False
    
    def get(self, url, timeout=30):
        """导航到URL"""
        if not self.page:
            self.launch()
        try:
            self.page.get(url, timeout=timeout)
            time.sleep(1.5)
            logger.info(f"导航: {url} | 标题: {self.page.title}")
            return True
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False
    
    def click(self, target, timeout=10):
        """点击元素（支持多种定位方式）"""
        try:
            self.page(target).click(timeout=timeout)
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"点击失败 [{target}]: {e}")
            return False
    
    def input(self, target, text, clear=True):
        """输入文字"""
        try:
            ele = self.page(target)
            if clear:
                ele.clear()
            ele.input(text)
            time.sleep(0.3)
            return True
        except Exception as e:
            logger.error(f"输入失败 [{target}]: {e}")
            return False
    
    def wait(self, target, timeout=10):
        """等待元素出现"""
        try:
            self.page(target, timeout=timeout)
            return True
        except:
            return False
    
    def screenshot(self, path=None, full_page=False):
        """截图"""
        if not self.page:
            return None
        if not path:
            ts = int(time.time())
            path = SCREENSHOT_DIR / f"screenshot_{ts}.png"
        try:
            self.page.get_screenshot(path=str(path), full_page=full_page)
            logger.info(f"截图: {path}")
            return str(path)
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def scroll(self, distance=500):
        """滚动页面"""
        if not self.page:
            return
        self.page.run_js(f'window.scrollBy(0, {distance})')
        time.sleep(0.5)
    
    def get_cookies(self):
        """获取cookies"""
        if not self.page:
            return []
        try:
            return self.page.cookies().as_dict()
        except:
            return []
    
    def save_cookies(self, backup=True):
        """保存cookies到文件"""
        cookies = self.get_cookies()
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"Cookies已保存: {len(cookies)}个")
        
        if backup:
            with open(COOKIE_BACKUP, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        return len(cookies)
    
    def load_cookies(self):
        """从文件加载cookies"""
        if not os.path.exists(COOKIE_FILE):
            return 0
        try:
            with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            if cookies and self.page:
                self.page.set.cookies(cookies)
                logger.info(f"Cookies已加载: {len(cookies)}个")
                return len(cookies)
        except Exception as e:
            logger.error(f"加载Cookies失败: {e}")
        return 0
    
    def run_js(self, js):
        """执行JS代码"""
        if not self.page:
            return None
        try:
            return self.page.run_js(js)
        except Exception as e:
            logger.error(f"JS执行失败: {e}")
            return None
    
    def close(self):
        """关闭浏览器"""
        with self._lock:
            if self.page:
                try:
                    self.page.quit()
                except:
                    pass
                self.page = None
                logger.info("浏览器已关闭")
    
    def is_alive(self):
        """检查浏览器是否存活"""
        if not self.page:
            return False
        try:
            _ = self.page.url
            return True
        except:
            return False
    
    # ==================== 业务操作 ====================
    
    def wechat_login(self):
        """打开微信公众平台，等待扫码登录"""
        logger.info("打开微信公众平台...")
        self.get("https://mp.weixin.qq.com/")
        self.screenshot(SCREENSHOT_DIR / "wechat_login.png")
        logger.info("请在浏览器中扫码登录公众号后台")
        logger.info("登录后输入'ok'保存cookies，或输入'q'退出")
        return True
    
    def fetch_wechat_article(self, url):
        """抓取微信文章"""
        self.get(url)
        time.sleep(2)
        
        title = self.page.run_js(
            "return document.querySelector('h1#activity-name')?.innerText || document.title"
        )
        content = self.page.run_js(
            """
            () => {
                const article = document.querySelector('#js_content');
                if (!article) return '';
                const clone = article.cloneNode(true);
                clone.querySelectorAll('script,style').forEach(e => e.remove());
                return clone.innerText.trim();
            }
            """
        )
        screenshot = self.screenshot()
        
        return {
            'title': title or '',
            'content': content or '',
            'url': url,
            'screenshot': screenshot,
            'length': len(content or '')
        }
    
    def fetch_sina_weibo(self):
        """抓取微博热搜"""
        self.get("https://s.weibo.com/top/summary")
        time.sleep(3)
        
        items = self.page.eles('td.td-02 a')
        hot_list = []
        for item in items[:20]:
            text = item.text.strip()
            if text and text != '微博热搜':
                hot_list.append(text)
        
        self.screenshot(SCREENSHOT_DIR / "weibo_hot.png")
        return hot_list


# ==================== HTTP API服务 ====================

class BrowserAPI:
    """HTTP API服务器，供外部脚本调用"""
    
    def __init__(self, port=8765):
        self.port = port
        self.browser = PersistentBrowser()
        self._server = None
        self._running = False
    
    async def handle_request(self, scope):
        """处理HTTP请求（ASGI格式）"""
        method = scope['method']
        path = scope['path']
        
        # 解析参数
        query = {}
        if '?' in path:
            path, qs = path.split('?', 1)
            for pair in qs.split('&'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    query[urllib.parse.unquote(k)] = urllib.parse.unquote(v)
        
        headers = {k.decode(): v.decode() for k, v in scope.get('headers', [])}
        
        try:
            # 路由
            if path == '/api/launch':
                headless = query.get('headless', '').lower() == 'true'
                self.browser.launch(headless=headless)
                body = json.dumps({'status': 'ok', 'message': '浏览器已启动'}).encode()
            
            elif path == '/api/navigate':
                url = query.get('url', '')
                if not url:
                    raise ValueError("缺少url参数")
                self.browser.get(url)
                body = json.dumps({
                    'status': 'ok', 
                    'url': url, 
                    'title': self.browser.page.title if self.browser.page else ''
                }).encode()
            
            elif path == '/api/screenshot':
                path_s = self.browser.screenshot()
                body = json.dumps({'status': 'ok', 'path': path_s}).encode()
            
            elif path == '/api/cookies/save':
                count = self.browser.save_cookies()
                body = json.dumps({'status': 'ok', 'count': count}).encode()
            
            elif path == '/api/cookies/load':
                count = self.browser.load_cookies()
                body = json.dumps({'status': 'ok', 'count': count}).encode()
            
            elif path == '/api/wechat/article':
                url = query.get('url', '')
                if not url:
                    raise ValueError("缺少url参数")
                data = self.browser.fetch_wechat_article(url)
                body = json.dumps({'status': 'ok', 'data': data}, ensure_ascii=False).encode()
            
            elif path == '/api/wechat/login':
                self.browser.wechat_login()
                body = json.dumps({'status': 'ok', 'message': '请在浏览器中扫码登录'}).encode()
            
            elif path == '/api/weibo/hot':
                hot = self.browser.fetch_sina_weibo()
                body = json.dumps({'status': 'ok', 'hot': hot}, ensure_ascii=False).encode()
            
            elif path == '/api/eval':
                js = query.get('js', '')
                result = self.browser.run_js(js)
                body = json.dumps({'status': 'ok', 'result': str(result) if result else None}).encode()
            
            elif path == '/api/status':
                body = json.dumps({
                    'status': 'ok',
                    'alive': self.browser.is_alive(),
                    'title': self.browser.page.title if self.browser.page and self.browser.is_alive() else None
                }).encode()
            
            elif path == '/api/close':
                self.browser.close()
                body = json.dumps({'status': 'ok', 'message': '浏览器已关闭'}).encode()
            
            elif path == '/api/refresh':
                if self.browser.is_alive():
                    self.browser.page.refresh()
                    time.sleep(2)
                body = json.dumps({'status': 'ok'}).encode()
            
            else:
                body = json.dumps({
                    'status': 'ok',
                    'endpoints': [
                        '/api/launch?headless=false',
                        '/api/navigate?url=https://...',
                        '/api/screenshot',
                        '/api/cookies/save',
                        '/api/cookies/load',
                        '/api/wechat/login',
                        '/api/wechat/article?url=...',
                        '/api/weibo/hot',
                        '/api/eval?js=...',
                        '/api/status',
                        '/api/close',
                        '/api/refresh',
                    ]
                }, ensure_ascii=False).encode()
            
            return 200, [(b'Content-Type', b'application/json; charset=utf-8')], body
        
        except Exception as e:
            logger.exception("API请求失败")
            body = json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False).encode()
            return 500, [(b'Content-Type', b'application/json; charset=utf-8')], body
    
    async def app(self, scope, receive, send):
        """ASGI应用"""
        status, headers, body = await self.handle_request(scope)
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': headers,
        })
        await send({
            'type': 'http.response.body',
            'body': body,
        })
    
    def start(self, background=True):
        """启动API服务器"""
        import urllib.parse
        import asyncio
        
        async def run():
            import uvicorn
            config = uvicorn.Config(
                self.app,
                host='127.0.0.1',
                port=self.port,
                log_level='info',
            )
            server = uvicorn.Server(config)
            await server.serve()
        
        def run_sync():
            asyncio.run(run())
        
        if background:
            t = threading.Thread(target=run_sync, daemon=True)
            t.start()
            time.sleep(2)  # 等待服务器启动
            logger.info(f"API服务已启动: http://127.0.0.1:{self.port}")
            print(f"\n{'='*55}")
            print(f"  浏览器API服务已启动!")
            print(f"  地址: http://127.0.0.1:{self.port}")
            print(f"  文档: http://127.0.0.1:{self.port}/api/")
            print(f"{'='*55}\n")
        else:
            asyncio.run(run())


# ==================== 命令行入口 ====================

def main():
    import argparse
    import urllib.parse
    
    parser = argparse.ArgumentParser(description='持久化浏览器控制工具')
    parser.add_argument('--action', '-a', default='interactive',
                        choices=['launch', 'interactive', 'serve', 'wechat-login', 'weibo-hot', 'fetch-article'])
    parser.add_argument('--url', '-u', help='URL地址')
    parser.add_argument('--headless', action='store_true', help='无头模式')
    parser.add_argument('--port', '-p', type=int, default=8765, help='API端口')
    parser.add_argument('--screenshot', '-s', help='截图保存路径')
    args = parser.parse_args()
    
    browser = PersistentBrowser()
    
    if args.action == 'launch':
        browser.launch(headless=args.headless)
        if args.url:
            browser.get(args.url)
        input("按回车关闭...")
        browser.close()
    
    elif args.action == 'wechat-login':
        browser.launch()
        browser.wechat_login()
        while True:
            cmd = input("> ").strip()
            if cmd in ['ok', 'save', '保存']:
                browser.save_cookies()
                print("Cookies已保存!")
            elif cmd in ['q', 'quit', 'exit']:
                browser.close()
                break
            elif cmd == 'ss' or cmd == '截图':
                browser.screenshot()
                print("截图已保存!")
            elif cmd:
                print("输入 'ok' 保存cookies, '截图' 截图, 'q' 退出")
    
    elif args.action == 'weibo-hot':
        browser.launch(headless=True)
        hot = browser.fetch_sina_weibo()
        print("\n微博热搜TOP20:")
        for i, h in enumerate(hot, 1):
            print(f"  {i:2d}. {h}")
        browser.close()
    
    elif args.action == 'fetch-article':
        if not args.url:
            print("错误: 需要 --url 参数")
            return
        browser.launch(headless=True)
        data = browser.fetch_wechat_article(args.url)
        print(f"\n标题: {data['title']}")
        print(f"字数: {data['length']}")
        print(f"截图: {data['screenshot']}")
        print(f"\n内容预览（前500字）:\n{data['content'][:500]}")
        browser.close()
    
    elif args.action == 'serve':
        api = BrowserAPI(port=args.port)
        api.browser = browser
        browser.launch(headless=False)
        api.start(background=False)
    
    elif args.action == 'interactive':
        browser.launch(headless=False)
        if args.url:
            browser.get(args.url)
        print("\n交互模式: 输入命令")
        print("  open <url>    - 打开URL")
        print("  click <sel>   - 点击元素")
        print("  input <sel> <text> - 输入文字")
        print("  screenshot    - 截图")
        print("  cookies save  - 保存cookies")
        print("  cookies load  - 加载cookies")
        print("  js <code>     - 执行JS")
        print("  q/quit        - 退出")
        
        while True:
            try:
                cmd = input("\n> ").strip()
                if not cmd:
                    continue
                
                if cmd in ['q', 'quit', 'exit']:
                    break
                elif cmd == 'screenshot':
                    browser.screenshot()
                elif cmd.startswith('open '):
                    browser.get(cmd[5:])
                elif cmd == 'cookies save':
                    browser.save_cookies()
                elif cmd == 'cookies load':
                    browser.load_cookies()
                elif cmd.startswith('js '):
                    result = browser.run_js(cmd[3:])
                    print("Result:", result)
                else:
                    print("未知命令")
            except KeyboardInterrupt:
                break
        
        browser.close()


if __name__ == '__main__':
    main()
