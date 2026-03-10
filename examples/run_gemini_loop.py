#!/usr/bin/env python3
"""
使用 Gemini 视觉模型分析截屏并决策动作，再执行。

需要先安装 LLM 依赖并设置 API Key：
  uv sync --extra llm
  export GEMINI_API_KEY="你的 API Key"

从 [Google AI Studio](https://aistudio.google.com/apikey) 获取 API Key。
LiteLLM 默认使用代理 https://llm-proxy.lilithgames.com/v1，可用 LITELLM_API_BASE 覆盖。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sae import SAEPipeline
from sae.action import GeminiActionModel
from sae.execute import DesktopExecutor
from sae.state import ScreenStateProvider


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("请设置环境变量 GEMINI_API_KEY 或 GOOGLE_API_KEY")
        sys.exit(1)

    # monitor=1 为第一块屏，monitor=2 为第二块屏；在屏幕一运行、感知屏幕二时改为 monitor=2
    state_provider = ScreenStateProvider(monitor=1)
    # 使用 openai/ 前缀走代理的 OpenAI 兼容接口，无需 Google Cloud SDK
    action_model = GeminiActionModel(
        model="openai/gemini-3.1-flash-image-preview",
        user_prompt="请根据当前画面输出一个要执行的动作（仅回复 JSON：kind、params、reason）。",
    )
    executor = DesktopExecutor()

    pipeline = SAEPipeline(
        state_provider,
        action_model,
        executor,
        on_action=lambda a: print(f"  Action: {a.kind} {a.params}  reason: {a.meta.get('reason', '')}"),
    )

    print("SAE + Gemini：截屏 → Gemini 决策 → 执行，共 3 步，间隔 2s...")
    pipeline.run(max_steps=20, interval_seconds=2.0)
    print("Done.")


if __name__ == "__main__":
    main()
