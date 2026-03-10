"""State 抽象：表示某一时刻的感知结果。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class State:
    """某一时刻的「状态」快照，供 Action 层消费。"""

    # 原始画面，numpy RGB (H, W, 3)，可选
    image: np.ndarray | None = None
    # 可选的附加信息（如 OCR 文本、结构化游戏状态等）
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.meta is None:
            self.meta = {}


class StateProvider(ABC):
    """State 提供者：负责捕获当前「画面/状态」。"""

    @abstractmethod
    def capture(self) -> State:
        """捕获当前状态并返回。"""
        ...
