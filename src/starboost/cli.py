from __future__ import annotations

import argparse
import cmd
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from .config import RuntimeOverrides
from .service import StarBoostError, StarBoostSession
from .task_package import TaskPackageError


def _add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--executor-backend", choices=["docker", "local"], default=None)
    parser.add_argument("--executor-model", default=None)
    parser.add_argument("--codex-bin", default=None)
    parser.add_argument("--docker-bin", default=None)
    parser.add_argument("--docker-image", default=None)
    parser.add_argument("--auth-mode", choices=["copy-auth", "env", "global"], default=None)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--no-open", action="store_true")


def _overrides(args: argparse.Namespace) -> RuntimeOverrides:
    return RuntimeOverrides(
        executor_backend=getattr(args, "executor_backend", None),
        executor_model=getattr(args, "executor_model", None),
        codex_bin=getattr(args, "codex_bin", None),
        docker_bin=getattr(args, "docker_bin", None),
        docker_image=getattr(args, "docker_image", None),
        timeout_seconds=getattr(args, "timeout_seconds", None),
        auth_mode=getattr(args, "auth_mode", None),
        no_open=bool(getattr(args, "no_open", False)),
    )


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _maybe_open(path: str, no_open: bool) -> None:
    if no_open:
        return
    try:
        subprocess.run(["open", path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return


def _session(args: argparse.Namespace) -> StarBoostSession:
    return StarBoostSession(Path(args.package), _overrides(args))


def cmd_validate(args: argparse.Namespace) -> int:
    result = _session(args).validate()
    _print_json(result)
    return 0 if result["valid"] else 2


def cmd_load_task(args: argparse.Namespace) -> int:
    result = _session(args).load_task()
    _print_json(result)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    _print_json(_session(args).status())
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    result = _session(args).start_review()
    _print_json(result)
    _maybe_open(result["review_path"], args.no_open)
    _maybe_open(result["deliverables_path"], args.no_open)
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    review_path = Path(args.review_path) if args.review_path else None
    result = _session(args).submit_review(review_path)
    _print_json(result)
    return 0 if result.get("accepted") else 2


def cmd_export(args: argparse.Namespace) -> int:
    _print_json(_session(args).export())
    return 0


class StarBoostShell(cmd.Cmd):
    intro = "StarBoost shell. Type help or ? for commands."
    prompt = "starboost> "

    def _run(self, argv: str, handler: Callable[[argparse.Namespace], int], needs_package: bool = True) -> None:
        try:
            parts = shlex.split(argv)
            parser = argparse.ArgumentParser(prog=handler.__name__)
            if needs_package:
                parser.add_argument("package")
            _add_runtime_options(parser)
            args = parser.parse_args(parts)
            handler(args)
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001 - shell should stay alive.
            print(f"error: {exc}")

    def do_load_task(self, arg: str) -> None:
        self._run(arg, cmd_load_task)

    def do_validate(self, arg: str) -> None:
        self._run(arg, cmd_validate)

    def do_status(self, arg: str) -> None:
        self._run(arg, cmd_status)

    def do_review(self, arg: str) -> None:
        self._run(arg, cmd_review)

    def do_submit(self, arg: str) -> None:
        self._run(arg, cmd_submit)

    def do_export(self, arg: str) -> None:
        self._run(arg, cmd_export)

    def do_exit(self, arg: str) -> bool:
        return True

    def do_quit(self, arg: str) -> bool:
        return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="starboost")
    sub = parser.add_subparsers(dest="command")

    commands = {
        "validate": cmd_validate,
        "load_task": cmd_load_task,
        "status": cmd_status,
        "review": cmd_review,
        "submit": cmd_submit,
        "export": cmd_export,
    }
    for name, handler in commands.items():
        p = sub.add_parser(name)
        p.add_argument("package")
        if name == "submit":
            p.add_argument("--review-path", default=None)
        _add_runtime_options(p)
        p.set_defaults(handler=handler)
    sub.add_parser("shell").set_defaults(handler=lambda args: StarBoostShell().cmdloop() or 0)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    try:
        return int(args.handler(args) or 0)
    except (TaskPackageError, StarBoostError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
