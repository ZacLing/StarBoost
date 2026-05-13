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

## Quick Start

```bash
cd StarBoost
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

# Validate a task package, run cold start if needed, and create boost_runs/.
starboost load_task /path/to/package --executor-model gpt-5.5

# Create/open a review template for the latest deliverable.
starboost review /path/to/package

# After editing the review file, validate it and launch the next round.
starboost submit /path/to/package

# Show current state.
starboost status /path/to/package
```

Validate the bundled example package:

```bash
starboost validate examples/simple_memo_task
```

By default StarBoost uses Docker isolation for executor runs. See [Docker And Auth](docs/docker_and_auth.md) for the image and credential expectations.

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

