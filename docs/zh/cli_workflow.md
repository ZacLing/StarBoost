# 命令行流程

[English](../cli_workflow.md) | [中文](cli_workflow.md)

StarBoost 是一个命令行工作台。直接运行 `starboost` 会进入交互式界面，并显示 dashboard 面板：

```bash
starboost
```

界面 prompt 会显示当前任务：

```text
starboost [no task]>
starboost [simple_memo_task]>
```

dashboard 会展示当前任务、状态、轮次信息、关键路径和下一步建议。任何时候都可以输入 `home` 或 `dashboard` 再次显示。

在交互式界面中：

```text
starboost [no task]> load_task ./examples/simple_memo_task
starboost [simple_memo_task]> review
starboost [simple_memo_task]> submit
starboost [simple_memo_task]> status
starboost [simple_memo_task]> home
starboost [simple_memo_task]> exit
```

直接命令：

```bash
starboost validate <package>
starboost load_task <package>
starboost review [package]
starboost submit [package]
starboost status [package]
starboost export [package] [--force]
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

当 `load_task` 需要启动 cold-start executor，或者 `submit` 需要启动下一轮 boosted executor 时，CLI 会显示进度提示和 spinner。已有 checkpoint 的任务会直接加载，不会额外启动 executor。

如果 review 校验失败，StarBoost 会显示错误，并重新打开 review 文件和 deliverables，方便你直接修改。如果 executor 运行失败，任务状态会变成 `executor_failed`，dashboard 会显示最后的错误信息，并且失败 round 会被视为可重试，不会挡住后续重新运行。

`export` 默认只用于已经完成的任务。也就是说，只有任务状态变成 `terminated` 后，它才会正常导出，避免把仍在 review 循环中的中间状态误认为最终包。如果确实需要保存过程快照，可以使用 `starboost export --force`；这个导出应被视为 snapshot，而不是最终审完的交付包。

交互式模式会输出紧凑的面板，而不是原始 JSON，方便专家快速浏览当前状态。直接命令仍保留 JSON 风格输出，便于脚本和自动化使用。

`--executor-backend local` 只建议用于 smoke test 和调试。默认且推荐的隔离方式是 Docker。
