# 快速开始

[English](../quickstart.md) | [中文](quickstart.md)

以 editable 模式安装：

```bash
cd StarBoost
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

校验一个任务包：

```bash
starboost validate ./examples/my_task
```

仓库里包含一个极简示例：

```bash
starboost validate examples/simple_memo_task
```

启动交互式工作台：

```bash
starboost
```

在工作台中加载任务包：

```text
starboost [no task]> load_task ./examples/my_task --executor-model gpt-5.5
```

该任务会成为当前任务，常用循环会更短：

```text
starboost [my_task]> review
starboost [my_task]> submit
starboost [my_task]> status
```

直接命令也会记住当前任务。执行 `load_task` 之后，`starboost review` 和 `starboost submit` 可以省略 package path。

最低 weakness 数量只是下限。专家如果觉得结果仍然不满意，可以写更多 weaknesses；即使下限已经衰减到 0，只要提交一个或多个 weaknesses，流程就会继续进入下一轮。只有当下限为 0 且专家提交零个 weakness 时，流程才会结束，并在 `exports/` 下写出 zip 导出包。
