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

第一次真实运行前，先构建默认 Docker executor 镜像：

```bash
docker build -t starboost-codex:latest -f docker/codex-boost.Dockerfile .
```

StarBoost 默认使用 Docker，并且会查找 `starboost-codex:latest`，除非你显式传入 `--docker-image <name>`。仓库自带的 Dockerfile 会安装 Codex CLI、Python 和常见 shell 工具。如果这个镜像不存在，`load_task` 或 `submit` 在启动 executor round 时可能会遇到 Docker 的 “No such image” 错误。

校验一个任务包：

```bash
starboost validate ./examples/my_task
```

仓库里包含几个示例：

```bash
starboost validate examples/simple_memo_task
starboost validate examples/code_cli_task
starboost validate examples/biostats_csv_task
starboost validate examples/legal_risk_memo_task
starboost validate examples/checkpoint_resume_task
```

这些示例刻意使用了不同的 review policy。例如 `simple_memo_task` 是最低 1 条 weakness 的轻量示例，`code_cli_task` 起始要求 4 条 weakness 且每轮递减 2 条，`legal_risk_memo_task` 使用更接近默认设置的 5 条 weakness 质性审阅流程。`checkpoint_resume_task` 则不同：它已经包含一次真实 Docker + `gpt-5.5` cold start 和一轮 boosted 结果，用户可以加载后直接从下一次 review 继续。

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
