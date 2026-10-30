"""
src/checks.py — Individual QA check implementations.

Each check is a class implementing the CourseCheck protocol (Strategy pattern).
Checks are stateless; all configuration is injected via the constructor.
"""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Protocol

import requests

from src import html_utils
from src.models import (
    AuditConfig,
    MediaFormats,
    MoodleConfig,
    BrokenLinkResults,
    LinkResult,
    FileTypeResults,
    FileSizeResults,
    FileInfo,
    AuthAccessResults,
    ContentDepthResults,
    DepthRecord,
    AccessibilityResults,
    AccessibilityIssue,
    MaliciousCodeResults,
    SuspiciousCodeFinding,
    MobileReadyResults,
    MobileIssue,
)


# ─────────────────────────────────────────────
# Protocol — every check must satisfy this
# ─────────────────────────────────────────────
class CourseCheck(Protocol):
    """Interface that all QA checks implement."""

    @property
    def name(self) -> str: ...

    def run(self, sections: list[dict]) -> object: ...


# ─────────────────────────────────────────────
# Helpers shared across checks
# ─────────────────────────────────────────────
def _file_extension(filename: str) -> str:
    return ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""


def _iter_modules(sections: list[dict]):
    """Yield (section_dict, module_dict) for every module in the course."""
    for section in sections:
        for module in section.get("modules", []):
            yield section, module


def _html_fields(module: dict) -> list[str]:
    """Return non-empty HTML content fields from a module."""
    return [module[f] for f in ("description", "content", "intro") if module.get(f)]


# ─────────────────────────────────────────────
# 1. Broken Links
# ─────────────────────────────────────────────
class BrokenLinkCheck:
    name = "Broken Links"

    def __init__(self, moodle_config: MoodleConfig, audit_config: AuditConfig):
        self._token = moodle_config.token
        self._timeout = audit_config.link_timeout_seconds
        self._delay = audit_config.delay_between_requests

    def run(self, sections: list[dict]) -> BrokenLinkResults:
        urls = self._collect_urls(sections)
        results = BrokenLinkResults()

        for url in urls:
            result = self._check_single_url(url)
            if result.status == "ok":
                results.ok_count += 1
            elif result.status == "broken":
                results.broken.append(result)
            elif result.status == "timeout":
                results.timeouts.append(result)
            else:
                results.errors.append(result)
            time.sleep(self._delay)

        return results

    # ── private ───────────────────────────────
    def _collect_urls(self, sections: list[dict]) -> set[str]:
        urls: set[str] = set()
        for _, module in _iter_modules(sections):
            if module.get("url"):
                urls.add(module["url"])
            for html in _html_fields(module):
                urls.update(html_utils.extract_urls(html))
            for content in module.get("contents", []):
                file_url = content.get("fileurl", "")
                if file_url:
                    if self._token not in file_url:
                        file_url += f"?token={self._token}"
                    urls.add(file_url)
        return urls

    def _check_single_url(self, url: str) -> LinkResult:
        try:
            resp = requests.head(url, timeout=self._timeout, allow_redirects=True)
            if resp.status_code < 400:
                return LinkResult(url=url, status="ok", status_code=resp.status_code)
            return LinkResult(url=url, status="broken", status_code=resp.status_code)
        except requests.Timeout:
            return LinkResult(url=url, status="timeout")
        except requests.RequestException as exc:
            return LinkResult(url=url, status="error", error_message=str(exc))


# ─────────────────────────────────────────────
# 2. File Types
# ─────────────────────────────────────────────
class FileTypeCheck:
    name = "Content & File Types"

    def __init__(self, media_formats: MediaFormats):
        self._legacy = media_formats.legacy_formats

    def run(self, sections: list[dict]) -> FileTypeResults:
        counts: dict[str, int] = defaultdict(int)
        legacy: list[str] = []

        for _, module in _iter_modules(sections):
            for content in module.get("contents", []):
                filename = content.get("filename", "")
                ext = _file_extension(filename) or "(none)"
                counts[ext] += 1
                if ext in self._legacy:
                    legacy.append(filename)

        return FileTypeResults(type_counts=dict(counts), legacy_files=legacy)


