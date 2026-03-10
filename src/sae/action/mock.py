"""占位/测试用 Action 模型：不依赖视觉模型，可配置简单规则或随机。"""

import random
from sae.action.base import Action, ActionModel
from sae.state.base import State


class MockActionModel(ActionModel):
    """返回预设或随机的 Action，用于跑通 State → Execute 流程。"""

    def __init__(
        self,
        *,
        action_pool: list[Action] | None = None,
        default: Action | None = None,
        random_from_pool: bool = True,
    ) -> None:
        """
        :param action_pool: 可选动作列表，random_from_pool 时从中随机选。
        :param default: 若不使用 pool，则始终返回该 Action。
        :param random_from_pool: 为 True 时从 action_pool 随机；否则用 default。
        """
        self._pool = action_pool or []
        self._default = default or Action(kind="noop", params={})
        self._random = random_from_pool

    def decide(self, state: State) -> Action:
        if self._random and self._pool:
            return random.choice(self._pool)
        return self._default
