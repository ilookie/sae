"""Execute 抽象。"""

from abc import ABC, abstractmethod

from sae.action.base import Action


class Executor(ABC):
    """执行器：把 Action 变成真实操作。"""

    @abstractmethod
    def execute(self, action: Action) -> None:
        """执行给定的 Action。"""
        ...
