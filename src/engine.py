"""
src/engine.py — The audit orchestrator.

Coordinates the Moodle client, checks, and reporters.
Follows Dependency Injection: all collaborators are passed in.
"""

from __future__ import annotations

import os
import time
from datetime import datetime

from src.checks import CourseCheck
from src.models import AuditConfig, CourseAuditResult
from src.moodle_client import MoodleClient
from src.reporters import Reporter


class AuditEngine:
    """Runs QA checks across all courses and delegates reporting."""

    def __init__(
        self,
        client: MoodleClient,
        audit_config: AuditConfig,
        checks: list[CourseCheck],
        reporters: list[Reporter],
        output_dir: str = "moodle_qa_reports",
    ):
        self._client = client
        self._config = audit_config
        self._checks = checks
        self._reporters = reporters
        self._output_dir = output_dir

    # ── public entry point ────────────────────
    def run(self) -> list[CourseAuditResult]:
        """Execute the full instance-wide audit."""
        os.makedirs(self._output_dir, exist_ok=True)

        self._print_header()
        courses = self._client.get_filtered_courses(self._config)
        print(f"  Found {len(courses)} courses to audit\n")

        if not courses:
            print("  No courses found. Check token permissions and filters.")
            return []

        results: list[CourseAuditResult] = []
        for i, course in enumerate(courses, 1):
            result = self._audit_single_course(course, i, len(courses))
            results.append(result)

            if i < len(courses):
                time.sleep(self._config.delay_between_courses)

        # Generate all reports
        for reporter in self._reporters:
            reporter.generate(results, self._output_dir)

        return results

    # ── private ───────────────────────────────
    def _audit_single_course(self, course: dict, index: int, total: int) -> CourseAuditResult:
        course_id = course["id"]
        course_name = course.get("fullname", f"Course {course_id}")
        print(f"  [{index}/{total}] Auditing: {course_name} (ID: {course_id})")

        result = CourseAuditResult(course_id=course_id, course_name=course_name)

        try:
            sections = self._client.get_course_contents(course_id)

            # Also include course summary as a virtual section/module if it has content
            # This allows checking links/HTML in course descriptions
            course_summary = course.get("summary", "")
            if course_summary and course_summary.strip():
                summary_module = {
                    "id": 0,
                    "name": "Course Summary",
                    "modname": "label",  # Treat as label for HTML content
                    "description": course_summary,  # Use 'description' field (checks look for this)
                    "descriptionformat": course.get("summaryformat", 1),
                }
                # Add as first section/module
                if sections:
                    if "modules" not in sections[0]:
                        sections[0]["modules"] = []
                    sections[0]["modules"].insert(0, summary_module)
                else:
                    # Create a virtual section if course has no sections
                    sections = [{
                        "id": 0,
                        "name": "Course Information",
                        "modules": [summary_module]
                    }]

        except Exception as exc:
            result.skipped = True
            result.error = str(exc)
            print(f"    ⚠ SKIPPED: {exc}")
            return result

        result.sections = len(sections)
        result.modules = sum(len(s.get("modules", [])) for s in sections)

        # Run every registered check and map results to the correct field
        check_field_map = {
            "Broken Links": "broken_links",
            "Content & File Types": "file_types",
            "File Sizes": "file_sizes",
            "Authenticated Access": "auth_access",
            "Content Layering / Depth": "content_depth",
            "Accessibility & Captions": "accessibility",
            "Malicious Code Detection": "malicious_code",
            "Mobile-Ready Content": "mobile_ready",
        }

        for check in self._checks:
            field = check_field_map.get(check.name)
            if field:
                setattr(result, field, check.run(sections))

        print(f"    ✓ Done — {result.modules} modules, {result.total_issues} issue(s)")
        return result

    def _print_header(self):
        print("=" * 70)
        print("  MOODLE INSTANCE-WIDE QA AUDIT")
        print(f"  Instance: {self._client.base_url}")
        print(f"  Started:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
