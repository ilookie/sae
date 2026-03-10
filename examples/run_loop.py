#!/usr/bin/env python3
"""
SAE 示例：使用 Mock 决策模型跑通 State → Action → Execute 循环。

运行前请确保已安装依赖：pip install -e ".[llm]"
（不接 [llm] 也可，本示例只用 mock）

默认会截屏 5 步，每步间隔 1 秒，动作从 [noop, wait] 中随机，不会真的按键/点鼠标。
若要测试真实按键，可修改 ACTION_POOL。
"""

import sys
from pathlib import Path

# 允许从 examples 直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sae import SAEPipeline
from sae.action import Action, MockActionModel
from sae.execute import DesktopExecutor
from sae.state import ScreenStateProvider


def main() -> None:
    state_provider = ScreenStateProvider(monitor=1)
    action_pool = [
        Action("noop", {}),
        Action("wait", {"duration": 0.3}),
        # 取消下面注释可测试真实按键（注意焦点窗口）
        # Action("key", {"key": "a"}),
    ]
    action_model = MockActionModel(action_pool=action_pool, random_from_pool=True)
    executor = DesktopExecutor()

    pipeline = SAEPipeline(
        state_provider,
        action_model,
        executor,
        on_action=lambda a: print(f"  Action: {a.kind} {a.params}"),
    )

    print("SAE 运行 3 步，每步间隔 0.5s（仅 noop/wait）...")
    pipeline.run(max_steps=3, interval_seconds=0.5)
    print("Done. 可修改 action_pool 测试真实按键/鼠标。")


if __name__ == "__main__":
    main()
