# Moodle Course QA Automation Tool

A clean-architecture Python tool that programmatically audits **every course** on a Moodle instance across 8 quality assurance dimensions. Designed for learning technologists, system administrators, and QA teams who need to maintain content standards at scale.

---

## Features

- **Instance-wide auditing** — automatically iterates over all courses (or a filtered subset)
- **8 comprehensive QA checks** covering links, files, accessibility, security, and mobile readiness
- **Multiple output formats** — console, CSV summary, CSV detailed, JSON, and HTML email
- **Clean architecture** — modular, testable, and easy to extend with new checks or reporters
- **Rate limiting** — configurable delays to avoid overloading your Moodle server
- **Graceful error handling** — skipped courses are logged without halting the audit
- **CLI-driven** — all options controllable via command-line arguments
- **Secure credentials** — SMTP passwords via environment variables, not command-line history
- **Fully tested** — comprehensive pytest suite with mocked HTTP and SMTP, no network calls required

---

## QA Checks

| # | Check | What It Does |
|---|-------|-------------|
| 1 | **Broken Links** | Extracts all URLs from course content (links, images, media, iframes) and tests each with an HTTP HEAD request. Reports broken (4xx/5xx), timed-out, and errored URLs. |
| 2 | **Content & File Types** | Catalogues every file extension in the course. Flags legacy formats (`.swf`, `.flv`, `.wmv`, `.avi`, `.rm`) that require special media players or plugins. |
| 3 | **File Sizes** | Flags files exceeding a configurable size threshold (default: 50 MB) that may cause slow downloads or timeout issues for users on limited networks. |
| 4 | **Authenticated Access** | Tests whether course resources are publicly accessible without a valid token. Flags any files that should be behind authentication but are not. |
| 5 | **Content Layering / Depth** | Maps the section → module → content hierarchy. Flags deeply nested structures (especially SCORM, Book, and Lesson modules) that exceed a configurable depth threshold. |
| 6 | **Accessibility & Captions** | Checks HTML content for: images missing alt text, empty links, tables without headers, skipped heading levels. Also checks whether video files have corresponding `.vtt` or `.srt` caption files. |
| 7 | **Malicious Code Detection** | Scans HTML content fields for suspicious patterns including `<script>` tags, `javascript:` URIs, inline event handlers (`onclick`, `onload`), `eval()`, `document.cookie`, `<iframe>`, and Base64-encoded content. |
| 8 | **Mobile-Ready Content** | Flags Flash content, legacy media formats unsupported on mobile, fixed pixel-width elements (not responsive), and module types with limited mobile support (SCORM, LTI). |

---

## Prerequisites

- **Python 3.10+** (uses `frozenset` type hints and `match` syntax)
- **Moodle 3.1+** with Web Services enabled
- A Moodle **API token** with access to `core_course_get_courses` and `core_course_get_contents`
- Network access from the machine running the script to your Moodle instance

---

## Installation

```bash
# Clone or download the project
cd moodle_qa

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Edit the top of `main.py` to set your Moodle connection details:

```python
# ─── Connection ───────────────────────────────
MOODLE_URL = "https://moodle.your-university.ac.uk"
TOKEN = "your_webservice_token_here"

# ─── Audit thresholds ────────────────────────
audit_config = AuditConfig(
    max_file_size_mb=50.0,           # Flag files larger than this
    link_timeout_seconds=10,          # Seconds before a link check times out
    max_acceptable_depth=4,           # Flag content nested deeper than this
    delay_between_courses=1.0,        # Seconds between courses (rate limiting)
    delay_between_requests=0.2,       # Seconds between HTTP requests
    only_visible_courses=True,        # Skip hidden courses
    exclude_course_ids=frozenset({1}),# Exclude site-level course
    category_id=None,                 # Set to int to limit to one category
)
```

---

## Usage

### Basic Usage

```bash
# Default: console summary + JSON report
python main.py

# Custom output directory
python main.py --output ./my_reports
```

### Output Formats

```bash
# Add CSV summary (one row per course)
python main.py --csv

# Add detailed CSV (one row per issue)
python main.py --csv-detailed

# Both CSV reports
python main.py --csv --csv-detailed

# All file formats
python main.py --all

# Disable specific outputs
python main.py --no-console          # No console output
python main.py --no-json             # No JSON file
python main.py --no-console --no-json --csv  # CSV only
```

### Email Reports

```bash
# Email to one recipient
python main.py --email admin@uni.ac.uk

# Email to multiple recipients
python main.py --email admin@uni.ac.uk qa-team@uni.ac.uk

# Custom SMTP settings
python main.py --email admin@uni.ac.uk \
    --smtp-host smtp.uni.ac.uk \
    --smtp-port 587 \
    --sender moodle-qa@uni.ac.uk

# Attach the full JSON report to the email
python main.py --email admin@uni.ac.uk --email-attach-json

# Full audit with all outputs + email
python main.py --all --email admin@uni.ac.uk qa@uni.ac.uk
```

---

## Environment Variables

Set these to avoid passing sensitive credentials on the command line:

```bash
export MOODLE_QA_SMTP_HOST="smtp.exeter.ac.uk"
export MOODLE_QA_SMTP_PORT="587"
export MOODLE_QA_SENDER="moodle-qa@exeter.ac.uk"
export MOODLE_QA_SMTP_USER="svc-moodle-qa"
export MOODLE_QA_SMTP_PASS="your_secure_password"
```

---

## Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing
```

---

## Moodle API Setup

To generate the API token your script needs:

1. **Enable Web Services**: *Site Administration → Advanced features → Enable web services* ✓
2. **Enable REST protocol**: *Site Administration → Plugins → Web services → Manage protocols → REST* ✓
3. **Create a service**: *Site Administration → Plugins → Web services → External services → Add*
   - Name: `QA Audit Service`
   - Enabled: ✓
   - Authorised users only: ✓
4. **Add functions to the service**:
   - `core_course_get_courses`
   - `core_course_get_contents`
5. **Create a dedicated user account** (e.g., `svc-qa-audit`)
6. **Generate a token**: *Site Administration → Plugins → Web services → Manage tokens → Create token*

---

## Project Structure

```
moodle_qa/
├── main.py              # Entry point — CLI parsing and dependency wiring
├── README.md            # This file
├── requirements.txt     # Python dependencies
├── src/
│   ├── __init__.py
│   ├── models.py        # Data models and configuration
│   ├── moodle_client.py # Moodle REST API wrapper
│   ├── html_utils.py    # HTML parsing helpers
│   ├── checks.py        # 8 QA check implementations
│   ├── reporters.py     # Output formatters
│   └── engine.py        # Audit orchestrator
└── tests/
    ├── conftest.py      # Shared test fixtures
    ├── test_models.py
    ├── test_html_utils.py
    ├── test_moodle_client.py
    ├── test_checks.py
    ├── test_reporters.py
    └── test_engine.py
```

---

## License

This project is provided as-is for educational and institutional use. Adapt and extend it to suit your organisation's needs.
