"""
Task Parser Module - 自然语言任务解析器
Re-exported from project root task_parser.py
"""

import sys
from pathlib import Path

# Re-export everything from root-level task_parser.py
_root_parser = Path(__file__).parent.parent / "task_parser.py"
if _root_parser.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("root_task_parser", _root_parser)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[__name__] = module
else:
    raise ImportError("task_parser.py not found in project root")
