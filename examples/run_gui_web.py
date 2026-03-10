#!/usr/bin/env python3
"""
SAE Web 界面（Gradio）：在浏览器中配置截屏、决策模式并运行流水线。不依赖系统 Tk。

若 run_gui.py 报错 ImportError: Library not loaded: ... libtk8.6.dylib（常见于 macOS pyenv），
请用本脚本代替：
  uv sync --extra gui
  uv run python examples/run_gui_web.py
"""

import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# 供 Stop 按钮与 pipeline 使用
_stop_event = threading.Event()
_log_lines: list[str] = []
_log_lock = threading.Lock()


def _run_pipeline(monitor: int, half: str, mode: str, api_key: str, max_steps_str: str, interval_str: str):
    """在后台线程运行 pipeline，把日志写入 _log_lines。"""
    from sae import SAEPipeline
    from sae.state import ScreenStateProvider
    from sae.execute import DesktopExecutor

    _stop_event.clear()
    with _log_lock:
        _log_lines.clear()
    half_val = half if half in ("left", "right") else None
    state_provider = ScreenStateProvider(monitor=monitor, half=half_val)
    try:
        max_steps = int(max_steps_str.strip() or "0") or None
    except ValueError:
        max_steps = None
    try:
        interval_seconds = float(interval_str.strip() or "2")
    except ValueError:
        interval_seconds = 2.0

    if mode == "gemini":
        try:
            from sae.action import GeminiActionModel
        except ImportError:
            with _log_lock:
                _log_lines.append("Error: 请先执行 uv sync --extra llm")
            return
        key = (api_key or "").strip() or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            with _log_lock:
                _log_lines.append("Error: 请填写 API Key 或设置 GEMINI_API_KEY")
            return
        action_model = GeminiActionModel(api_key=key)
    else:
        from sae.action import MockActionModel, Action
        action_model = MockActionModel(
            action_pool=[Action("noop", {}), Action("wait", {"duration": 0.3})],
            random_from_pool=True,
        )
    executor = DesktopExecutor()

    def on_action(a):
        with _log_lock:
            _log_lines.append(f"Action: {a.kind} {a.params}  reason: {a.meta.get('reason', '')}")

    pipeline = SAEPipeline(state_provider, action_model, executor, on_action=on_action)
    with _log_lock:
        _log_lines.append(f"--- 启动 屏{monitor} 区域={'左半' if half_val == 'left' else '右半' if half_val == 'right' else '全部'} {mode} ---")
    try:
        pipeline.run(
            max_steps=max_steps,
            interval_seconds=interval_seconds,
            stop_if=lambda s, a: _stop_event.is_set(),
        )
    except Exception as e:
        with _log_lock:
            _log_lines.append(f"Error: {e}")
    with _log_lock:
        _log_lines.append("--- 已停止 ---")


def run_and_stream(monitor, half: str, mode: str, api_key: str, max_steps: str, interval: str):
    """Gradio 的「运行」：在后台启动 pipeline，然后不断 yield 当前日志，直到结束或 Stop。"""
    import time
    try:
        monitor = int(monitor)
    except (TypeError, ValueError):
        yield "Error: 显示器请选择 1、2 或 3"
        return
    yield "启动中...\n"
    with _log_lock:
        _log_lines.clear()
    _stop_event.clear()
    thread = threading.Thread(
        target=_run_pipeline,
        args=(monitor, half, mode, api_key or "", max_steps or "20", interval or "2.0"),
        daemon=True,
    )
    thread.start()
    last_n = 0
    while thread.is_alive():
        with _log_lock:
            lines = list(_log_lines)
            n = len(lines)
        if n > last_n:
            yield "\n".join(lines)
            last_n = n
        time.sleep(0.25)
    with _log_lock:
        lines = list(_log_lines)
    yield "\n".join(lines) if lines else "--- 已停止 ---"


def stop_run():
    """Gradio 的「停止」按钮：设置停止事件。"""
    _stop_event.set()
    return "已请求停止，当前步结束后将停止。"


def main():
    try:
        import gradio as gr
    except ImportError:
        print("请先安装 GUI 依赖: uv sync --extra gui")
        sys.exit(1)

    with gr.Blocks(title="SAE — State → Action → Execute", css=".log { font-size: 12px; }") as demo:
        gr.Markdown("## SAE — State → Action → Execute")
        with gr.Row():
            monitor = gr.Radio(choices=[1, 2, 3], value=1, label="显示器", type="value")
            half = gr.Radio(choices=["全部", "左半", "右半"], value="全部", label="截取区域")
        with gr.Row():
            mode = gr.Radio(choices=["mock", "gemini"], value="gemini", label="决策模式")
            api_key = gr.Textbox(label="API Key（Gemini 必填或设环境变量）", type="password", placeholder="可选")
        with gr.Row():
            max_steps = gr.Textbox(value="20", label="最大步数")
            interval = gr.Textbox(value="2.0", label="间隔(秒)")
        half_map = {"全部": "", "左半": "left", "右半": "right"}
        run_btn = gr.Button("启动", variant="primary")
        stop_btn = gr.Button("停止")
        log_out = gr.Textbox(label="日志", lines=14, max_lines=20, interactive=False, elem_classes=["log"])
        stop_msg = gr.Textbox(visible=False)

        def run(mon_val, half_label, mode_val, api_key_val, max_val, interval_val):
            half_val = half_map.get(half_label, "") if half_label else ""
            try:
                for text in run_and_stream(mon_val, half_val, mode_val, api_key_val or "", max_val or "20", interval_val or "2.0"):
                    yield text
            except Exception as e:
                yield f"Error: {e}"

        run_btn.click(
            fn=run,
            inputs=[monitor, half, mode, api_key, max_steps, interval],
            outputs=log_out,
            show_progress="minimal",
        )
        stop_btn.click(fn=stop_run, outputs=stop_msg)

    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
