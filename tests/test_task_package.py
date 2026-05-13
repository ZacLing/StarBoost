import json
from pathlib import Path

from starboost.task_package import load_task_spec, validate_task_spec


def test_package_validation_requires_fail_fast_rubrics(tmp_path: Path) -> None:
    task = tmp_path / "pkg" / "original_task"
    task.mkdir(parents=True)
    (task / "prompt.md").write_text("Do the task.", encoding="utf-8")
    (task / "task.json").write_text(json.dumps({"task_id": "demo"}), encoding="utf-8")
    (task / "rubrics.json").write_text(
        json.dumps(
            [
                {"id": "R001", "question": "Does it exist?", "expected": True, "fail_fast": True},
                {"id": "R002", "question": "Optional?", "expected": True, "fail_fast": False},
            ]
        ),
        encoding="utf-8",
    )
    spec = load_task_spec(tmp_path / "pkg")
    errors = validate_task_spec(spec)
    assert any("R002" in error for error in errors)

