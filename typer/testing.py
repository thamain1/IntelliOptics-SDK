"""Testing helpers for the lightweight :mod:`typer` shim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import io
import sys

from . import Exit


@dataclass
class Result:
    """Container for the outcome of a CLI invocation."""

    exit_code: int
    stdout: str
    stderr: str
    exception: Exception | None = None


class CliRunner:
    """Execute CLI commands while capturing output for assertions."""

    def invoke(self, app: object, args: Optional[Iterable[str]] = None) -> Result:
        argv = list(args or [])
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        exit_code = 0
        exc: Exception | None = None

        try:
            sys.stdout, sys.stderr = stdout, stderr
            if not hasattr(app, "_invoke"):
                raise TypeError("App must provide an _invoke() method")

            exit_code = app._invoke(argv)
        except Exit as exit_exc:
            exit_code = exit_exc.exit_code
        except Exception as err:  # pragma: no cover - defensive
            exc = err
            exit_code = 1
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        return Result(exit_code=exit_code, stdout=stdout.getvalue(), stderr=stderr.getvalue(), exception=exc)

