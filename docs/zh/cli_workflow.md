# 命令行流程

[English](../cli_workflow.md) | [中文](cli_workflow.md)

StarBoost 是一个命令行工作台。直接运行 `starboost` 会进入交互式界面：

```bash
starboost
```

界面 prompt 会显示当前任务：

```text
starboost [no task]>
starboost [simple_memo_task]>
```

在交互式界面中：

```text
starboost [no task]> load_task ./examples/simple_memo_task
starboost [simple_memo_task]> review
starboost [simple_memo_task]> submit
starboost [simple_memo_task]> status
starboost [simple_memo_task]> exit
```

直接命令：

```bash
starboost validate <package>
starboost load_task <package>
starboost review [package]
starboost submit [package]
starboost status [package]
starboost export [package]
starboost current
starboost clear
```

执行 `load_task` 后，StarBoost 会记住当前任务。因此 `starboost review`、`starboost submit`、`starboost status` 和 `starboost export` 都可以不再重复写 package path。显式传入 path 仍然可用，并且会优先于当前任务。

常用参数：

```bash
--executor-model gpt-5.5
--executor-backend docker
--executor-backend local
--codex-bin codex
--docker-image starboost-codex:latest
--auth-mode copy-auth
--timeout-seconds 3600
--no-open
```

`load_task` 会创建运行目录。如果还没有已有产出，它会自动启动初始 AI 产出，并把该任务设为当前任务。`review` 会为最新产出创建 review 模板。`submit` 会校验模板，如果通过，就启动下一轮产出；如果满足零 weakness 终止规则，则结束流程并导出任务包。

`--executor-backend local` 只建议用于 smoke test 和调试。默认且推荐的隔离方式是 Docker。
