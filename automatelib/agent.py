"""
Agent Module - LLM 调用与任务执行
Re-exported from project root agent.py
"""

import sys
from pathlib import Path

# Re-export everything from root-level agent.py
_root_agent = Path(__file__).parent.parent / "agent.py"
if _root_agent.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("root_agent", _root_agent)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[__name__] = module
else:
    raise ImportError("agent.py not found in project root")
