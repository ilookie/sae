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
        half: str | None = None,
    ) -> None:
        """
        :param monitor: mss 的显示器索引。0=所有显示器合并，1=第一块屏，2=第二块屏，以此类推。
            例如在屏幕一运行程序、但要感知屏幕二时传 monitor=2。
        :param left, top, width, height: 若指定，则只截取该矩形区域；否则截整个 monitor。
        :param half: 若为 "left" 或 "right"，则只截取该屏幕左半或右半（忽略 left/top/width/height）。
        """
        self._monitor = monitor
        self._region = None
        self._half = (half or "").strip().lower() if half else None
        if self._half not in ("left", "right"):
            self._half = None
        if self._half is None and left is not None and top is not None and width is not None and height is not None:
            self._region = {"left": left, "top": top, "width": width, "height": height}

    def capture(self) -> State:
        import mss
        from PIL import Image

        with mss.mss() as sct:
            region = self._region
            if self._half and region is None:
                mon = sct.monitors[self._monitor]
                w, h = mon["width"], mon["height"]
                half_w = w // 2
                if self._half == "left":
                    region = {"left": mon["left"], "top": mon["top"], "width": half_w, "height": h}
                else:
                    region = {"left": mon["left"] + half_w, "top": mon["top"], "width": half_w, "height": h}
            if region:
                shot = sct.grab(region)
            else:
                shot = sct.grab(sct.monitors[self._monitor])
            # mss 返回 BGRA，转为 RGB numpy
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            arr = np.array(img)
        return State(image=arr, meta={"size": (shot.width, shot.height)})