# ─────────────────────────────────────────────
# 3. File Sizes
# ─────────────────────────────────────────────
class FileSizeCheck:
    name = "File Sizes"

    def __init__(self, audit_config: AuditConfig):
        self._max_mb = audit_config.max_file_size_mb

    def run(self, sections: list[dict]) -> FileSizeResults:
        results = FileSizeResults()

        for _, module in _iter_modules(sections):
            module_name = module.get("name", "Unnamed")
            for content in module.get("contents", []):
                filename = content.get("filename", "unknown")
                size_mb = content.get("filesize", 0) / (1024 * 1024)
                results.file_count += 1
                results.total_size_mb += size_mb

                if size_mb > self._max_mb:
                    results.large_files.append(
                        FileInfo(filename=filename, extension=_file_extension(filename),
                                 size_mb=round(size_mb, 1), module_name=module_name)
                    )

        results.total_size_mb = round(results.total_size_mb, 1)
        return results


# ─────────────────────────────────────────────
# 4. Authenticated Access
# ─────────────────────────────────────────────
class AuthAccessCheck:
    name = "Authenticated Access"

    def __init__(self, audit_config: AuditConfig):
        self._timeout = audit_config.link_timeout_seconds
        self._delay = audit_config.delay_between_requests

    def run(self, sections: list[dict]) -> AuthAccessResults:
        results = AuthAccessResults()

        for _, module in _iter_modules(sections):
            for content in module.get("contents", []):
                file_url = content.get("fileurl", "")
                if not file_url:
                    continue
                filename = content.get("filename", "unknown")
                clean_url = file_url.split("?")[0]
                try:
                    time.sleep(self._delay)
                    resp = requests.head(clean_url, timeout=self._timeout, allow_redirects=True)
                    if resp.status_code < 400:
                        results.publicly_accessible.append(filename)
                except requests.RequestException:
                    pass  # Connection error = likely protected

        return results


# ─────────────────────────────────────────────
# 5. Content Depth
# ─────────────────────────────────────────────
class ContentDepthCheck:
    name = "Content Layering / Depth"

    DEEP_MODULE_TYPES = {"scorm", "book", "lesson"}

    def __init__(self, moodle_config: MoodleConfig, audit_config: AuditConfig):
        self._base_url = moodle_config.base_url
        self._threshold = audit_config.max_acceptable_depth

    def run(self, sections: list[dict]) -> ContentDepthResults:
        results = ContentDepthResults()

        for section, module in _iter_modules(sections):
            record = self._evaluate_module(section, module)
            results.max_depth = max(results.max_depth, record.depth)
            if record.depth > self._threshold:
                results.deep_modules.append(record)

        return results

    def _evaluate_module(self, section: dict, module: dict) -> DepthRecord:
        base_depth = 2  # section → module
        extra = 0

        for html in _html_fields(module):
            soup = html_utils.parse(html)
            internal = [a for a in soup.find_all("a", href=True) if self._base_url in a["href"]]
            if internal:
                extra = max(extra, 1)

        if module.get("modname") in self.DEEP_MODULE_TYPES:
            extra += 2

        total = base_depth + extra + (1 if module.get("contents") else 0)

        return DepthRecord(
            section=section.get("name", "Unnamed"),
            module=module.get("name", "Unnamed"),
            module_type=module.get("modname", "unknown"),
            depth=total,
        )


