"""Lightweight subset of the :mod:`typer` API used by the tests.

This shim implements the minimal surface that the project relies on without
pulling in the third-party dependency. It purposefully mirrors the small
pieces of behaviour exercised by the CLI tests: registering commands, raising
``Exit`` with an ``exit_code`` attribute, and streaming output through
``echo``.

The goal is not to be feature complete, but to provide a stable drop-in
replacement that behaves similarly for the supported methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional

import sys

__all__ = ["Typer", "Exit", "echo"]


class Exit(Exception):
    """Exception used to signal an early exit from a command."""

    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.exit_code = code


def echo(message: Any, *, err: bool = False) -> None:
    """Write ``message`` followed by a newline to the desired stream."""

    stream = sys.stderr if err else sys.stdout
    text = message if isinstance(message, str) else str(message)
    stream.write(text + "\n")
    stream.flush()


CommandFn = Callable[..., Any]


class Typer:
    """Extremely small command registry compatible with the tests."""

    def __init__(self, *, add_completion: bool | None = None) -> None:  # pragma: no cover - signature parity
        self._commands: Dict[str, CommandFn] = {}

    def command(self, name: str | None = None) -> Callable[[CommandFn], CommandFn]:
        """Register ``func`` as a command under ``name`` (or its own name)."""

        def decorator(func: CommandFn) -> CommandFn:
            cmd_name = name or func.__name__.replace("_", "-")
            # Register both the CLI name (with hyphens) and the Python identifier
            # so that lookups succeed with either variant.
            self._commands[cmd_name] = func
            self._commands.setdefault(func.__name__, func)
            return func

        return decorator

    # ------------------------------------------------------------------
    # Invocation helpers
    # ------------------------------------------------------------------
    def _lookup(self, name: str) -> CommandFn:
        func = self._commands.get(name) or self._commands.get(name.replace("-", "_"))
        if func is None:
            raise Exit(code=1)
        return func

    def _invoke(self, argv: Iterable[str]) -> int:
        args = list(argv)
        if not args:
            raise Exit(code=0)

        command_name, *tail = args
        func = self._lookup(command_name)
        func(*tail)
        return 0

    def __call__(self, argv: Optional[Iterable[str]] = None) -> int:  # pragma: no cover - passthrough
        return self._invoke(argv or sys.argv[1:])


# Import at module load so ``typer.testing.CliRunner`` is available as
# ``from typer.testing import CliRunner``.
from . import testing  # noqa: E402  # isort:skip

CliRunner = testing.CliRunner  # re-export for convenience

