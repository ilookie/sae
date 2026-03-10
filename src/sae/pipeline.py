"""SAE 主流程：State → Action → Execute 循环。"""

from __future__ import annotations

import time
from typing import Callable

from sae.action.base import Action, ActionModel
from sae.execute.base import Executor
from sae.state.base import State, StateProvider


class SAEPipeline:
    """一次「感知 → 决策 → 执行」的流水线；可循环运行。"""

    def __init__(
        self,
        state_provider: StateProvider,
        action_model: ActionModel,
        executor: Executor,
        *,
        on_state: Callable[[State], None] | None = None,
        on_action: Callable[[Action], None] | None = None,
    ) -> None:
        self._state_provider = state_provider
        self._action_model = action_model
        self._executor = executor
        self._on_state = on_state
        self._on_action = on_action

    def step(self) -> tuple[State, Action]:
        """执行一步：捕获 State → 决策 Action → 执行。"""
        state = self._state_provider.capture()
        if self._on_state:
            self._on_state(state)
        action = self._action_model.decide(state)
        if self._on_action:
            self._on_action(action)
        self._executor.execute(action)
        return state, action

    def run(
        self,
        *,
        max_steps: int | None = None,
        interval_seconds: float = 0.5,
        stop_if: Callable[[State, Action], bool] | None = None,
    ) -> None:
        """
        循环运行 SAE：每 interval_seconds 执行一步，直到达到 max_steps 或 stop_if 返回 True。
        """
        step_count = 0
        while True:
            if max_steps is not None and step_count >= max_steps:
                break
            state, action = self.step()
            step_count += 1
            if stop_if and stop_if(state, action):
                break
            if interval_seconds > 0:
                time.sleep(interval_seconds)
