from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .config import RuntimeOverrides, apply_overrides
from .task_package import TaskSpec
from .util import read_json, utc_now, write_json


STATE_FILE = "starboost.json"


def state_path(package_root: Path) -> Path:
    return package_root / STATE_FILE


def has_state(package_root: Path) -> bool:
    return state_path(package_root).exists()


def load_state(package_root: Path) -> Dict[str, Any]:
    return read_json(state_path(package_root))


def save_state(package_root: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    write_json(state_path(package_root), state)


def initialize_state(spec: TaskSpec, overrides: RuntimeOverrides) -> Dict[str, Any]:
    config = apply_overrides(spec.starboost_config, overrides)
    if spec.timeout_seconds and overrides.timeout_seconds is None:
        config.setdefault("executor", {})["timeout_seconds"] = spec.timeout_seconds
    policy = config["review_policy"]
    now = utc_now()
    return {
        "schema_version": "starboost.state.v1",
        "package_id": spec.task_id,
        "created_at": now,
        "updated_at": now,
        "status": "initialized",
        "original_task_dir": spec.original_task_dir.relative_to(spec.package_root).as_posix()
        if spec.original_task_dir.is_relative_to(spec.package_root)
        else str(spec.original_task_dir),
        "config": config,
        "current_round": -1,
        "latest_deliverable_round": None,
        "next_review_index": 1,
        "current_min_strengths": int(policy.get("min_strengths", 3)),
        "current_min_weaknesses": int(policy.get("initial_min_weaknesses", 5)),
        "rounds": [],
        "reviews": [],
        "exports": [],
        "last_error": None,
    }


def load_or_initialize_state(spec: TaskSpec, overrides: RuntimeOverrides) -> Dict[str, Any]:
    if has_state(spec.package_root):
        state = load_state(spec.package_root)
        state["config"] = apply_overrides(state.get("config", {}), overrides)
        recover_rounds_from_manifests(spec.package_root, state)
        rebase_runtime_paths(spec.package_root, state)
        return state
    state = initialize_state(spec, overrides)
    recover_rounds_from_manifests(spec.package_root, state)
    rebase_runtime_paths(spec.package_root, state)
    return state


def latest_round(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rounds = state.get("rounds") or []
    if not rounds:
        return None
    return rounds[-1]


def recover_rounds_from_manifests(package_root: Path, state: Dict[str, Any]) -> None:
    if state.get("rounds"):
        return
    rounds_dir = package_root / "boost_runs" / "rounds"
    if not rounds_dir.exists():
        return
    recovered = []
    for manifest_path in sorted(rounds_dir.glob("*/manifest.json")):
        try:
            manifest = read_json(manifest_path)
        except Exception:
            continue
        if isinstance(manifest, dict):
            recovered.append(manifest)
    if not recovered:
        return
    recovered.sort(key=lambda item: int(item.get("round_index", 0)))
    latest = recovered[-1]
    state["rounds"] = recovered
    state["current_round"] = int(latest.get("round_index", len(recovered) - 1))
    state["latest_deliverable_round"] = latest.get("round_id")
    state["status"] = "awaiting_review"
    state["last_error"] = None


def rebase_runtime_paths(package_root: Path, state: Dict[str, Any]) -> None:
    for round_record in state.get("rounds") or []:
        round_id = round_record.get("round_id")
        if not round_id:
            continue
        round_root = package_root / "boost_runs" / "rounds" / str(round_id)
        workspace = round_root / "workspace"
        logs = round_root / "logs"
        outputs = workspace / "outputs"
        if "workspace" in round_record:
            round_record["workspace"] = str(workspace)
        if "outputs" in round_record:
            round_record["outputs"] = str(outputs)
        if "logs" in round_record:
            round_record["logs"] = str(logs)
        manifest = round_record.get("artifact_manifest")
        if isinstance(manifest, dict) and "root" in manifest:
            manifest["root"] = str(outputs)
