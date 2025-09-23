from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intellioptics.client import IntelliOptics


def test_init_uses_environment_defaults(monkeypatch):
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "env-token")

    client = IntelliOptics()

    assert client._http.base == "https://example.invalid"
    assert client._http.headers["Authorization"] == "Bearer env-token"
