# CLI Workflow

StarBoost provides both direct commands and an interactive shell.

Direct commands:

```bash
starboost validate <package>
starboost load_task <package>
starboost review <package>
starboost submit <package>
starboost status <package>
starboost export <package>
starboost shell
```

Useful options:

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

`load_task` creates runtime folders and automatically runs the cold-start executor if no prior deliverable exists. `review` creates a template for the latest deliverable. `submit` validates that template and either launches the next executor round or terminates and exports the package if the zero-weakness termination rule is met.

Use `--executor-backend local` only for smoke tests. Docker is the default and recommended backend for isolation.
