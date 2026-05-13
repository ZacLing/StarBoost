import json
import os
import stat
from pathlib import Path

from starboost.config import RuntimeOverrides
from starboost.service import StarBoostSession


def _fake_codex(tmp_path: Path) -> Path:
    script = tmp_path / "fake_codex.py"
    script.write_text(
        """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv[1:]
final_path = None
for i, arg in enumerate(args):
    if arg == "--output-last-message" and i + 1 < len(args):
        final_path = Path(args[i + 1])

prompt = sys.stdin.read()
workspace = Path.cwd()
outputs = workspace / "outputs"
outputs.mkdir(parents=True, exist_ok=True)
is_boosted = (workspace / "inputs" / "review_weaknesses.md").exists()
weakness_text = ""
if is_boosted:
    weakness_text = (workspace / "inputs" / "review_weaknesses.md").read_text(encoding="utf-8")
body = "boosted deliverable addressed: " + weakness_text if is_boosted else "cold deliverable"
(outputs / "answer.md").write_text(body, encoding="utf-8")
print(json.dumps({"type": "agent_message", "message": "fake complete"}))
print(json.dumps({"type": "command_execution", "command": "write answer", "output": body}))
if final_path:
    final_path.write_text("final: " + body, encoding="utf-8")
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _package(tmp_path: Path, fake_codex: Path) -> Path:
    root = tmp_path / "pkg"
    original = root / "original_task"
    materials = original / "materials"
    materials.mkdir(parents=True)
    (materials / "input.txt").write_text("visible material", encoding="utf-8")
    (original / "prompt.md").write_text("Create answer.md from the input.", encoding="utf-8")
    (original / "rubrics.json").write_text(
        json.dumps([{"id": "R001", "question": "Is answer.md present?", "expected": True, "fail_fast": True}]),
        encoding="utf-8",
    )
    (original / "human_reference.json").write_text(json.dumps({"secret": "not visible"}), encoding="utf-8")
    (original / "task.json").write_text(
        json.dumps(
            {
                "task_id": "fake_loop",
                "prompt_file": "prompt.md",
                "rubrics_file": "rubrics.json",
                "materials_dir": "materials",
                "starboost": {
                    "review_policy": {
                        "min_strengths": 1,
                        "initial_min_weaknesses": 1,
                        "weakness_decrement_per_round": 1,
                        "allow_zero_weakness_termination": True,
                    },
                    "executor": {"backend": "local", "codex_bin": str(fake_codex), "timeout_seconds": 10},
                },
            }
        ),
        encoding="utf-8",
    )
    return root


def test_full_loop_with_fake_codex(tmp_path: Path) -> None:
    fake = _fake_codex(tmp_path)
    package = _package(tmp_path, fake)
    session = StarBoostSession(package, RuntimeOverrides(executor_backend="local", codex_bin=str(fake), no_open=True))

    status = session.load_task()
    assert status["round_count"] == 1
    cold_output = package / "boost_runs" / "rounds" / "v000_cold_start" / "workspace" / "outputs" / "answer.md"
    assert cold_output.read_text(encoding="utf-8") == "cold deliverable"
    assert not (package / "boost_runs" / "rounds" / "v000_cold_start" / "workspace" / "inputs" / "human_reference.json").exists()

    review_info = session.start_review()
    review_path = Path(review_info["review_path"])
    review_path.write_text(
        """# Review

## Scores
- correctness: 3/5

## Strengths
- It produced a file.

## Weaknesses
- It should mention the visible material.

## Notes
""",
        encoding="utf-8",
    )
    result = session.submit_review()
    assert result["accepted"] is True
    assert result["terminated"] is False
    boosted_output = package / "boost_runs" / "rounds" / "v001_boosted" / "workspace" / "outputs" / "answer.md"
    assert "visible material" in boosted_output.read_text(encoding="utf-8")

    second_review = session.start_review()
    second_path = Path(second_review["review_path"])
    second_path.write_text(
        """# Review

## Scores
- correctness: 5/5

## Strengths
- It addressed the weakness.

## Weaknesses

## Notes
""",
        encoding="utf-8",
    )
    terminal = session.submit_review()
    assert terminal["accepted"] is True
    assert terminal["terminated"] is True
    assert Path(terminal["export"]["path"]).exists()

