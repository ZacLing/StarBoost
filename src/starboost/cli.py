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
from .context import (
    CurrentTaskError,
    clear_current_task,
    get_current_task_record,
    resolve_package_path,
    set_current_task,
)
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


def _compact_status(status: dict[str, Any]) -> str:
    return (
        f"{status.get('package_id')} | {status.get('status')} | "
        f"rounds={status.get('round_count')} reviews={status.get('review_count')} | "
        f"min weaknesses={status.get('current_min_weaknesses')}"
    )


def _maybe_open(path: str, no_open: bool) -> None:
    if no_open:
        return
    try:
        subprocess.run(["open", path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return


def _package_arg(args: argparse.Namespace) -> Optional[str]:
    return getattr(args, "package", None)


def _session(args: argparse.Namespace) -> StarBoostSession:
    package = resolve_package_path(_package_arg(args))
    return StarBoostSession(package, _overrides(args))


def cmd_validate(args: argparse.Namespace) -> int:
    result = _session(args).validate()
    _print_json(result)
    return 0 if result["valid"] else 2


def cmd_load_task(args: argparse.Namespace) -> int:
    package = resolve_package_path(_package_arg(args), allow_discovery=False)
    session = StarBoostSession(package, _overrides(args))
    result = session.load_task()
    set_current_task(package)
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
    review_path = Path(args.review_path) if getattr(args, "review_path", None) else None
    result = _session(args).submit_review(review_path)
    _print_json(result)
    return 0 if result.get("accepted") else 2


def cmd_export(args: argparse.Namespace) -> int:
    _print_json(_session(args).export())
    return 0


def cmd_current(args: argparse.Namespace) -> int:
    record = get_current_task_record()
    if not record:
        print("No current task. Run `starboost load_task <path>` first.")
        return 1
    _print_json(record)
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    clear_current_task()
    print("Current task cleared.")
    return 0


class StarBoostShell(cmd.Cmd):
    intro = (
        "\n"
        "StarBoost\n"
        "Expert review workspace for AI deliverables.\n\n"
        "Common commands:\n"
        "  load_task <path>     load or resume a task package\n"
        "  review               open a review template for the current task\n"
        "  submit               submit the current review and continue\n"
        "  status               show task status\n"
        "  current              show the current task\n"
        "  clear                clear the current task\n"
        "  exit                 leave StarBoost\n"
    )

    def __init__(self) -> None:
        super().__init__()
        self._refresh_prompt()

    def _current_label(self) -> str:
        record = get_current_task_record()
        if not record:
            return "no task"
        return str(record.get("display_name") or Path(str(record.get("package_path"))).name)

    def _refresh_prompt(self) -> None:
        self.prompt = f"starboost [{self._current_label()}]> "

    def _parser(self, prog: str, package_optional: bool = True) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=prog)
        if package_optional:
            parser.add_argument("package", nargs="?")
        else:
            parser.add_argument("package")
        _add_runtime_options(parser)
        return parser

    def _run(
        self,
        argv: str,
        handler: Callable[[argparse.Namespace], int],
        *,
        prog: str,
        package_optional: bool = True,
        add_submit_options: bool = False,
    ) -> None:
        try:
            parts = shlex.split(argv)
            parser = self._parser(prog, package_optional=package_optional)
            if add_submit_options:
                parser.add_argument("--review-path", default=None)
            args = parser.parse_args(parts)
            code = handler(args)
            if code == 0:
                self._refresh_prompt()
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001 - shell should stay alive.
            print(f"error: {exc}")

    def do_load_task(self, arg: str) -> None:
        self._run(arg, cmd_load_task, prog="load_task", package_optional=False)

    def do_load(self, arg: str) -> None:
        self.do_load_task(arg)

    def do_validate(self, arg: str) -> None:
        self._run(arg, cmd_validate, prog="validate")

    def do_status(self, arg: str) -> None:
        self._run(arg, cmd_status, prog="status")

    def do_review(self, arg: str) -> None:
        self._run(arg, cmd_review, prog="review")

    def do_submit(self, arg: str) -> None:
        self._run(arg, cmd_submit, prog="submit", add_submit_options=True)

    def do_export(self, arg: str) -> None:
        self._run(arg, cmd_export, prog="export")

    def do_current(self, arg: str) -> None:
        cmd_current(argparse.Namespace())
        self._refresh_prompt()

    def do_clear(self, arg: str) -> None:
        cmd_clear(argparse.Namespace())
        self._refresh_prompt()

    def do_help(self, arg: str) -> None:
        print(
            "Commands:\n"
            "  load_task <path> [options]   load/resume a task and make it current\n"
            "  load <path> [options]        alias for load_task\n"
            "  review [path] [options]      create/open review for current or explicit task\n"
            "  submit [path] [options]      submit review for current or explicit task\n"
            "  status [path]                show status\n"
            "  validate [path]              validate current or explicit task\n"
            "  export [path]                export current or explicit task\n"
            "  current                      show current task\n"
            "  clear                        clear current task\n"
            "  exit                         leave StarBoost\n"
        )

    def emptyline(self) -> None:
        self.do_status("")

    def do_exit(self, arg: str) -> bool:
        return True

    def do_quit(self, arg: str) -> bool:
        return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="starboost")
    sub = parser.add_subparsers(dest="command")

    task_commands = {
        "validate": cmd_validate,
        "load_task": cmd_load_task,
        "status": cmd_status,
        "review": cmd_review,
        "submit": cmd_submit,
        "export": cmd_export,
    }
    for name, handler in task_commands.items():
        p = sub.add_parser(name)
        if name == "load_task":
            p.add_argument("package")
        else:
            p.add_argument("package", nargs="?")
        if name == "submit":
            p.add_argument("--review-path", default=None)
        _add_runtime_options(p)
        p.set_defaults(handler=handler)

    sub.add_parser("current").set_defaults(handler=cmd_current)
    sub.add_parser("clear").set_defaults(handler=cmd_clear)
    sub.add_parser("shell").set_defaults(handler=lambda args: StarBoostShell().cmdloop() or 0)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        return int(StarBoostShell().cmdloop() or 0)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        return int(StarBoostShell().cmdloop() or 0)
    try:
        return int(args.handler(args) or 0)
    except (TaskPackageError, StarBoostError, CurrentTaskError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

