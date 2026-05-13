from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .util import read_json


class TaskPackageError(ValueError):
    pass


@dataclass
class Rubric:
    rubric_id: str
    question: str
    expected: bool
    fail_fast: bool


@dataclass
class VisibleInput:
    source: Path
    destination: str


@dataclass
class TaskSpec:
    package_root: Path
    original_task_dir: Path
    task_id: str
    prompt_path: Path
    rubrics_path: Path
    human_reference_path: Optional[Path]
    visible_inputs: List[VisibleInput]
    rubrics: List[Rubric]
    allow_web_search: bool
    timeout_seconds: Optional[int]
    starboost_config: Dict[str, Any]


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"yes", "true", "1"}:
            return True
        if normalized in {"no", "false", "0"}:
            return False
    raise TaskPackageError(f"Expected boolean-like value, got {value!r}")


def _rubric_list(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("rubrics", "items"):
            if isinstance(raw.get(key), list):
                return raw[key]
    raise TaskPackageError("rubrics.json must be a list or an object with a rubrics list")


def load_rubrics(path: Path) -> List[Rubric]:
    raw = _rubric_list(read_json(path))
    rubrics: List[Rubric] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise TaskPackageError(f"Rubric #{index} is not an object")
        rubric_id = str(item.get("id") or item.get("rubric_id") or f"R{index:03d}")
        question = str(item.get("question") or item.get("judge_question") or item.get("description") or "").strip()
        if not question:
            raise TaskPackageError(f"Rubric {rubric_id} is missing a question")
        expected = as_bool(item.get("expected", item.get("expected_answer", True)))
        fail_fast = as_bool(item.get("fail_fast", False))
        rubrics.append(Rubric(rubric_id=rubric_id, question=question, expected=expected, fail_fast=fail_fast))
    return rubrics


def _resolve_original_task_dir(package_root: Path) -> Path:
    if (package_root / "original_task" / "task.json").exists():
        return package_root / "original_task"
    if (package_root / "task.json").exists():
        return package_root
    raise TaskPackageError(
        "Expected task.json at package root or original_task/task.json. "
        f"Checked package path: {package_root}"
    )


def _default_visible_inputs(task_dir: Path, prompt_path: Path, rubrics_path: Path, human_reference_path: Optional[Path]) -> List[VisibleInput]:
    excluded = {
        "task.json",
        prompt_path.name,
        rubrics_path.name,
        "rubrics.json",
        "human_reference.json",
        "reference",
        "references",
        "hidden",
        "answers",
        "solutions",
        "boost_runs",
        "exports",
        "starboost.json",
    }
    if human_reference_path:
        excluded.add(human_reference_path.name)
    visible: List[VisibleInput] = []
    materials_dir = task_dir / "materials"
    if materials_dir.exists():
        visible.append(VisibleInput(materials_dir, "materials"))
        return visible
    for item in sorted(task_dir.iterdir()):
        if item.name.startswith(".") or item.name in excluded:
            continue
        visible.append(VisibleInput(item, f"materials/{item.name}"))
    return visible


def _configured_visible_inputs(task_dir: Path, task_json: Dict[str, Any]) -> Optional[List[VisibleInput]]:
    if "materials_dir" in task_json:
        source = task_dir / str(task_json["materials_dir"])
        if not source.exists():
            raise TaskPackageError(f"materials_dir does not exist: {source}")
        return [VisibleInput(source, "materials")]
    if "files_dir" in task_json:
        source = task_dir / str(task_json["files_dir"])
        if not source.exists():
            raise TaskPackageError(f"files_dir does not exist: {source}")
        return [VisibleInput(source, "materials")]
    if isinstance(task_json.get("visible_files"), list):
        inputs: List[VisibleInput] = []
        for item in task_json["visible_files"]:
            if isinstance(item, str):
                inputs.append(VisibleInput(task_dir / item, f"materials/{Path(item).name}"))
            elif isinstance(item, dict):
                src = task_dir / str(item["source"])
                dst = str(item.get("destination") or f"materials/{src.name}")
                inputs.append(VisibleInput(src, dst))
            else:
                raise TaskPackageError("visible_files entries must be strings or objects")
        return inputs
    return None


def load_task_spec(package_path: Path) -> TaskSpec:
    package_root = package_path.resolve()
    task_dir = _resolve_original_task_dir(package_root)
    task_json_path = task_dir / "task.json"
    task_json = read_json(task_json_path)
    if not isinstance(task_json, dict):
        raise TaskPackageError("task.json must be a JSON object")

    task_id = str(task_json.get("task_id") or task_json.get("id") or package_root.name)
    prompt_file = str(task_json.get("prompt_file") or "prompt.md")
    rubrics_file = str(task_json.get("rubrics_file") or "rubrics.json")
    prompt_path = task_dir / prompt_file
    rubrics_path = task_dir / rubrics_file
    if not prompt_path.exists():
        raise TaskPackageError(f"prompt file does not exist: {prompt_path}")
    if not rubrics_path.exists():
        raise TaskPackageError(f"rubrics file does not exist: {rubrics_path}")

    human_reference_file = task_json.get("human_reference_file", "human_reference.json")
    human_reference_path = task_dir / str(human_reference_file)
    if not human_reference_path.exists():
        human_reference_path = None

    rubrics = load_rubrics(rubrics_path)
    visible_inputs = _configured_visible_inputs(task_dir, task_json)
    if visible_inputs is None:
        visible_inputs = _default_visible_inputs(task_dir, prompt_path, rubrics_path, human_reference_path)
    for visible in visible_inputs:
        if not visible.source.exists():
            raise TaskPackageError(f"visible input does not exist: {visible.source}")

    return TaskSpec(
        package_root=package_root,
        original_task_dir=task_dir,
        task_id=task_id,
        prompt_path=prompt_path,
        rubrics_path=rubrics_path,
        human_reference_path=human_reference_path,
        visible_inputs=visible_inputs,
        rubrics=rubrics,
        allow_web_search=bool(task_json.get("allow_web_search", False)),
        timeout_seconds=task_json.get("timeout_seconds"),
        starboost_config=dict(task_json.get("starboost", {})),
    )


def validate_task_spec(spec: TaskSpec) -> List[str]:
    errors: List[str] = []
    if not spec.rubrics:
        errors.append("rubrics.json must contain at least one rubric")
    for rubric in spec.rubrics:
        if not rubric.fail_fast:
            errors.append(f"Rubric {rubric.rubric_id} is not fail_fast; StarBoost requires fail-fast rubrics")
    return errors
