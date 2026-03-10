"""桌面执行器：通过键盘、鼠标执行 Action。"""

from __future__ import annotations

import time
from pynput.keyboard import Controller as KeyController, Key, KeyCode
from pynput.mouse import Button, Controller as MouseController

from sae.action.base import Action
from sae.execute.base import Executor


# 常见按键名到 pynput Key 的映射（字符串形式用 pynput.keyboard.KeyCode 或 Key）
_KEY_MAP: dict[str, Key | None] = {
    "enter": Key.enter,
    "tab": Key.tab,
    "space": Key.space,
    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "alt": Key.alt,
    "esc": Key.esc,
    "backspace": Key.backspace,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
}


class DesktopExecutor(Executor):
    """使用 pynput 在桌面执行键盘、鼠标操作。"""

    def __init__(self, *, key_delay: float = 0.05, mouse_delay: float = 0.02) -> None:
        self._keyboard = KeyController()
        self._mouse = MouseController()
        self._key_delay = key_delay
        self._mouse_delay = mouse_delay

    def execute(self, action: Action) -> None:
        kind = (action.kind or "").strip().lower()
        params = action.params or {}

        if kind == "noop" or kind == "none":
            return

        if kind == "key" or kind == "key_press":
            self._do_key(params)
        elif kind == "key_combo":
            self._do_key_combo(params)
        elif kind == "mouse_click" or kind == "click":
            self._do_click(params)
        elif kind == "mouse_move" or kind == "move":
            self._do_move(params)
        elif kind == "wait":
            self._do_wait(params)
        else:
            # 未知类型仅记录，不抛错，便于扩展
            pass

    def _do_key(self, params: dict) -> None:
        key = params.get("key") or params.get("key_name")
        if key is None:
            return
        key_str = str(key).strip().lower()
        pynput_key = _KEY_MAP.get(key_str)
        if pynput_key is not None:
            self._keyboard.press(pynput_key)
            time.sleep(self._key_delay)
            self._keyboard.release(pynput_key)
        else:
            # 单字符或未映射的键
            kc = KeyCode.from_char(key_str) if len(key_str) == 1 else KeyCode.from_vk(0)
            if len(key_str) == 1:
                self._keyboard.press(kc)
                time.sleep(self._key_delay)
                self._keyboard.release(kc)

    def _do_key_combo(self, params: dict) -> None:
        keys = params.get("keys", [])
        if not keys:
            return
        mods = []
        main_key = None
        for k in keys:
            k = str(k).strip().lower()
            if k in _KEY_MAP and _KEY_MAP[k] is not None:
                if k in ("shift", "ctrl", "alt"):
                    mods.append(_KEY_MAP[k])
                else:
                    main_key = _KEY_MAP[k]
            else:
                main_key = k
        for m in mods:
            self._keyboard.press(m)
        time.sleep(self._key_delay)
        if main_key is not None:
            if isinstance(main_key, str) and len(main_key) == 1:
                main_key = KeyCode.from_char(main_key)
            if hasattr(main_key, "value") or hasattr(main_key, "char"):
                self._keyboard.press(main_key)
                self._keyboard.release(main_key)
            else:
                self._keyboard.press(main_key)
                self._keyboard.release(main_key)
        for m in reversed(mods):
            self._keyboard.release(m)

    def _do_click(self, params: dict) -> None:
        x = params.get("x")
        y = params.get("y")
        button = params.get("button", "left")
        if x is not None and y is not None:
            self._mouse.position = (int(x), int(y))
            time.sleep(self._mouse_delay)
        btn = Button.right if str(button).lower() == "right" else Button.left
        self._mouse.click(btn)
        time.sleep(self._mouse_delay)

    def _do_move(self, params: dict) -> None:
        x = params.get("x")
        y = params.get("y")
        if x is not None and y is not None:
            self._mouse.position = (int(x), int(y))
        time.sleep(self._mouse_delay)

    def _do_wait(self, params: dict) -> None:
        duration = float(params.get("duration", params.get("seconds", 0.1)))
        if duration > 0:
            time.sleep(duration)
