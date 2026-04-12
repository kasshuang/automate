"""
AutoMate - AI驱动的PC自动化工具
https://github.com/kasshuang/automate
"""

__version__ = "0.1.0"
__author__ = "kasshuang"
__license__ = "MIT"

from automatelib.agent import TaskAgent, LLMClient, ConversationAgent
from automatelib.task_parser import TaskParser, ParsedTask, TaskType

__all__ = [
    "__version__",
    "TaskAgent",
    "LLMClient",
    "ConversationAgent",
    "TaskParser",
    "ParsedTask",
    "TaskType",
]
