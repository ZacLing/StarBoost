from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import RuntimeOverrides
from .executor import run_executor_round
from .exporter import export_package
from .review import create_review_template, parse_review, review_dir, save_review_json, validate_review
from .state import latest_round, load_or_initialize_state, save_state
from .task_package import TaskPackageError, load_task_spec, validate_task_spec
from .util import ensure_dir, utc_now, write_json


class StarBoostError(RuntimeError):
    pass


class StarBoostSession:
    def __init__(self, package_path: Path, overrides: Optional[RuntimeOverrides] = None) -> None:
        self.spec = load_task_spec(package_path)
        self.overrides = overrides or RuntimeOverrides()
        self.state = load_or_initialize_state(self.spec, self.overrides)

    @property
    def package_root(self) -> Path:
        return self.spec.package_root

    def validate(self) -> Dict[str, Any]:
        errors = validate_task_spec(self.spec)
        return {"valid": not errors, "errors": errors, "task_id": self.spec.task_id}

    def load_task_will_run_executor(self) -> bool:
        return not bool(self.state.get("rounds"))

    def load_task(self) -> Dict[str, Any]:
        validation = self.validate()
        if not validation["valid"]:
            raise TaskPackageError("; ".join(validation["errors"]))
        ensure_dir(self.package_root / "boost_runs" / "rounds")
        ensure_dir(self.package_root / "boost_runs" / "reviews")
        ensure_dir(self.package_root / "exports")
        if not self.state.get("rounds"):
            self.state["status"] = "running_cold_start"
            save_state(self.package_root, self.state)
            try:
                metadata = run_executor_round(self.spec, self.state)
            except Exception as exc:
                self.state["status"] = "executor_failed"
                self.state["last_error"] = str(exc)
                save_state(self.package_root, self.state)
                raise
            self.state["rounds"].append(metadata)
            self.state["current_round"] = metadata["round_index"]
            self.state["latest_deliverable_round"] = metadata["round_id"]
            self.state["status"] = "awaiting_review"
            self.state["last_error"] = None
        else:
            self.state["status"] = self.state.get("status") or "awaiting_review"
        save_state(self.package_root, self.state)
        return self.status()

    def status(self) -> Dict[str, Any]:
        current = latest_round(self.state)
        return {
            "package_id": self.state.get("package_id"),
            "status": self.state.get("status"),
            "round_count": len(self.state.get("rounds") or []),
            "review_count": len(self.state.get("reviews") or []),
            "latest_round": current["round_id"] if current else None,
            "latest_outputs": current["outputs"] if current else None,
            "current_min_strengths": self.state.get("current_min_strengths"),
            "current_min_weaknesses": self.state.get("current_min_weaknesses"),
            "next_review_index": self.state.get("next_review_index"),
            "exports": self.state.get("exports") or [],
            "last_error": self.state.get("last_error"),
        }

    def start_review(self) -> Dict[str, Any]:
        current = latest_round(self.state)
        if not current:
            raise StarBoostError("No deliverable exists. Run load_task first.")
        index = int(self.state.get("next_review_index") or 1)
        directory = review_dir(self.package_root, index)
        ensure_dir(directory)
        review_path = directory / "review.md"
        if not review_path.exists():
            create_review_template(
                review_path,
                str(self.state.get("package_id")),
                str(current["round_id"]),
                Path(str(current["outputs"])),
                int(self.state.get("current_min_strengths") or 0),
                int(self.state.get("current_min_weaknesses") or 0),
            )
        self.state["status"] = "awaiting_review"
        save_state(self.package_root, self.state)
        return {"review_path": str(review_path), "deliverables_path": current["outputs"]}

    def submit_review_will_run_executor(self, review_path: Optional[Path] = None) -> bool:
        current = latest_round(self.state)
        if not current:
            return False
        index = int(self.state.get("next_review_index") or 1)
        if review_path is None:
            review_path = review_dir(self.package_root, index) / "review.md"
        if not review_path.exists():
            return False

        parsed = parse_review(review_path)
        validation = validate_review(
            parsed,
            int(self.state.get("current_min_strengths") or 0),
            int(self.state.get("current_min_weaknesses") or 0),
        )
        if not validation["valid"]:
            return False

        policy = self.state["config"].get("review_policy", {})
        current_min_weaknesses = int(self.state.get("current_min_weaknesses") or 0)
        terminal = (
            current_min_weaknesses == 0
            and len(parsed.weaknesses) == 0
            and policy.get("allow_zero_weakness_termination", True)
        )
        return not terminal

    def submit_review(self, review_path: Optional[Path] = None) -> Dict[str, Any]:
        current = latest_round(self.state)
        if not current:
            raise StarBoostError("No deliverable exists. Run load_task first.")
        index = int(self.state.get("next_review_index") or 1)
        if review_path is None:
            review_path = review_dir(self.package_root, index) / "review.md"
        if not review_path.exists():
            raise StarBoostError(f"Review file does not exist: {review_path}")

        parsed = parse_review(review_path)
        validation = validate_review(
            parsed,
            int(self.state.get("current_min_strengths") or 0),
            int(self.state.get("current_min_weaknesses") or 0),
        )
        save_review_json(review_path.parent / "review.json", parsed, validation)
        write_json(review_path.parent / "validation.json", validation)
        if not validation["valid"]:
            return {
                "accepted": False,
                "validation": validation,
                "review_path": str(review_path),
                "deliverables_path": current["outputs"],
            }

        review_record = {
            "review_id": parsed.review_id,
            "submitted_at": utc_now(),
            "review_path": str(review_path),
            "review_json": str(review_path.parent / "review.json"),
            "round_under_review": current["round_id"],
            "strength_count": len(parsed.strengths),
            "weakness_count": len(parsed.weaknesses),
            "scores": parsed.scores,
        }
        policy = self.state["config"].get("review_policy", {})
        current_min_weaknesses = int(self.state.get("current_min_weaknesses") or 0)
        if current_min_weaknesses == 0 and len(parsed.weaknesses) == 0 and policy.get("allow_zero_weakness_termination", True):
            self.state.setdefault("reviews", []).append(review_record)
            self.state["status"] = "terminated"
            export_record = export_package(self.package_root, self.state)
            self.state.setdefault("exports", []).append(export_record)
            save_state(self.package_root, self.state)
            return {"accepted": True, "terminated": True, "export": export_record, "validation": validation}

        self.state["status"] = "running_boost_round"
        save_state(self.package_root, self.state)
        previous_outputs = Path(str(current["outputs"]))
        try:
            metadata = run_executor_round(self.spec, self.state, parsed.weaknesses, previous_outputs)
        except Exception as exc:
            self.state["status"] = "executor_failed"
            self.state["last_error"] = str(exc)
            save_state(self.package_root, self.state)
            raise
        self.state.setdefault("reviews", []).append(review_record)
        self.state["rounds"].append(metadata)
        self.state["current_round"] = metadata["round_index"]
        self.state["latest_deliverable_round"] = metadata["round_id"]
        decrement = int(policy.get("weakness_decrement_per_round", 1))
        self.state["current_min_weaknesses"] = max(0, current_min_weaknesses - decrement)
        self.state["next_review_index"] = index + 1
        self.state["status"] = "awaiting_review"
        self.state["last_error"] = None
        save_state(self.package_root, self.state)
        return {"accepted": True, "terminated": False, "round": metadata, "validation": validation}

    def export(self, force: bool = False) -> Dict[str, Any]:
        if self.state.get("status") != "terminated" and not force:
            raise StarBoostError(
                "Task is not terminated yet. Submit a zero-weakness terminal review first, "
                "or run export with --force to create a non-terminal snapshot."
            )
        record = export_package(self.package_root, self.state)
        self.state.setdefault("exports", []).append(record)
        save_state(self.package_root, self.state)
        return record
