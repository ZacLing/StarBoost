# StarBoost

**Expert-in-the-loop annotation and improvement workspace for AI-generated deliverables.**

[English](README.md) | [中文](README.zh.md)

StarBoost helps domain experts turn their judgment into structured, repeatable annotation data. You give StarBoost a task package, let an AI assistant produce an initial answer, then review that answer the way an expert would: mark what is strong, identify concrete weaknesses, and optionally score the work.

After each review, the AI produces a new version of the work, and the expert can continue reviewing the updated result. Over multiple rounds, StarBoost records the expert feedback, improved outputs, timing, traces, and final export package, so the whole annotation process is easy to audit, compare, and reuse.

In practice, you use StarBoost as an expert-in-the-loop workspace: load a task, inspect the AI's output, write a structured review, submit it, and repeat until there are no remaining weaknesses worth sending into another improvement round.

## What It Helps You Do

| Expert task | How StarBoost helps |
| --- | --- |
| Review an AI deliverable | Opens a structured review template for strengths, weaknesses, notes, and scores. |
| Turn feedback into data | Stores each review as machine-readable metadata. |
| Improve an answer round by round | Sends the accepted weaknesses into the next AI production round. |
| Preserve the full process | Keeps outputs, traces, timing, review files, and export archives. |
| Keep task secrets hidden | Executors receive visible inputs only; rubrics and references stay out of the workspace. |

## Workflow

```text
Task package
  -> AI produces initial deliverable
  -> Expert reviews strengths and weaknesses
  -> AI produces an updated deliverable
  -> Expert reviews again
  -> Export the full annotation record
```

## Workspace UI

When you run `starboost`, the interactive workspace opens with a dashboard panel. It shows the current task, state, rounds, review progress, weakness minimum, key paths, and the suggested next action.

```text
+----------------------------------------------------------------------------------+
| StarBoost workspace                                                              |
+----------------------------------------------------------------------------------+
| Current task       simple_memo_task                                              |
| Status             awaiting_review                                               |
|                                                                                  |
| Common commands:                                                                 |
|   load_task <path>     load or resume a task package                             |
|   review               create/open the review file                               |
|   submit               submit review and continue                                |
|   status               show current task metadata                                |
|   home                 show this dashboard                                       |
|   exit                 leave StarBoost                                           |
|                                                                                  |
| Next               Run `review`, edit the review file, then run `submit`.        |
+----------------------------------------------------------------------------------+
```

## Quick Start

```bash
cd StarBoost
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

# Build the default Docker executor image from the bundled Dockerfile.
# StarBoost looks for this image unless you pass --docker-image.
docker build -t starboost-codex:latest -f docker/codex-boost.Dockerfile .

# Start the StarBoost workspace.
starboost

# Inside the workspace, load a task package.
starboost [no task]> load_task /path/to/package --executor-model gpt-5.5

# The loaded task becomes current, so the common loop no longer needs a path.
starboost [my_task]> review
starboost [my_task]> submit
starboost [my_task]> status
starboost [my_task]> home
```

StarBoost uses Docker by default. Build `starboost-codex:latest` before the first real executor run, otherwise Docker will report that the image cannot be found. The bundled Dockerfile installs the Codex CLI plus Python and common shell tools. StarBoost then starts each executor round in a locked-down container with only the round workspace and per-round `CODEX_HOME` mounted.

Direct commands work too. After `load_task`, StarBoost remembers the current task:

```bash
starboost load_task /path/to/package --executor-model gpt-5.5
starboost review
starboost submit
starboost status
```

Validate one of the bundled example packages:

```bash
starboost validate examples/simple_memo_task
```

Bundled examples include:

| Package | What it demonstrates | Review policy | Executor config |
| --- | --- | --- | --- |
| `examples/simple_memo_task` | A short implementation memo from project notes. | `min_strengths=1`, `initial_min_weaknesses=1`, decrement `1`; a lightweight one-issue demo. | Defaults. |
| `examples/code_cli_task` | A Python standard-library CLI deliverable with tests. | `min_strengths=2`, `initial_min_weaknesses=4`, decrement `2`; code review starts stricter but tapers faster. | `timeout_seconds=3600`. |
| `examples/biostats_csv_task` | A biostatistics summary CSV generated from trial measurements. | `min_strengths=1`, `initial_min_weaknesses=3`, decrement `1`; focused review for numeric correctness and formatting. | `timeout_seconds=1800`. |
| `examples/legal_risk_memo_task` | A legal-style vendor data-sharing risk memo grounded in supplied policy excerpts. | `min_strengths=3`, `initial_min_weaknesses=5`, decrement `1`; richer qualitative review for nuanced writing. | `timeout_seconds=2400`. |
| `examples/checkpoint_resume_task` | A pre-run checkpoint example with real `gpt-5.5` Docker traces. It has completed cold start plus one boost round and is waiting for the next review. | `min_strengths=2`, current `min_weaknesses=2`; demonstrates resume-and-continue behavior. | `timeout_seconds=2400`; generated with Docker + `gpt-5.5`. |

By default StarBoost uses Docker isolation for executor runs. See [Docker And Auth](docs/docker_and_auth.md) for image, credential, and `--docker-image` details.

## Task Packages

A StarBoost package should contain:

```text
my_task_package/
  original_task/
    task.json
    prompt.md
    rubrics.json
    materials/
      ...
```

StarBoost adds runtime files next to `original_task/`:

```text
my_task_package/
  starboost.json
  boost_runs/
  exports/
```

Executors never receive `rubrics.json` or `human_reference.json`; they only receive the prompt and visible materials copied into a clean workspace.

## Documentation

| Topic | English | Chinese |
| --- | --- | --- |
| Overview | [Overview](docs/overview.md) | [概览](docs/zh/overview.md) |
| Quickstart | [Quickstart](docs/quickstart.md) | [快速开始](docs/zh/quickstart.md) |
| Package Format | [Package Format](docs/package_format.md) | [任务包格式](docs/zh/package_format.md) |
| CLI Workflow | [CLI Workflow](docs/cli_workflow.md) | [命令行流程](docs/zh/cli_workflow.md) |
| Review Guidelines | [Review Guidelines](docs/review_guidelines.md) | [审阅指南](docs/zh/review_guidelines.md) |
| Docker And Auth | [Docker And Auth](docs/docker_and_auth.md) | [Docker 与认证](docs/zh/docker_and_auth.md) |
