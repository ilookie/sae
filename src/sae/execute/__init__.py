"""Execute 层：将 Action 转化为实际输入（键盘、鼠标等）。"""

from sae.execute.base import Executor
from sae.execute.desktop import DesktopExecutor

__all__ = ["Executor", "DesktopExecutor"]