# ─────────────────────────────────────────────
# 6. Accessibility & Captions
# ─────────────────────────────────────────────
class AccessibilityCheck:
    name = "Accessibility & Captions"

    def __init__(self, media_formats: MediaFormats):
        self._video_exts = media_formats.supported_video | {".flv", ".wmv", ".avi"}
        self._caption_exts = media_formats.caption_formats

    def run(self, sections: list[dict]) -> AccessibilityResults:
        results = AccessibilityResults()
        all_filenames = self._collect_filenames(sections)

        for _, module in _iter_modules(sections):
            name = module.get("name", "Unnamed")
            self._check_html_accessibility(module, name, results)
            self._check_captions(module, name, all_filenames, results)

        return results

    # ── private ───────────────────────────────
    @staticmethod
    def _collect_filenames(sections: list[dict]) -> set[str]:
        names: set[str] = set()
        for _, module in _iter_modules(sections):
            for content in module.get("contents", []):
                names.add(content.get("filename", "").lower())
        return names

    @staticmethod
    def _check_html_accessibility(module: dict, name: str, results: AccessibilityResults):
        for html in _html_fields(module):
            soup = html_utils.parse(html)

            for _ in html_utils.find_images_without_alt(soup):
                results.issues.append(AccessibilityIssue(name, "missing_alt_text"))

            for _ in html_utils.find_empty_links(soup):
                results.issues.append(AccessibilityIssue(name, "empty_link"))

            for _ in html_utils.find_tables_without_headers(soup):
                results.issues.append(AccessibilityIssue(name, "table_missing_headers"))

            for prev, curr in html_utils.find_heading_skips(soup):
                results.issues.append(
                    AccessibilityIssue(name, "heading_skip", f"h{prev} → h{curr}")
                )

    def _check_captions(self, module: dict, name: str,
                        all_filenames: set[str], results: AccessibilityResults):
        for content in module.get("contents", []):
            filename = content.get("filename", "")
            ext = _file_extension(filename)
            if ext not in self._video_exts:
                continue
            base = filename.rsplit(".", 1)[0].lower()
            has_caption = any(
                base in fn and any(fn.endswith(ce) for ce in self._caption_exts)
                for fn in all_filenames
            )
            if not has_caption:
                results.videos_without_captions.append(filename)


# ─────────────────────────────────────────────
# 7. Malicious Code
# ─────────────────────────────────────────────
class MaliciousCodeCheck:
    name = "Malicious Code Detection"

    PATTERNS = [
        r"<script[\s>]", r"javascript\s*:", r"on(click|load|error|mouseover|focus)\s*=",
        r"<iframe[\s>]", r"<embed[\s>]", r"<object[\s>]",
        r"eval\s*\(", r"document\.cookie", r"window\.location", r"base64",
    ]

    def run(self, sections: list[dict]) -> MaliciousCodeResults:
        results = MaliciousCodeResults()

        for _, module in _iter_modules(sections):
            name = module.get("name", "Unnamed")
            for field_name in ("description", "content", "intro"):
                html = module.get(field_name, "")
                if not html:
                    continue
                for pattern in self.PATTERNS:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        results.findings.append(
                            SuspiciousCodeFinding(name, field_name, pattern, len(matches))
                        )

        return results


# ─────────────────────────────────────────────
# 8. Mobile Ready
# ─────────────────────────────────────────────
class MobileReadyCheck:
    name = "Mobile-Ready Content"

    POOR_MOBILE_TYPES = {"scorm", "lti"}

    def __init__(self, media_formats: MediaFormats):
        self._legacy = media_formats.legacy_formats

    def run(self, sections: list[dict]) -> MobileReadyResults:
        results = MobileReadyResults()

        for _, module in _iter_modules(sections):
            name = module.get("name", "Unnamed")
            mod_type = module.get("modname", "unknown")

            if mod_type in self.POOR_MOBILE_TYPES:
                results.issues.append(MobileIssue(name, f"'{mod_type}' limited mobile support"))

            for content in module.get("contents", []):
                filename = content.get("filename", "")
                ext = _file_extension(filename)
                if ext in self._legacy:
                    results.issues.append(MobileIssue(name, f"Legacy format '{ext}'", filename))

            for html in _html_fields(module):
                soup = html_utils.parse(html)
                if html_utils.has_fixed_pixel_width(soup):
                    results.issues.append(MobileIssue(name, "Fixed pixel width (not responsive)"))
                if html_utils.has_flash_embed(soup):
                    results.issues.append(MobileIssue(name, "Flash content detected"))

        return results
