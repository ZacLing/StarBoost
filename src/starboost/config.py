from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


DEFAULT_REVIEW_POLICY = {
    "min_strengths": 3,
    "initial_min_weaknesses": 5,
    "weakness_decrement_per_round": 1,
    "allow_zero_weakness_termination": True,
}

DEFAULT_EXECUTOR = {
    "backend": "docker",
    "model": "gpt-5.5",
    "codex_bin": "codex",
    "docker_bin": "docker",
    "docker_image": "starboost-codex:latest",
    "auth_mode": "copy-auth",
    "timeout_seconds": 7200,
}

DEFAULT_RUNTIME = {
    "open_files_after_review_start": True,
}


@dataclass
class RuntimeOverrides:
    executor_backend: Optional[str] = None
    executor_model: Optional[str] = None
    codex_bin: Optional[str] = None
    docker_bin: Optional[str] = None
    docker_image: Optional[str] = None
    timeout_seconds: Optional[int] = None
    auth_mode: Optional[str] = None
    no_open: bool = False


def deep_merge(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def default_config() -> Dict[str, Any]:
    return {
        "review_policy": dict(DEFAULT_REVIEW_POLICY),
        "executor": dict(DEFAULT_EXECUTOR),
        "runtime": dict(DEFAULT_RUNTIME),
    }


def apply_overrides(config: Dict[str, Any], overrides: RuntimeOverrides) -> Dict[str, Any]:
    cfg = deep_merge(default_config(), config)
    executor = cfg.setdefault("executor", {})
    runtime = cfg.setdefault("runtime", {})
    if overrides.executor_backend:
        executor["backend"] = overrides.executor_backend
    if overrides.executor_model:
        executor["model"] = overrides.executor_model
    if overrides.codex_bin:
        executor["codex_bin"] = overrides.codex_bin
    if overrides.docker_bin:
        executor["docker_bin"] = overrides.docker_bin
    if overrides.docker_image:
        executor["docker_image"] = overrides.docker_image
    if overrides.timeout_seconds is not None:
        executor["timeout_seconds"] = overrides.timeout_seconds
    if overrides.auth_mode:
        executor["auth_mode"] = overrides.auth_mode
    if overrides.no_open:
        runtime["open_files_after_review_start"] = False
    return cfg
