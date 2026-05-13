from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .task_package import TaskSpec
from .trace import summarize_events
from .util import artifact_manifest, copy_path, ensure_dir, remove_if_exists, utc_now, write_json, write_text


class ExecutorError(RuntimeError):
    pass


def _round_id(index: int) -> str:
    if index == 0:
        return "v000_cold_start"
    return f"v{index:03d}_boosted"


def _append_runtime_guidance(prompt: str, boosted: bool) -> str:
    common = """

---

StarBoost runtime note:
- You are working inside a clean workspace.
- Task files are available under `./inputs/`.
- Additional visible files, if any, are under `./inputs/materials/`.
- Write the complete final deliverable package under `./outputs/`.
- Do not write outside this workspace.
"""
    if not boosted:
        return prompt.rstrip() + common
    boost = """
- Previous deliverables are available under `./inputs/previous_deliverables/`.
- The latest human expert weaknesses are available in `./inputs/review_weaknesses.md`.
- Produce a complete replacement deliverable package in `./outputs/`, not a patch file.
"""
    return prompt.rstrip() + common + boost


def _prepare_workspace(
    spec: TaskSpec,
    round_root: Path,
    boosted: bool,
    previous_outputs: Optional[Path],
    weaknesses: Optional[List[str]],
) -> Dict[str, Path]:
    workspace = round_root / "workspace"
    inputs = workspace / "inputs"
    outputs = workspace / "outputs"
    logs = round_root / "logs"
    codex_home = round_root / "codex_home"
    for path in (workspace, inputs, outputs, logs, codex_home):
        ensure_dir(path)

    raw_prompt = spec.prompt_path.read_text(encoding="utf-8")
    write_text(inputs / "prompt.md", _append_runtime_guidance(raw_prompt, boosted))
    for visible in spec.visible_inputs:
        copy_path(visible.source, inputs / visible.destination)
    if boosted:
        if previous_outputs and previous_outputs.exists():
            copy_path(previous_outputs, inputs / "previous_deliverables")
        weakness_text = "\n".join(f"- {item}" for item in (weaknesses or []))
        write_text(inputs / "review_weaknesses.md", "# Latest Expert Weaknesses\n\n" + weakness_text + "\n")
    return {"workspace": workspace, "inputs": inputs, "outputs": outputs, "logs": logs, "codex_home": codex_home}


def _codex_exec_args(config: Dict[str, Any], final_path: str, allow_web_search: bool, sandbox: str) -> List[str]:
    args: List[str] = []
    if allow_web_search:
        args.append("--search")
    args.extend(
        [
            "exec",
            "--json",
            "--ephemeral",
            "--output-last-message",
            final_path,
            "--sandbox",
            sandbox,
            "--skip-git-repo-check",
            "--ignore-rules",
            "--disable",
            "plugins",
            "--disable",
            "memories",
            "-c",
            'approval_policy="never"',
            "-c",
            'model_reasoning_summary="detailed"',
            "-c",
            "show_raw_agent_reasoning=true",
        ]
    )
    model = config.get("model")
    if model:
        args.extend(["-m", str(model)])
    args.append("-")
    return args


def _prepare_auth_home(codex_home: Path, auth_mode: str, isolated: bool) -> Dict[str, str]:
    env = os.environ.copy()
    if auth_mode == "global" and not isolated:
        return env
    codex_home.mkdir(parents=True, exist_ok=True)
    env["CODEX_HOME"] = str(codex_home)
    if auth_mode in {"copy-auth", "global"}:
        source = Path.home() / ".codex" / "auth.json"
        if source.exists():
            shutil.copy2(source, codex_home / "auth.json")
    elif auth_mode != "env":
        raise ExecutorError(f"Unknown auth mode: {auth_mode}")
    return env


