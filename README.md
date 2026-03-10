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

可选：带 LLM 相关依赖（后续接视觉/语言模型时用）

```bash
uv sync --extra llm
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
    action/      # 决策：Action、ActionModel、MockActionModel
    execute/     # 执行：Executor、DesktopExecutor
    pipeline.py  # State → Action → Execute 主循环
  examples/
    run_loop.py  # 示例：截屏 + Mock 决策 + 执行
```

## 快速运行

```bash
uv run python examples/run_loop.py
```

默认会截取主屏、用 Mock 模型随机 noop/wait 跑 5 步，不产生真实按键。可在 `run_loop.py` 里修改 `action_pool` 测试真实按键（注意窗口焦点）。

## 扩展

- **State**：实现 `StateProvider.capture()`，可接游戏内 API、模拟器帧等。
- **Action**：实现 `ActionModel.decide(state)`，可接 VLM/LLM 或强化学习策略。
- **Execute**：实现 `Executor.execute(action)`，可接游戏 API、手柄等。

## 依赖

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/)：包与虚拟环境管理
- mss, Pillow, numpy：截屏与图像
- pynput：键盘、鼠标控制
