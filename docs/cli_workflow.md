# CLI Workflow

StarBoost is designed as a command-line workspace. Running `starboost` with no arguments opens the interactive shell and shows a dashboard panel:

```bash
starboost
```

The prompt shows the current task:

```text
starboost [no task]>
starboost [simple_memo_task]>
```

The dashboard gives the current task, status, round metadata, important paths, and a suggested next action. Use `home` or `dashboard` at any time to show it again.

Inside the shell:

```text
starboost [no task]> load_task ./examples/simple_memo_task
starboost [simple_memo_task]> review
starboost [simple_memo_task]> submit
starboost [simple_memo_task]> status
starboost [simple_memo_task]> home
starboost [simple_memo_task]> exit
```

Direct commands:

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

After `load_task`, StarBoost remembers the current task. That means `starboost review`, `starboost submit`, `starboost status`, and `starboost export` can be run without a package path. Explicit paths still work and always override the current task.

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

`load_task` creates runtime folders, automatically runs the initial executor if no prior deliverable exists, and makes the package the current task. `review` creates a template for the latest deliverable. `submit` validates that template and either launches the next executor round or terminates and exports the package if the zero-weakness termination rule is met.

When `load_task` needs to run a cold-start executor, or `submit` needs to launch the next boosted executor, the CLI prints a progress message and spinner. Existing checkpoint packages load quickly without starting a new executor.

If review validation fails, StarBoost reports the errors and reopens the review file and deliverables so you can fix the comments. If an executor run fails, the task status becomes `executor_failed`, the dashboard shows the last error, and the failed round is treated as retryable rather than blocking future attempts.

`export` is intended for completed packages. By default it only runs after the task status is `terminated`, which prevents an in-progress review loop from being mistaken for a final archive. If you intentionally need a mid-process archive, use `starboost export --force`; treat that output as a snapshot rather than the final reviewed package.

In interactive mode, StarBoost prints compact panels instead of raw JSON so the workspace is easier to scan. Direct commands keep JSON-style output for scripts and automation.

Use `--executor-backend local` only for smoke tests. Docker is the default and recommended backend for isolation.
