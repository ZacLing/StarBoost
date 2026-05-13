import json
import os
import stat
from pathlib import Path

import pytest

from starboost.config import RuntimeOverrides
from starboost.service import StarBoostError, StarBoostSession


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

    assert session.load_task_will_run_executor() is True
    status = session.load_task()
    assert session.load_task_will_run_executor() is False
    assert status["round_count"] == 1
    cold_output = package / "boost_runs" / "rounds" / "v000_cold_start" / "workspace" / "outputs" / "answer.md"
    assert cold_output.read_text(encoding="utf-8") == "cold deliverable"
    assert not (package / "boost_runs" / "rounds" / "v000_cold_start" / "workspace" / "inputs" / "human_reference.json").exists()

    review_info = session.start_review()
    review_path = Path(review_info["review_path"])
    review_path.write_text(
        """# Review

## Strengths
- It produced a file.

## Weaknesses
- It should mention the visible material.

## Latest Deliverables Satisfaction
(3)/5

## Latest Deliverables Aligns User Scores
(5)/10

## Notes
        """,
        encoding="utf-8",
    )
    assert session.submit_review_will_run_executor() is True
    result = session.submit_review()
    assert result["accepted"] is True
    assert result["terminated"] is False
    boosted_prompt = package / "boost_runs" / "rounds" / "v001_boosted" / "workspace" / "inputs" / "prompt.md"
    boosted_prompt_text = boosted_prompt.read_text(encoding="utf-8")
    assert boosted_prompt_text.startswith("# StarBoost Expert-Boosting Revision Round")
    assert "## Original Task Prompt\n\nCreate answer.md from the input." in boosted_prompt_text
    assert "You are not answering the reviewer" in boosted_prompt_text
    assert "Modify the deliverables" in boosted_prompt_text
    assert "Use only the weaknesses" in boosted_prompt_text
    assert "Do not structure the deliverable around the review comments" in boosted_prompt_text
    assert "Do not overfit to the wording of the weaknesses" in boosted_prompt_text
    boosted_output = package / "boost_runs" / "rounds" / "v001_boosted" / "workspace" / "outputs" / "answer.md"
    assert "visible material" in boosted_output.read_text(encoding="utf-8")

    second_review = session.start_review()
    second_path = Path(second_review["review_path"])
    second_path.write_text(
        """# Review

## Strengths
- It addressed the weakness.

## Weaknesses

## Latest Deliverables Satisfaction
(5)/5

## Latest Deliverables Aligns User Scores
(9)/10

## Notes
        """,
        encoding="utf-8",
    )
    assert session.submit_review_will_run_executor() is False
    terminal = session.submit_review()
    assert terminal["accepted"] is True
    assert terminal["terminated"] is True
    assert Path(terminal["export"]["path"]).exists()
    assert Path(session.export()["path"]).exists()


def test_export_requires_terminal_state_unless_forced(tmp_path: Path) -> None:
    fake = _fake_codex(tmp_path)
    package = _package(tmp_path, fake)
    session = StarBoostSession(package, RuntimeOverrides(executor_backend="local", codex_bin=str(fake), no_open=True))

    session.load_task()

    with pytest.raises(StarBoostError, match="not terminated"):
        session.export()

    snapshot = session.export(force=True)
    assert Path(snapshot["path"]).exists()


def test_load_task_archives_stale_incomplete_round(tmp_path: Path) -> None:
    fake = _fake_codex(tmp_path)
    package = _package(tmp_path, fake)
    stale_round = package / "boost_runs" / "rounds" / "v000_cold_start"
    stale_round.mkdir(parents=True)
    (stale_round / "stderr.log").write_text("interrupted", encoding="utf-8")

    session = StarBoostSession(package, RuntimeOverrides(executor_backend="local", codex_bin=str(fake), no_open=True))
    status = session.load_task()

    assert status["round_count"] == 1
    assert (package / "boost_runs" / "rounds" / "v000_cold_start" / "manifest.json").exists()
    stale_dirs = list((package / "boost_runs" / "stale").glob("v000_cold_start_*"))
    assert stale_dirs


def test_local_executor_resolves_relative_codex_bin(tmp_path: Path, monkeypatch) -> None:
    fake = _fake_codex(tmp_path)
    relative_fake = Path("fake_codex.py")
    package = _package(tmp_path, fake)
    monkeypatch.chdir(tmp_path)

    session = StarBoostSession(package, RuntimeOverrides(executor_backend="local", codex_bin=str(relative_fake), no_open=True))
    status = session.load_task()

    assert status["round_count"] == 1
    assert (package / "boost_runs" / "rounds" / "v000_cold_start" / "workspace" / "outputs" / "answer.md").exists()
