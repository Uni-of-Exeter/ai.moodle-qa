"""
src/models.py — Data models for the Moodle QA audit system.

All domain objects are immutable dataclasses with clear types.
"""

from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class MoodleConfig:
    """Connection settings for the Moodle instance."""
    base_url: str
    token: str


@dataclass(frozen=True)
class AuditConfig:
    """Thresholds and behavioural settings for the audit."""
    max_file_size_mb: float = 50.0
    link_timeout_seconds: int = 10
    max_acceptable_depth: int = 4
    delay_between_courses: float = 1.0
    delay_between_requests: float = 0.2
    only_visible_courses: bool = True
    exclude_course_ids: frozenset[int] = frozenset({1})
    category_id: Optional[int] = None


# ─────────────────────────────────────────────
# Media / format constants
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class MediaFormats:
    """Recognised file format groups."""
    supported_video: frozenset[str] = frozenset({".mp4", ".webm", ".ogv"})
    supported_audio: frozenset[str] = frozenset({".mp3", ".ogg", ".wav", ".m4a"})
    caption_formats: frozenset[str] = frozenset({".vtt", ".srt"})
    legacy_formats: frozenset[str] = frozenset({".swf", ".flv", ".wmv", ".avi", ".rm", ".ram"})


# ─────────────────────────────────────────────
# Issue / finding records
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class LinkResult:
    url: str
    status: str  # "ok", "broken", "timeout", "error"
    status_code: Optional[int] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class FileInfo:
    filename: str
    extension: str
    size_mb: float
    module_name: str


@dataclass(frozen=True)
class AccessIssue:
    filename: str
    is_publicly_accessible: bool


@dataclass(frozen=True)
class DepthRecord:
    section: str
    module: str
    module_type: str
    depth: int


@dataclass(frozen=True)
class AccessibilityIssue:
    module: str
    issue_type: str
    detail: str = ""


@dataclass(frozen=True)
class SuspiciousCodeFinding:
    module: str
    field: str
    pattern: str
    match_count: int


@dataclass(frozen=True)
class MobileIssue:
    module: str
    issue: str
    filename: str = ""


# ─────────────────────────────────────────────
# Aggregated check results
# ─────────────────────────────────────────────
@dataclass
class BrokenLinkResults:
    ok_count: int = 0
    broken: list[LinkResult] = field(default_factory=list)
    timeouts: list[LinkResult] = field(default_factory=list)
    errors: list[LinkResult] = field(default_factory=list)


@dataclass
class FileTypeResults:
    type_counts: dict[str, int] = field(default_factory=dict)
    legacy_files: list[str] = field(default_factory=list)


@dataclass
class FileSizeResults:
    large_files: list[FileInfo] = field(default_factory=list)
    total_size_mb: float = 0.0
    file_count: int = 0


@dataclass
class AuthAccessResults:
    publicly_accessible: list[str] = field(default_factory=list)


@dataclass
class ContentDepthResults:
    max_depth: int = 0
    deep_modules: list[DepthRecord] = field(default_factory=list)


@dataclass
class AccessibilityResults:
    issues: list[AccessibilityIssue] = field(default_factory=list)
    videos_without_captions: list[str] = field(default_factory=list)


@dataclass
class MaliciousCodeResults:
    findings: list[SuspiciousCodeFinding] = field(default_factory=list)


@dataclass
class MobileReadyResults:
    issues: list[MobileIssue] = field(default_factory=list)


# ─────────────────────────────────────────────
# Course-level result
# ─────────────────────────────────────────────
@dataclass
class CourseAuditResult:
    course_id: int
    course_name: str
    sections: int = 0
    modules: int = 0
    skipped: bool = False
    error: Optional[str] = None
    broken_links: BrokenLinkResults = field(default_factory=BrokenLinkResults)
    file_types: FileTypeResults = field(default_factory=FileTypeResults)
    file_sizes: FileSizeResults = field(default_factory=FileSizeResults)
    auth_access: AuthAccessResults = field(default_factory=AuthAccessResults)
    content_depth: ContentDepthResults = field(default_factory=ContentDepthResults)
    accessibility: AccessibilityResults = field(default_factory=AccessibilityResults)
    malicious_code: MaliciousCodeResults = field(default_factory=MaliciousCodeResults)
    mobile_ready: MobileReadyResults = field(default_factory=MobileReadyResults)

    @property
    def total_issues(self) -> int:
        return (
            len(self.broken_links.broken)
            + len(self.file_types.legacy_files)
            + len(self.file_sizes.large_files)
            + len(self.auth_access.publicly_accessible)
            + len(self.accessibility.issues)
            + len(self.accessibility.videos_without_captions)
            + len(self.malicious_code.findings)
            + len(self.mobile_ready.issues)
        )
