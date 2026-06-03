"""Blocking Toggl API v9 client.

Every call performs a synchronous HTTP request and must therefore run off the
UI thread — see :mod:`toggl.workers`.
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

API_BASE = "https://api.track.toggl.com/api/v9"
CREATED_WITH = "toggl-wrapper-native"
_TIMEOUT = 30


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class TogglClient:
    """Thin Toggl API v9 client. All calls are blocking."""

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.auth = (token, "api_token")
        self.session.headers["Content-Type"] = "application/json"

    def _get(self, path: str):
        res = self.session.get(f"{API_BASE}{path}", timeout=_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def me(self) -> dict:
        return self._get("/me")

    def projects(self, workspace_id: int) -> list[dict]:
        return self._get(f"/workspaces/{workspace_id}/projects")

    def current_entry(self) -> dict | None:
        """The running entry, or ``None`` when nothing is running."""
        return self._get("/me/time_entries/current")

    def start(self, workspace_id: int, project_id: int, description: str = "") -> dict:
        body = {
            "duration": -1,
            "wid": workspace_id,
            "description": description,
            "created_with": CREATED_WITH,
            "start": _utc_now_iso(),
            "tag_ids": [],
            "project_id": project_id,
        }
        res = self.session.post(
            f"{API_BASE}/workspaces/{workspace_id}/time_entries",
            json=body,
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()

    def stop(self, workspace_id: int, entry_id: int) -> dict:
        res = self.session.patch(
            f"{API_BASE}/workspaces/{workspace_id}/time_entries/{entry_id}/stop",
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()
