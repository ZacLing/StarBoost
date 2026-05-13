import json
import stat
from pathlib import Path

from starboost.cli import main
from starboost.context import get_current_task_path


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
sys.stdin.read()
(Path.cwd() / "outputs").mkdir(parents=True, exist_ok=True)
(Path.cwd() / "outputs" / "answer.md").write_text("ok", encoding="utf-8")
print(json.dumps({"type": "agent_message", "message": "ok"}))
if final_path:
    final_path.write_text("ok", encoding="utf-8")
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _package(tmp_path: Path) -> Path:
    root = tmp_path / "pkg"
    original = root / "original_task"
    materials = original / "materials"
    materials.mkdir(parents=True)
    (materials / "note.txt").write_text("hello", encoding="utf-8")
    (original / "prompt.md").write_text("Write answer.md.", encoding="utf-8")
    (original / "rubrics.json").write_text(
        json.dumps([{"id": "R001", "question": "Exists?", "expected": True, "fail_fast": True}]),
        encoding="utf-8",
    )
    (original / "task.json").write_text(
        json.dumps(
            {
                "task_id": "cli_current_demo",
                "prompt_file": "prompt.md",
                "rubrics_file": "rubrics.json",
                "materials_dir": "materials",
                "starboost": {"executor": {"backend": "local"}},
            }
        ),
        encoding="utf-8",
    )
    return root


def test_load_task_sets_current_and_status_can_omit_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    fake = _fake_codex(tmp_path)
    package = _package(tmp_path)

    assert main(["load_task", str(package), "--executor-backend", "local", "--codex-bin", str(fake), "--no-open"]) == 0
    assert get_current_task_path() == package.resolve()
    assert main(["status"]) == 0
    assert main(["current"]) == 0
    assert main(["clear"]) == 0
    assert get_current_task_path() is None

