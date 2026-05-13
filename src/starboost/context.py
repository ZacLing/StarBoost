from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .task_package import TaskPackageError, load_task_spec
from .util import ensure_dir, read_json, utc_now, write_json


CONTEXT_DIR = ".starboost"
CURRENT_TASK_FILE = "current_task.json"


class CurrentTaskError(RuntimeError):
    pass


def context_dir() -> Path:
    return Path.home() / CONTEXT_DIR


def current_task_path() -> Path:
    return context_dir() / CURRENT_TASK_FILE


def _display_name(package_path: Path) -> str:
    try:
        return load_task_spec(package_path).task_id
    except Exception:
        return package_path.name


def set_current_task(package_path: Path) -> Dict[str, Any]:
    resolved = package_path.expanduser().resolve()
    record = {
        "package_path": str(resolved),
        "display_name": _display_name(resolved),
        "set_at": utc_now(),
    }
    ensure_dir(context_dir())
    write_json(current_task_path(), record)
    return record


def get_current_task_record() -> Optional[Dict[str, Any]]:
    path = current_task_path()
    if not path.exists():
        return None
    try:
        record = read_json(path)
    except Exception:
        return None
    if not isinstance(record, dict) or not record.get("package_path"):
        return None
    return record


def get_current_task_path() -> Optional[Path]:
    record = get_current_task_record()
    if not record:
        return None
    path = Path(str(record["package_path"])).expanduser()
    if path.exists():
        return path.resolve()
    return None


def clear_current_task() -> None:
    path = current_task_path()
    if path.exists():
        path.unlink()


def discover_package_from_cwd(start: Optional[Path] = None) -> Optional[Path]:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "original_task" / "task.json").exists() or (candidate / "task.json").exists():
            try:
                load_task_spec(candidate)
                return candidate
            except TaskPackageError:
                continue
        if (candidate / "starboost.json").exists():
            try:
                load_task_spec(candidate)
                return candidate
            except TaskPackageError:
                continue
    return None


def resolve_package_path(package_arg: Optional[str], *, allow_discovery: bool = True) -> Path:
    if package_arg:
        path = Path(package_arg).expanduser()
        if not path.exists() and path.parts and path.parts[0] == Path.cwd().name:
            without_cwd_name = Path(*path.parts[1:]) if len(path.parts) > 1 else Path(".")
            if without_cwd_name.exists():
                return without_cwd_name.resolve()
        return path.resolve()
    current = get_current_task_path()
    if current:
        return current
    if allow_discovery:
        discovered = discover_package_from_cwd()
        if discovered:
            return discovered
    raise CurrentTaskError("No current task. Run `load_task <path>` first, or pass a package path explicitly.")
