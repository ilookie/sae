"""Action 抽象：决策层输出。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sae.state.base import State


@dataclass
class Action:
    """单次决策结果：要执行什么操作。"""

    # 动作类型，如 "key", "mouse_click", "mouse_move", "wait", "noop"
    kind: str
    # 参数，如 key 名、坐标、持续时间等
    params: dict[str, Any] = field(default_factory=dict)
    # 可选：模型给出的理由或置信度，便于调试
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.meta is None:
            self.meta = {}


class ActionModel(ABC):
    """决策模型：根据当前 State 输出 Action。"""

    @abstractmethod
    def decide(self, state: State) -> Action:
        """根据 state 决策并返回一个 Action。"""
        ...
