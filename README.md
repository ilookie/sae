# SAE — State → Action → Execute

通过**感知**当前状态（如游戏画面）→ **模型决策**（Action）→ **执行**（键盘/鼠标等）的闭环框架。

## 概念

- **State**：感知层。例如截取屏幕或游戏窗口画面，得到「当前看到了什么」。
- **Action**：决策层。根据 State（可配合视觉/语言模型）输出要执行的动作描述。
- **Execute**：执行层。将 Action 转为真实输入（按键、点击、移动等）。

## 安装

使用 [uv](https://docs.astral.sh/uv/) 管理依赖（需先安装 uv）：

```bash
cd sae
uv sync
```

可选：带 LLM 相关依赖（LiteLLM + Gemini 视觉决策）

```bash
uv sync --extra llm
```

可选：带 GUI 依赖（Gradio，用于 Web 界面）

```bash
uv sync --extra gui
```

可选：带开发依赖（pytest、ruff）

```bash
uv sync --extra dev
```

## 项目结构

```
sae/
  src/sae/
    state/       # 感知：State、StateProvider、ScreenStateProvider
    action/      # 决策：Action、ActionModel、MockActionModel、GeminiActionModel
    execute/     # 执行：Executor、DesktopExecutor
    pipeline.py  # State → Action → Execute 主循环
  examples/
    run_loop.py   # 示例：截屏 + Mock 决策 + 执行
    run_gemini_loop.py  # 示例：Gemini 视觉决策
    run_gui.py    # 图形界面（tkinter）：配置显示器/区域/模式，启动与停止
    run_gui_web.py  # Web 界面（Gradio）：tkinter 不可用时使用
```

## 快速运行

```bash
uv run python examples/run_loop.py
```

默认会截取主屏、用 Mock 模型随机 noop/wait 跑 3 步。可在 `run_loop.py` 里修改 `action_pool` 测试真实按键（注意窗口焦点）。

### 使用 Gemini 分析画面并决策

安装 LLM 依赖后，可用 LiteLLM 调用 Gemini 视觉模型，根据截屏内容输出动作：

```bash
export GEMINI_API_KEY="你的 Gemini API Key"   # 或 GOOGLE_API_KEY
uv run python examples/run_gemini_loop.py
```

**多显示器**：在屏幕一运行程序、只感知屏幕二时，使用 `ScreenStateProvider(monitor=2, ...)`。mss 索引：0=全部，1=第一块屏，2=第二块屏。

### 图形界面（GUI）

在界面中选择显示器、截取区域（全部/左半/右半）、决策模式（Mock 或 Gemini），填写 API Key（可选，不填则用环境变量）后点击「启动」；「停止」可随时结束循环。日志区会输出每步的 Action 与 reason。

若本机 tkinter 不可用（例如 macOS 上出现 `Library not loaded: libtk8.6.dylib`），可改用 **Web 界面**（不依赖 Tk）：
```bash
uv sync --extra gui
uv run python examples/run_gui_web.py
```
浏览器打开 http://127.0.0.1:7860 即可使用。

```bash
uv run python examples/run_gui.py
```

使用 Gemini 时需先 `uv sync --extra llm` 并设置 API Key。

需在 [Google AI Studio](https://aistudio.google.com/apikey) 申请 API Key。LiteLLM 默认请求 `https://llm-proxy.lilithgames.com/v1`（OpenAI 兼容），可通过环境变量 `LITELLM_API_BASE` 或 `GeminiActionModel(api_base="...")` 覆盖。**使用默认代理时请将模型名写成 `openai/模型名`**（如 `openai/gemini-2.0-flash`），否则会走 Google/Vertex 路径并需要安装 `google-cloud-aiplatform`。`run_gemini_loop.py` 会截屏 → 发送给代理 → 解析返回的 JSON 动作 → 执行（键盘/鼠标/等待等）。

## 扩展

- **State**：实现 `StateProvider.capture()`，可接游戏内 API、模拟器帧等。
- **Action**：实现 `ActionModel.decide(state)`；已提供 `GeminiActionModel`（LiteLLM + Gemini 视觉）。
- **Execute**：实现 `Executor.execute(action)`，可接游戏 API、手柄等。

## 依赖

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/)：包与虚拟环境管理
- mss, Pillow, numpy：截屏与图像
- pynput：键盘、鼠标控制
- [LiteLLM](https://docs.litellm.ai/)（可选）：统一调用 Gemini 等模型，用于 `GeminiActionModel`
