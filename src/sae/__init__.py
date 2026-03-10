"""
SAE: State → Action → Execute

通过感知存在的事务（如游戏画面）→ 模型决策（Action）→ 执行（Execute）的闭环框架。
"""

__version__ = "0.1.0"

from sae.state import State, StateProvider
from sae.action import Action, ActionModel, GeminiActionModel
from sae.execute import Executor
from sae.pipeline import SAEPipeline

__all__ = [
    "State",
    "StateProvider",
    "Action",
    "ActionModel",
    "GeminiActionModel",
    "Executor",
    "SAEPipeline",
]
