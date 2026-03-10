"""基于屏幕截图的 State 提供者。"""

from __future__ import annotations

import numpy as np

from sae.state.base import State, StateProvider


class ScreenStateProvider(StateProvider):
    """从当前屏幕（或指定区域）截取画面作为 State。"""

    def __init__(
        self,
        *,
        monitor: int = 1,
        left: int | None = None,
        top: int | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """
        :param monitor: mss 的显示器索引，1 表示主屏。
        :param left, top, width, height: 若指定，则只截取该矩形区域；否则截整个 monitor。
        """
        self._monitor = monitor
        self._region = None
        if left is not None and top is not None and width is not None and height is not None:
            self._region = {"left": left, "top": top, "width": width, "height": height}

    def capture(self) -> State:
        import mss
        from PIL import Image

        with mss.mss() as sct:
            if self._region:
                shot = sct.grab(self._region)
            else:
                shot = sct.grab(sct.monitors[self._monitor])
            # mss 返回 BGRA，转为 RGB numpy
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            arr = np.array(img)
        return State(image=arr, meta={"size": (shot.width, shot.height)})
