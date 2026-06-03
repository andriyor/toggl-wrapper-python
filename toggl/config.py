"""Token resolution for the native Toggl timer."""

from __future__ import annotations

import os
from pathlib import Path

# Repo-root ``.env`` (../.. from this file): native/toggl/config.py -> repo root.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
_ENV_KEY = "TOGGL_TOKEN"


def load_token() -> str:
    """Resolve the Toggl API token.

    Order: ``TOGGL_TOKEN`` env var, then ``TOGGL_TOKEN`` from the
    project-root ``.env``.

    Raises:
        SystemExit: if no token can be found in any location.
    """
    token = os.environ.get(_ENV_KEY)
    if token:
        return token.strip()

    token = _token_from_env_file(_ENV_PATH)
    if token:
        return token

    raise SystemExit(
        "No Toggl token found. Set TOGGL_API_TOKEN or add TOGGL_API_TOKEN=... to .env"
    )


def _token_from_env_file(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{_ENV_KEY}="):
            return line.split("=", 1)[1].strip().strip("\"'")
    return None