def _docker_command(config: Dict[str, Any], paths: Dict[str, Path], allow_web_search: bool, auth_env: Dict[str, str], docker_auth_home: Path) -> List[str]:
    docker = str(config.get("docker_bin") or "docker")
    image = str(os.environ.get("STARBOOST_DOCKER_IMAGE") or config.get("docker_image") or "starboost-codex:latest")
    env_args: List[str] = []
    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY"):
        if auth_env.get(key):
            env_args.extend(["-e", key])
    codex_args = _codex_exec_args(config, "/workspace/final.md", allow_web_search, "danger-full-access")
    return [
        docker,
        "run",
        "--rm",
        "-i",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "512",
        "--memory",
        str(config.get("memory") or "6g"),
        "--cpus",
        str(config.get("cpus") or "4"),
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=1g",
        "--mount",
        f"type=bind,src={paths['workspace']},dst=/workspace",
        "--mount",
        f"type=bind,src={docker_auth_home},dst=/codex-home",
        "-w",
        "/workspace",
        "-e",
        "CODEX_HOME=/codex-home",
        "-e",
        "HOME=/codex-home",
        *env_args,
        image,
        str(config.get("codex_bin") or "codex"),
        *codex_args,
    ]


def _local_command(config: Dict[str, Any], paths: Dict[str, Path], allow_web_search: bool) -> List[str]:
    codex_bin = str(config.get("codex_bin") or "codex")
    sandbox = str(config.get("local_sandbox") or "workspace-write")
    return [codex_bin, *_codex_exec_args(config, str(paths["workspace"] / "final.md"), allow_web_search, sandbox)]


def run_executor_round(
    spec: TaskSpec,
    state: Dict[str, Any],
    weaknesses: Optional[List[str]] = None,
    previous_outputs: Optional[Path] = None,
) -> Dict[str, Any]:
    round_index = len(state.get("rounds", []))
    round_id = _round_id(round_index)
    round_root = spec.package_root / "boost_runs" / "rounds" / round_id
    if round_root.exists():
        raise ExecutorError(f"Round directory already exists: {round_root}")
    paths = _prepare_workspace(spec, round_root, round_index > 0, previous_outputs, weaknesses)
    config = state["config"]["executor"]
    backend = str(config.get("backend") or "docker")
    auth_mode = str(config.get("auth_mode") or "copy-auth")
    if backend == "docker":
        docker_auth_home = paths["codex_home"] / "docker"
        auth_env = _prepare_auth_home(docker_auth_home, auth_mode, isolated=True)
        command = _docker_command(config, paths, spec.allow_web_search, auth_env, docker_auth_home)
    else:
        auth_env = _prepare_auth_home(paths["codex_home"] / "local", auth_mode, isolated=False)
        command = _local_command(config, paths, spec.allow_web_search)

    prompt = (paths["inputs"] / "prompt.md").read_text(encoding="utf-8")
    events_path = paths["logs"] / "events.jsonl"
    stderr_path = paths["logs"] / "stderr.log"
    started = time.monotonic()
    started_at = utc_now()
    exit_code: Optional[int] = None
    timed_out = False
    with events_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
        try:
            proc = subprocess.run(
                command,
                input=prompt.encode("utf-8"),
                stdout=stdout_handle,
                stderr=stderr_handle,
                cwd=str(paths["workspace"] if backend != "docker" else spec.package_root),
                env=auth_env,
                timeout=int(config.get("timeout_seconds") or 7200),
                check=False,
            )
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = -9
    duration = time.monotonic() - started
    ended_at = utc_now()
    final_in_workspace = paths["workspace"] / "final.md"
    if final_in_workspace.exists():
        shutil.copy2(final_in_workspace, paths["logs"] / "final.md")
    else:
        write_text(paths["logs"] / "final.md", "")

    trace_summary = summarize_events(events_path, paths["logs"] / "trace_summary.json")
    manifest = artifact_manifest(paths["outputs"])
    write_json(paths["logs"] / "artifact_manifest.json", manifest)
    metadata = {
        "round_id": round_id,
        "round_index": round_index,
        "stage": "cold_start" if round_index == 0 else "boosted",
        "backend": backend,
        "model": config.get("model"),
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "command": command,
        "workspace": str(paths["workspace"]),
        "outputs": str(paths["outputs"]),
        "logs": str(paths["logs"]),
        "artifact_manifest": manifest,
        "trace_summary": trace_summary,
    }
    write_json(round_root / "manifest.json", metadata)
    if exit_code != 0:
        raise ExecutorError(f"Executor round {round_id} failed with exit code {exit_code}")
    return metadata
