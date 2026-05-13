# Package Format

The package root contains source task inputs and StarBoost runtime state:

```text
task_package/
  original_task/
    task.json
    prompt.md
    rubrics.json
    human_reference.json        # optional, never shown to executors
    materials/                  # optional visible files
  starboost.json                # generated
  boost_runs/                   # generated
  exports/                      # generated
```

`task.json` minimum fields:

```json
{
  "task_id": "example_task",
  "prompt_file": "prompt.md",
  "rubrics_file": "rubrics.json",
  "materials_dir": "materials",
  "allow_web_search": false
}
```

All rubrics must be fail-fast in the first StarBoost release. This keeps the human review loop focused on tasks whose acceptance requirements are hard constraints rather than optional score items.

Visible executor inputs are copied into a clean workspace:

```text
workspace/
  inputs/
    prompt.md
    materials/
      ...
  outputs/
```

Boosted rounds additionally receive:

```text
workspace/
  inputs/
    previous_deliverables/
    review_weaknesses.md
```

Rubrics, hidden references, and expert reasoning are never copied into executor workspaces.

