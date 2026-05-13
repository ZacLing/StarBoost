# 命令行流程

[English](../cli_workflow.md) | [中文](cli_workflow.md)

StarBoost 支持直接命令和交互式 shell。

直接命令：

```bash
starboost validate <package>
starboost load_task <package>
starboost review <package>
starboost submit <package>
starboost status <package>
starboost export <package>
starboost shell
```

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

`load_task` 会创建运行目录。如果还没有已有产出，它会自动启动初始 AI 产出。`review` 会为最新产出创建 review 模板。`submit` 会校验模板，如果通过，就启动下一轮产出；如果满足零 weakness 终止规则，则结束流程并导出任务包。

`--executor-backend local` 只建议用于 smoke test 和调试。默认且推荐的隔离方式是 Docker。

