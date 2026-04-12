"""
Browser Control Module - 浏览器自动化控制
Re-exported from project root browser_control.py
"""

import sys
from pathlib import Path

# Re-export from root-level browser_control.py
_root_browser = Path(__file__).parent.parent / "browser_control.py"
if _root_browser.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("root_browser", _root_browser)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[__name__] = module
else:
    raise ImportError("browser_control.py not found in project root")
