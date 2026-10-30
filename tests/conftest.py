"""
tests/conftest.py — Shared fixtures for the entire test suite.

Provides reusable Moodle course data, configurations, and mock objects.
"""

import pytest
from src.models import MoodleConfig, AuditConfig, MediaFormats


# ─────────────────────────────────────────────
# Configuration fixtures
# ─────────────────────────────────────────────
@pytest.fixture
def moodle_config():
    return MoodleConfig(
        base_url="https://moodle.test.ac.uk",
        token="test_token_abc123",
    )


@pytest.fixture
def audit_config():
    return AuditConfig(
        max_file_size_mb=50.0,
        link_timeout_seconds=5,
        max_acceptable_depth=4,
        delay_between_courses=0,
        delay_between_requests=0,
        only_visible_courses=True,
        exclude_course_ids=frozenset({1}),
        category_id=None,
    )


@pytest.fixture
def media_formats():
    return MediaFormats()


# ─────────────────────────────────────────────
# Sample Moodle course data
# ─────────────────────────────────────────────
@pytest.fixture
def empty_course_sections():
    """A course with one empty section."""
    return [{"name": "General", "modules": []}]


@pytest.fixture
def simple_course_sections():
    """A course with a single page module containing a file."""
    return [
        {
            "name": "Week 1",
            "modules": [
                {
                    "name": "Welcome Page",
                    "modname": "page",
                    "url": "https://moodle.test.ac.uk/mod/page/view.php?id=10",
                    "description": '<p>Welcome! <a href="https://example.com/guide">Guide</a></p>',
                    "content": "",
                    "contents": [
                        {
                            "filename": "intro.pdf",
                            "fileurl": "https://moodle.test.ac.uk/pluginfile.php/1/intro.pdf",
                            "filesize": 1048576,  # 1 MB
                        }
                    ],
                }
            ],
        }
    ]


@pytest.fixture
def complex_course_sections():
    """A course with multiple modules exercising all check paths."""
    return [
        {
            "name": "Week 1",
            "modules": [
                {
                    "name": "Lecture Video",
                    "modname": "resource",
                    "url": "https://moodle.test.ac.uk/mod/resource/view.php?id=20",
                    "description": "",
                    "content": '<p><img src="https://moodle.test.ac.uk/img/photo.jpg"></p>',
                    "contents": [
                        {
                            "filename": "lecture1.mp4",
                            "fileurl": "https://moodle.test.ac.uk/pluginfile.php/2/lecture1.mp4",
                            "filesize": 104857600,  # 100 MB
                        }
                    ],
                },
                {
                    "name": "Legacy Flash Activity",
                    "modname": "resource",
                    "url": "",
                    "description": "",
                    "content": '<embed type="application/x-shockwave-flash" src="old.swf">',
                    "contents": [
                        {
                            "filename": "animation.swf",
                            "fileurl": "https://moodle.test.ac.uk/pluginfile.php/3/animation.swf",
                            "filesize": 2097152,  # 2 MB
                        }
                    ],
                },
            ],
        },
        {
            "name": "Week 2",
            "modules": [
                {
                    "name": "SCORM Package",
                    "modname": "scorm",
                    "url": "https://moodle.test.ac.uk/mod/scorm/view.php?id=30",
                    "description": '<a href="https://moodle.test.ac.uk/mod/page/view.php?id=99">Deep link</a>',
                    "content": "",
                    "contents": [
                        {
                            "filename": "package.zip",
                            "fileurl": "https://moodle.test.ac.uk/pluginfile.php/4/package.zip",
                            "filesize": 5242880,  # 5 MB
                        }
                    ],
                },
            ],
        },
    ]


@pytest.fixture
def accessibility_problem_sections():
    """Course content with multiple accessibility issues."""
    return [
        {
            "name": "Section 1",
            "modules": [
                {
                    "name": "Bad Accessibility Page",
                    "modname": "page",
                    "url": "",
                    "description": """
                        <h1>Title</h1>
                        <h3>Skipped h2</h3>
                        <img src="photo.jpg">
                        <a href="https://example.com"></a>
                        <table><tr><td>No headers</td></tr></table>
                    """,
                    "content": "",
                    "contents": [
                        {
                            "filename": "lecture.mp4",
                            "fileurl": "https://moodle.test.ac.uk/pluginfile.php/5/lecture.mp4",
                            "filesize": 10485760,
                        }
                    ],
                }
            ],
        }
    ]


@pytest.fixture
def malicious_content_sections():
    """Course content with suspicious code patterns."""
    return [
        {
            "name": "Section 1",
            "modules": [
                {
                    "name": "Injected Page",
                    "modname": "page",
                    "url": "",
                    "description": """
                        <p>Normal text</p>
                        <script>alert('xss')</script>
                        <a href="javascript:void(0)">Click</a>
                        <img onerror="alert(1)" src="x">
                    """,
                    "content": '<p>Also has eval("code") and document.cookie access</p>',
                    "contents": [],
                }
            ],
        }
    ]


@pytest.fixture
def mobile_problem_sections():
    """Course content with mobile compatibility issues."""
    return [
        {
            "name": "Section 1",
            "modules": [
                {
                    "name": "Fixed Width Page",
                    "modname": "page",
                    "url": "",
                    "description": '<div style="width: 1200px;">Too wide</div>',
                    "content": '<embed type="application/x-shockwave-flash" src="old.swf">',
                    "contents": [
                        {
                            "filename": "old_video.wmv",
                            "fileurl": "https://moodle.test.ac.uk/pluginfile.php/6/old_video.wmv",
                            "filesize": 5242880,
                        }
                    ],
                },
                {
                    "name": "SCORM Module",
                    "modname": "scorm",
                    "url": "",
                    "description": "",
                    "content": "",
                    "contents": [],
                },
                {
                    "name": "LTI Tool",
                    "modname": "lti",
                    "url": "",
                    "description": "",
                    "content": "",
                    "contents": [],
                },
            ],
        }
    ]


@pytest.fixture
def sample_courses():
    """List of course dicts as returned by the Moodle API."""
    return [
        {"id": 1, "fullname": "Site Course", "visible": 1, "categoryid": 0},
        {"id": 2, "fullname": "Intro to Python", "visible": 1, "categoryid": 5},
        {"id": 3, "fullname": "Advanced Maths", "visible": 1, "categoryid": 5},
        {"id": 4, "fullname": "Hidden Course", "visible": 0, "categoryid": 5},
        {"id": 5, "fullname": "Art History", "visible": 1, "categoryid": 10},
    ]
