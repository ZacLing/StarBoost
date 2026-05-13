import json
from pathlib import Path

from starboost.config import RuntimeOverrides
from starboost.state import load_or_initialize_state
from starboost.task_package import load_task_spec


def test_existing_checkpoint_paths_are_rebased_to_current_package_root(tmp_path: Path) -> None:
    task = tmp_path / "pkg" / "original_task"
    task.mkdir(parents=True)
    (task / "prompt.md").write_text("Do the task.", encoding="utf-8")
    (task / "task.json").write_text(json.dumps({"task_id": "checkpoint"}), encoding="utf-8")
    (task / "rubrics.json").write_text(
        json.dumps([{"id": "R001", "question": "Does it exist?", "expected": True, "fail_fast": True}]),
        encoding="utf-8",
    )
    (tmp_path / "pkg" / "starboost.json").write_text(
        json.dumps(
            {
                "schema_version": "starboost.state.v1",
                "package_id": "checkpoint",
                "status": "awaiting_review",
                "config": {},
                "current_round": 0,
                "latest_deliverable_round": "v000_cold_start",
                "next_review_index": 1,
                "current_min_strengths": 1,
                "current_min_weaknesses": 1,
                "rounds": [
                    {
                        "round_id": "v000_cold_start",
                        "round_index": 0,
                        "workspace": "<PACKAGE_ROOT>/boost_runs/rounds/v000_cold_start/workspace",
                        "outputs": "<PACKAGE_ROOT>/boost_runs/rounds/v000_cold_start/workspace/outputs",
                        "logs": "<PACKAGE_ROOT>/boost_runs/rounds/v000_cold_start/logs",
                        "artifact_manifest": {"root": "<PACKAGE_ROOT>/boost_runs/rounds/v000_cold_start/workspace/outputs"},
                    }
                ],
                "reviews": [],
                "exports": [],
            }
        ),
        encoding="utf-8",
    )

    spec = load_task_spec(tmp_path / "pkg")
    state = load_or_initialize_state(spec, RuntimeOverrides())
    round_record = state["rounds"][0]

    assert round_record["workspace"] == str(tmp_path / "pkg" / "boost_runs" / "rounds" / "v000_cold_start" / "workspace")
    assert round_record["outputs"] == str(
        tmp_path / "pkg" / "boost_runs" / "rounds" / "v000_cold_start" / "workspace" / "outputs"
    )
    assert round_record["logs"] == str(tmp_path / "pkg" / "boost_runs" / "rounds" / "v000_cold_start" / "logs")
    assert round_record["artifact_manifest"]["root"] == round_record["outputs"]
