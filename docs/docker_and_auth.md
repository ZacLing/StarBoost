# Docker And Auth

The default executor backend is Docker. StarBoost mounts only the round workspace and a fresh `CODEX_HOME` directory into the container.

Expected image contents:

- `codex` CLI available on `PATH`.
- Python and common shell utilities.
- Network access if the task allows web search.

Build your image separately, for example:

```bash
docker build -t starboost-codex:latest -f docker/codex-boost.Dockerfile .
```

Credential handling:

- Default `--auth-mode copy-auth` copies host `~/.codex/auth.json` into the per-round isolated `CODEX_HOME` before launching Docker.
- `--auth-mode env` passes credential environment variables such as `OPENAI_API_KEY` into the container when present.
- `CODEX_HOME` is per-run and excluded from exports.

Docker isolation uses a read-only container root, a writable mounted workspace, a writable mounted Codex home, dropped capabilities, and no-new-privileges. Network isolation is intentionally not enabled by default because many benchmark tasks allow research.

## Local Backend Warning

`--executor-backend local` runs the host-installed Codex CLI. StarBoost sets the process working directory to the round workspace and asks Codex for `workspace-write` sandboxing, but this is not equivalent to Docker isolation. Use local mode for smoke tests and debugging only. For benchmark runs where the executor must not see sibling files, hidden references, rubrics, or host project state, use the default Docker backend.
