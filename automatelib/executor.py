"""
Executor Module - 任务执行器
Re-exported from project root executor.py
"""

import sys
from pathlib import Path

# Re-export from root-level executor.py
_root_executor = Path(__file__).parent.parent / "executor.py"
if _root_executor.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("root_executor", _root_executor)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[__name__] = module
else:
    raise ImportError("executor.py not found in project root")
