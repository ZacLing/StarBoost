from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict

from .util import ensure_dir, utc_now


EXCLUDED_PARTS = {".git", "__pycache__", "codex_home", ".pytest_cache"}


def _should_include(path: Path, package_root: Path) -> bool:
    rel_parts = path.relative_to(package_root).parts
    if any(part in EXCLUDED_PARTS for part in rel_parts):
        return False
    if rel_parts and rel_parts[0] == "exports":
        return False
    return True


def export_package(package_root: Path, state: Dict[str, Any]) -> Dict[str, Any]:
    exports_dir = ensure_dir(package_root / "exports")
    timestamp = utc_now().replace(":", "").replace("-", "")
    base_name = f"{state.get('package_id', package_root.name)}_starboost_{timestamp}"
    zip_path = exports_dir / f"{base_name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_root.rglob("*")):
            if path.is_file() and _should_include(path, package_root):
                archive.write(path, path.relative_to(package_root).as_posix())
    return {"created_at": utc_now(), "path": str(zip_path), "bytes": zip_path.stat().st_size}

