# Docker 与认证

[English](../docker_and_auth.md) | [中文](docker_and_auth.md)

StarBoost 默认使用 Docker 作为 executor backend。每一轮运行时，StarBoost 只会把当前 round 的 workspace 和一个独立的 `CODEX_HOME` 挂载进容器。

镜像需要包含：

- `codex` CLI，并且在 `PATH` 中可用。
- Python 和常见 shell 工具。
- 如果任务允许 web search，需要容器具备网络访问能力。

构建镜像示例：

```bash
docker build -t starboost-codex:latest -f docker/codex-boost.Dockerfile .
```

认证处理：

- 默认 `--auth-mode copy-auth` 会在启动 Docker 前，把宿主机 `~/.codex/auth.json` 复制到本轮独立的 `CODEX_HOME`。
- `--auth-mode env` 会把宿主机中存在的认证环境变量传入容器，例如 `OPENAI_API_KEY`。
- `CODEX_HOME` 是逐轮隔离的，并且不会进入导出包。

Docker 隔离使用只读容器根目录、可写 workspace mount、可写 Codex home mount、drop capabilities 和 no-new-privileges。默认不关闭网络，因为很多 research task 可能需要联网。

## Local Backend 警告

`--executor-backend local` 会运行宿主机上的 Codex CLI。StarBoost 会把进程工作目录设置为当前 round 的 workspace，并请求 Codex 使用 `workspace-write` sandbox，但这不等价于 Docker 隔离。local 模式只适合 smoke test 和调试。如果 benchmark 运行要求 executor 不能看到 sibling files、hidden references、rubrics 或宿主机项目状态，请使用默认 Docker backend。

