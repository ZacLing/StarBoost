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

The repository includes a tiny example:

```bash
starboost validate examples/simple_memo_task
```

Start or resume the boosting loop:

```bash
starboost load_task ./examples/my_task --executor-model gpt-5.5
```

Create a review template:

```bash
starboost review ./examples/my_task
```

Edit the generated `review.md`, then submit it:

```bash
starboost submit ./examples/my_task
```

The minimum weakness count is only a lower bound. Experts can always write more weaknesses when they believe the result still needs work. When the minimum has decayed to zero, submitting zero weaknesses terminates the loop and writes a zip archive under `exports/`; submitting one or more weaknesses continues to the next round.
