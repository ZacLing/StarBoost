# Quickstart

Install the package in editable mode:

```bash
cd StarBoost
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

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
```

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
