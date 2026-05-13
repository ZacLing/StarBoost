from __future__ import annotations

import argparse
import cmd
import json
import shlex
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Optional, TypeVar

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
from .ui import (
    render_export,
    render_home,
    render_message,
    render_review,
    render_status,
    render_submit,
    render_validation,
)


T = TypeVar("T")


@contextmanager
def _progress(message: str) -> Iterator[None]:
    print(message, file=sys.stderr, flush=True)
    if not sys.stderr.isatty():
        yield
        return

    stop = threading.Event()

    def animate() -> None:
        frames = "|/-\\"
        index = 0
        started = time.monotonic()
        while not stop.is_set():
            elapsed = int(time.monotonic() - started)
            frame = frames[index % len(frames)]
            sys.stderr.write(f"\r{frame} Working... {elapsed}s elapsed. Please wait.")
            sys.stderr.flush()
            index += 1
            stop.wait(0.2)
        sys.stderr.write("\r" + " " * 78 + "\r")
        sys.stderr.flush()

    thread = threading.Thread(target=animate, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1)


def _run_with_optional_progress(should_show: bool, message: str, operation: Callable[[], T]) -> T:
    if not should_show:
        return operation()
    with _progress(message):
        return operation()


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
    if no_open or not path or path == "None":
        return
    try:
        subprocess.run(["open", path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return


def _maybe_open_export_parent(result: dict[str, Any], no_open: bool) -> None:
    path = result.get("path")
    if not path:
        return
    _maybe_open(str(Path(str(path)).parent), no_open)


def _maybe_close_finder_window(path: Optional[str], no_open: bool) -> None:
    if no_open or not path or sys.platform != "darwin":
        return
    target = str(Path(path).expanduser().resolve())
    script = """
on normalizePath(rawPath)
    if rawPath ends with "/" then
        return text 1 thru -2 of rawPath
    end if
    return rawPath
end normalizePath

on run argv
    set wantedPath to my normalizePath(item 1 of argv)
    tell application "Finder"
        set winCount to count of windows
        repeat with i from winCount to 1 by -1
            try
                set finderWindow to window i
                set windowPath to my normalizePath(POSIX path of (target of finderWindow as alias))
                if windowPath is wantedPath then close finderWindow
            end try
        end repeat
    end tell
end run
"""
    try:
        subprocess.run(
            ["osascript", "-e", script, target],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
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
    result = _run_with_optional_progress(
        session.load_task_will_run_executor(),
        "No prior deliverable found. Executor agent is creating the cold-start deliverable; this can take a few minutes.",
        session.load_task,
    )
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
    session = _session(args)
    previous_outputs = session.status().get("latest_outputs")
    _maybe_close_finder_window(str(previous_outputs or ""), args.no_open)
    result = _run_with_optional_progress(
        session.submit_review_will_run_executor(review_path),
        "Review accepted for iteration. Executor agent is revising the deliverables from your comments; please wait a few minutes.",
        lambda: session.submit_review(review_path),
    )
    _print_json(result)
    if not result.get("accepted"):
        _maybe_open(str(result.get("review_path") or ""), args.no_open)
        _maybe_open(str(result.get("deliverables_path") or ""), args.no_open)
    return 0 if result.get("accepted") else 2


def cmd_export(args: argparse.Namespace) -> int:
    result = _session(args).export(force=bool(getattr(args, "force", False)))
    _print_json(result)
    _maybe_open_export_parent(result, args.no_open)
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
    def __init__(self) -> None:
        super().__init__()
        self.intro = self._home_panel()
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

    def _parse(
        self,
        argv: str,
        prog: str,
        package_optional: bool = True,
        add_submit_options: bool = False,
        add_export_options: bool = False,
    ) -> argparse.Namespace:
        parts = shlex.split(argv)
        parser = self._parser(prog, package_optional=package_optional)
        if add_submit_options:
            parser.add_argument("--review-path", default=None)
        if add_export_options:
            parser.add_argument("--force", action="store_true")
        return parser.parse_args(parts)

    def _session_for(self, args: argparse.Namespace) -> tuple[StarBoostSession, Path]:
        package = resolve_package_path(_package_arg(args))
        return StarBoostSession(package, _overrides(args)), package

    def _status_for_current(self) -> tuple[Optional[dict[str, Any]], Optional[Path]]:
        try:
            package = resolve_package_path(None, allow_discovery=False)
            session = StarBoostSession(package)
            return session.status(), package
        except Exception:
            return None, None

    def _home_panel(self) -> str:
        record = get_current_task_record()
        status, _ = self._status_for_current()
        return render_home(record, status)

    def _shell_error(self, exc: Exception) -> None:
        print(render_message("Error", str(exc)))

    def do_load_task(self, arg: str) -> None:
        try:
            args = self._parse(arg, "load_task", package_optional=False)
            package = resolve_package_path(_package_arg(args), allow_discovery=False)
            session = StarBoostSession(package, _overrides(args))
            status = _run_with_optional_progress(
                session.load_task_will_run_executor(),
                "No prior deliverable found. Executor agent is creating the cold-start deliverable; this can take a few minutes.",
                session.load_task,
            )
            set_current_task(package)
            print(render_status(status, package, title="Task loaded"))
            self._refresh_prompt()
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001 - shell should stay alive.
            self._shell_error(exc)

    def do_load(self, arg: str) -> None:
        self.do_load_task(arg)

    def do_validate(self, arg: str) -> None:
        try:
            args = self._parse(arg, "validate")
            session, _ = self._session_for(args)
            print(render_validation(session.validate()))
            self._refresh_prompt()
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001
            self._shell_error(exc)

    def do_status(self, arg: str) -> None:
        try:
            args = self._parse(arg, "status")
            session, package = self._session_for(args)
            print(render_status(session.status(), package))
            self._refresh_prompt()
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001
            self._shell_error(exc)

    def do_review(self, arg: str) -> None:
        try:
            args = self._parse(arg, "review")
            session, _ = self._session_for(args)
            result = session.start_review()
            print(render_review(result))
            _maybe_open(result["review_path"], args.no_open)
            _maybe_open(result["deliverables_path"], args.no_open)
            self._refresh_prompt()
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001
            self._shell_error(exc)

    def do_submit(self, arg: str) -> None:
        try:
            args = self._parse(arg, "submit", add_submit_options=True)
            session, _ = self._session_for(args)
            review_path = Path(args.review_path) if getattr(args, "review_path", None) else None
            previous_outputs = session.status().get("latest_outputs")
            _maybe_close_finder_window(str(previous_outputs or ""), args.no_open)
            result = _run_with_optional_progress(
                session.submit_review_will_run_executor(review_path),
                "Review accepted for iteration. Executor agent is revising the deliverables from your comments; please wait a few minutes.",
                lambda: session.submit_review(review_path),
            )
            print(render_submit(result))
            if not result.get("accepted"):
                _maybe_open(str(result.get("review_path") or ""), args.no_open)
                _maybe_open(str(result.get("deliverables_path") or ""), args.no_open)
            self._refresh_prompt()
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001
            self._shell_error(exc)

    def do_export(self, arg: str) -> None:
        try:
            args = self._parse(arg, "export", add_export_options=True)
            session, _ = self._session_for(args)
            result = session.export(force=bool(getattr(args, "force", False)))
            print(render_export(result))
            _maybe_open_export_parent(result, args.no_open)
            self._refresh_prompt()
        except SystemExit:
            return
        except Exception as exc:  # noqa: BLE001
            self._shell_error(exc)

    def do_current(self, arg: str) -> None:
        status, package = self._status_for_current()
        if status and package:
            print(render_status(status, package, title="Current task"))
        else:
            print(render_message("Current task", "No current task. Run `load_task <path>` first."))
        self._refresh_prompt()

    def do_clear(self, arg: str) -> None:
        clear_current_task()
        print(render_message("Current task", "Current task cleared."))
        self._refresh_prompt()

    def do_home(self, arg: str) -> None:
        print(self._home_panel())
        self._refresh_prompt()

    def do_dashboard(self, arg: str) -> None:
        self.do_home(arg)

    def do_help(self, arg: str) -> None:
        print(
            render_message(
                "Commands",
                "load_task <path> [options]   load/resume a task and make it current",
                "load <path> [options]        alias for load_task",
                "review [path] [options]      create/open review for current or explicit task",
                "submit [path] [options]      submit review for current or explicit task",
                "status [path]                show the task dashboard",
                "validate [path]              validate current or explicit task",
                "export [path] [--force]      export terminated task; --force makes a snapshot",
                "current                      show current task",
                "home                         show dashboard",
                "clear                        clear current task",
                "exit                         leave StarBoost",
            )
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
        if name == "export":
            p.add_argument("--force", action="store_true")
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
