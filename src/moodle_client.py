"""
src/moodle_client.py — Thin wrapper around the Moodle Web Services REST API.

Single Responsibility: HTTP communication with Moodle.
"""

from typing import Any

import requests

from src.models import MoodleConfig, AuditConfig


class MoodleApiError(Exception):
    """Raised when the Moodle API returns an error response."""


class MoodleClient:
    """Handles all communication with the Moodle REST API."""

    def __init__(self, config: MoodleConfig):
        self._base_url = config.base_url.rstrip("/")
        self._token = config.token
        self._endpoint = f"{self._base_url}/webservice/rest/server.php"

    # ── generic call ──────────────────────────
    def call(self, function: str, **params: Any) -> Any:
        params.update({
            "wstoken": self._token,
            "wsfunction": function,
            "moodlewsrestformat": "json",
        })
        response = requests.get(self._endpoint, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "exception" in data:
            raise MoodleApiError(f"{function}: {data.get('message', data)}")
        return data

    # ── convenience methods ───────────────────
    def get_courses(self) -> list[dict]:
        return self.call("core_course_get_courses")

    def get_course_contents(self, course_id: int) -> list[dict]:
        return self.call("core_course_get_contents", courseid=course_id)

    def get_filtered_courses(self, audit_config: AuditConfig) -> list[dict]:
        """Return courses that match the audit filter criteria."""
        courses = self.get_courses()
        return [
            c for c in courses
            if c["id"] not in audit_config.exclude_course_ids
            and (not audit_config.only_visible_courses or c.get("visible", 1))
            and (audit_config.category_id is None or c.get("categoryid") == audit_config.category_id)
        ]

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def token(self) -> str:
        return self._token
