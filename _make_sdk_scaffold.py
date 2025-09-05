import os, textwrap, shutil
from pathlib import Path

root = Path.cwd()
pkg = root / "intellioptics"
(pkg).mkdir(exist_ok=True)
(root / "tests").mkdir(exist_ok=True)
(root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

# pyproject.toml
(root / "pyproject.toml").write_text(textwrap.dedent('''\
[project]
name = "intellioptics"
version = "0.24.2"
description = "IntelliOptics SDK & CLI"
readme = "README.md"
requires-python = ">=3.9,<4.0"
license = { text = "MIT" }
dependencies = [
  "pydantic>=2,<3",
  "requests>=2.28,<3",
  "typer>=0.12,<0.13",
  "python-dateutil>=2.9,<3",
  "pillow>=9",
]
[project.scripts]
intellioptics = "intellioptics.cli:app"
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
'''))

(root / "README.md").write_text("# IntelliOptics SDK & CLI\n")

# package init
(pkg / "__init__.py").write_text("from .client import IntelliOptics\n")

# (… all the other code for client.py, _http.py, _img.py, errors.py, models.py, cli.py …)
print("SDK scaffold created.")
