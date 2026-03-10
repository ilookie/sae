"""基于 LiteLLM + Gemini 的视觉决策：根据截屏画面由模型输出 Action。"""

from __future__ import annotations

import base64
import json
import re
from io import BytesIO

from sae.action.base import Action, ActionModel
from sae.state.base import State


# 默认 LiteLLM 代理地址（OpenAI 兼容接口，不走 Google SDK）
DEFAULT_API_BASE = "https://llm-proxy.lilithgames.com/v1"
# 使用自定义 api_base 时默认用 openai/ 前缀，避免 LiteLLM 走 Vertex/Google 路径
DEFAULT_MODEL_WITH_PROXY = "openai/gemini-2.0-flash"

# 系统提示：约束模型输出 JSON 格式的 Action
ACTION_SYSTEM_PROMPT = """你是一个根据当前屏幕画面做决策的助手。根据用户提供的截图，输出一个要执行的动作。

只回复一个 JSON 对象，不要其他解释。格式：
{"kind": "动作类型", "params": {...}, "reason": "简短理由"}

动作类型及 params 示例：
- noop: {"kind": "noop", "params": {}, "reason": "..."}  无需操作
- wait: {"kind": "wait", "params": {"duration": 0.5}, "reason": "..."}  等待秒数
- key: {"kind": "key", "params": {"key": "enter"}, "reason": "..."}  按键，key 可为 enter/space/esc/a/b/... 等
- mouse_click: {"kind": "mouse_click", "params": {"x": 100, "y": 200, "button": "left"}, "reason": "..."}  在 (x,y) 点击
- mouse_move: {"kind": "mouse_move", "params": {"x": 100, "y": 200}, "reason": "..."}  移动鼠标

若无法判断或不应操作，请返回 noop。"""


def _image_to_base64_data_url(image_array, format: str = "PNG") -> str:
    """将 numpy RGB 图像转为 data URL（base64）。"""
    from PIL import Image
    pil = Image.fromarray(image_array.astype("uint8"))
    buf = BytesIO()
    pil.save(buf, format=format)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    mime = "image/png" if format.upper() == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


def _parse_action_from_response(text: str) -> Action | None:
    """从模型回复中解析出 Action；失败返回 None。"""
    text = (text or "").strip()
    # 提取 ```json ... ``` 或第一个完整 {...} 块
    code_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if code_match:
        text = code_match.group(1)
    else:
        start = text.find("{")
        if start >= 0:
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        text = text[start : i + 1]
                        break
    try:
        data = json.loads(text)
        kind = (data.get("kind") or "noop").strip().lower()
        params = data.get("params")
        if not isinstance(params, dict):
            params = {}
        reason = data.get("reason", "")
        return Action(kind=kind, params=params, meta={"reason": reason})
    except (json.JSONDecodeError, TypeError):
        return None


class GeminiActionModel(ActionModel):
    """通过 LiteLLM 调用 Gemini 视觉模型，根据当前画面决策 Action。"""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
        image_format: str = "PNG",
        user_prompt: str = "请根据当前画面输出一个要执行的动作（仅回复上述格式的 JSON）。",
    ) -> None:
        """
        :param model: LiteLLM 模型名。使用默认代理时请用 openai/ 前缀（如 openai/gemini-2.0-flash），
            否则 LiteLLM 会走 Google/Vertex 并需要安装 google-cloud-aiplatform。
        :param api_base: LiteLLM 请求的 API 根地址；不传则用环境变量 LITELLM_API_BASE，再否则用默认代理。
        :param api_key: API Key；不传则使用环境变量 GEMINI_API_KEY 或 GOOGLE_API_KEY。
        :param image_format: 传给模型的图片格式，PNG 或 JPEG。
        :param user_prompt: 用户提示，可覆盖默认的「根据画面输出动作」说明。
        """
        self._api_base = api_base
        # 默认用 openai/ 前缀走 OpenAI 兼容接口，避免 LiteLLM 加载 Google/Vertex SDK
        self._model = model if model is not None else DEFAULT_MODEL_WITH_PROXY
        self._api_key = api_key
        self._image_format = image_format
        self._user_prompt = user_prompt

    def decide(self, state: State) -> Action:
        import os
        import litellm

        if state.image is None:
            return Action(kind="noop", params={}, meta={"reason": "no image"})

        image_url = _image_to_base64_data_url(state.image, self._image_format)
        api_key = self._api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        api_base = self._api_base or os.environ.get("LITELLM_API_BASE") or DEFAULT_API_BASE

        messages = [
            {"role": "system", "content": ACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self._user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                ],
            },
        ]

        try:
            response = litellm.completion(
                model=self._model,
                messages=messages,
                max_tokens=512,
                api_key=api_key,
                api_base=api_base,
            )
            content = (response.choices[0].message.content or "").strip()
            action = _parse_action_from_response(content)
            if action is not None:
                return action
        except Exception as e:
            return Action(
                kind="noop",
                params={},
                meta={"reason": f"model error: {e}", "error": str(e)},
            )
        return Action(kind="noop", params={}, meta={"reason": "parse failed"})
