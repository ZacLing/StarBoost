# Quickstart

## Option A: Let Codex Install It For You

Open Codex with this repository folder as the workspace, or give Codex the absolute path to your local `StarBoost` folder. Then send Codex this prompt:

```text
Please understand this StarBoost project and install it on my computer.

Use the StarBoost repository path I provided as the project root. Set up the Python virtual environment, install the package in editable mode, build the default Docker executor image from docker/codex-boost.Dockerfile as starboost-codex:latest, validate all bundled example task packages, and run one bundled example task far enough to prove the CLI works. Prefer a safe built-in example and avoid changing unrelated files. At the end, report the exact commands you ran, whether Docker and Codex auth are ready, which example you ran, where the outputs were written, and any remaining setup I need to do.
```

Codex should end with a short report. If Docker is not running, the Docker image is missing, or Codex authentication is not configured, ask it to fix or explain that specific setup issue before running a real executor round.

## Option B: Manual Install

Install the package in editable mode:

```bash
cd StarBoost
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Build the default Docker executor image before the first real run:

```bash
docker build -t starboost-codex:latest -f docker/codex-boost.Dockerfile .
```

StarBoost uses Docker by default and looks for `starboost-codex:latest` unless you pass `--docker-image <name>`. The bundled Dockerfile installs the Codex CLI, Python, and common shell tools. If this image is missing, `load_task` or `submit` can fail with a Docker "No such image" error when an executor round starts.

Validate a task package:

```bash
starboost validate ./examples/my_task
```

The repository includes several examples:

```bash
starboost validate examples/simple_memo_task
starboost validate examples/code_cli_task
starboost validate examples/biostats_csv_task
starboost validate examples/legal_risk_memo_task
starboost validate examples/chinese_notice_task
starboost validate examples/checkpoint_resume_task
```

The examples intentionally use different review policies. For instance, `simple_memo_task` is a one-weakness lightweight demo, `code_cli_task` starts with four required weaknesses and decrements by two per accepted round, `legal_risk_memo_task` uses the default-style five-weakness qualitative review loop, and `chinese_notice_task` demonstrates Chinese task content with English paths and filenames. `checkpoint_resume_task` is different: it already contains a real Docker + `gpt-5.5` cold start and one boosted round, so you can load it and continue from the next review.

Start the interactive workspace:

```bash
starboost
```

Load a task package inside the workspace:

```text
starboost [no task]> load_task ./examples/my_task --executor-model gpt-5.5
```

The task is now current, so the common loop is short:

```text
starboost [my_task]> review
starboost [my_task]> submit
starboost [my_task]> status
```

Direct commands also remember the current task after `load_task`, so `starboost review` and `starboost submit` can omit the package path.

The minimum weakness count is only a lower bound. Experts can always write more weaknesses when they believe the result still needs work. When the minimum has decayed to zero, submitting zero weaknesses terminates the loop and writes a zip archive under `exports/`; submitting one or more weaknesses continues to the next round.
