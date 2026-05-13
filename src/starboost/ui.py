from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


WIDTH = 84


def _clip(text: Any, width: int) -> str:
    value = "" if text is None else str(text)
    value = value.replace("\n", " ")
    if len(value) <= width:
        return value
    return value[: max(0, width - 3)] + "..."


def _line(content: str = "") -> str:
    return "| " + _clip(content, WIDTH - 4).ljust(WIDTH - 4) + " |"


def _rule() -> str:
    return "+" + "-" * (WIDTH - 2) + "+"


def panel(title: str, rows: Iterable[str]) -> str:
    body: List[str] = [_rule(), _line(title), _rule()]
    body.extend(_line(row) for row in rows)
    body.append(_rule())
    return "\n".join(body)


def kv(label: str, value: Any) -> str:
    return f"{label.ljust(18)} {value}"


def next_action(status: Optional[Dict[str, Any]]) -> str:
    if not status:
        return "Run `load_task <path>` to start."
    state = status.get("status")
    if state == "awaiting_review":
        return "Run `review`, edit the review file, then run `submit`."
    if state == "terminated":
        return "Run `export` if you want a fresh archive."
    if state == "executor_failed":
        return "Fix the executor issue, then rerun the last command."
    if state and str(state).startswith("running"):
        return "Wait for the current run to finish."
    return "Run `status` to inspect the task."


def render_home(record: Optional[Dict[str, Any]], status: Optional[Dict[str, Any]]) -> str:
    task = record.get("display_name") if record else "No task loaded"
    rows = [
        kv("Current task", task),
        kv("Status", status.get("status") if status else "none"),
        "",
        "Common commands:",
        "  load_task <path>     load or resume a task package",
        "  review               create/open the review file",
        "  submit               submit review and continue",
        "  status               show current task metadata",
        "  home                 show this dashboard",
        "  exit                 leave StarBoost",
        "",
        kv("Next", next_action(status)),
    ]
    return panel("StarBoost workspace", rows)


def render_status(status: Dict[str, Any], package_path: Optional[Path] = None, title: str = "Task dashboard") -> str:
    rows = [
        kv("Task", status.get("package_id")),
        kv("Status", status.get("status")),
        kv("Rounds", status.get("round_count")),
        kv("Reviews", status.get("review_count")),
        kv("Latest round", status.get("latest_round") or "none"),
        kv("Min strengths", status.get("current_min_strengths")),
        kv("Min weaknesses", status.get("current_min_weaknesses")),
    ]
    if package_path:
        rows.append(kv("Package", package_path))
    if status.get("latest_outputs"):
        rows.append(kv("Outputs", status.get("latest_outputs")))
    if status.get("last_error"):
        rows.append(kv("Last error", status.get("last_error")))
    exports = status.get("exports") or []
    if exports:
        rows.append(kv("Latest export", exports[-1].get("path")))
    rows.extend(["", kv("Next", next_action(status))])
    return panel(title, rows)


def render_review(info: Dict[str, Any]) -> str:
    return panel(
        "Review workspace",
        [
            kv("Review file", info.get("review_path")),
            kv("Deliverables", info.get("deliverables_path")),
            "",
            "Edit the review file, then run `submit`.",
        ],
    )


def render_submit(result: Dict[str, Any]) -> str:
    validation = result.get("validation") or {}
    rows = [
        kv("Accepted", result.get("accepted")),
        kv("Terminated", result.get("terminated", False)),
    ]
    errors = validation.get("errors") or []
    warnings = validation.get("warnings") or []
    if errors:
        rows.append(kv("Errors", "; ".join(errors)))
    if warnings:
        rows.append(kv("Warnings", "; ".join(warnings)))
    if result.get("round"):
        round_info = result["round"]
        rows.append(kv("New round", round_info.get("round_id")))
        rows.append(kv("Outputs", round_info.get("outputs")))
    if result.get("export"):
        rows.append(kv("Export", result["export"].get("path")))
    if result.get("review_path"):
        rows.append(kv("Review file", result.get("review_path")))
    rows.extend(["", kv("Next", "Run `review` for the new output." if result.get("accepted") and not result.get("terminated") else "Fix the review file and run `submit` again." if not result.get("accepted") else "The loop is complete.")])
    return panel("Submit result", rows)


def render_validation(result: Dict[str, Any]) -> str:
    rows = [
        kv("Task", result.get("task_id")),
        kv("Valid", result.get("valid")),
    ]
    errors = result.get("errors") or []
    if errors:
        rows.append(kv("Errors", "; ".join(errors)))
    return panel("Validation", rows)


def render_export(result: Dict[str, Any]) -> str:
    return panel("Export", [kv("Path", result.get("path")), kv("Bytes", result.get("bytes"))])


def render_message(title: str, *lines: Any) -> str:
    return panel(title, [str(line) for line in lines])
