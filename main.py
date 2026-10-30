"""
main.py — Application entry point.

Wires up all dependencies and launches the audit.
This is the ONLY file you need to edit for configuration.

Usage:
  python main.py                                          # Console + JSON (default)
  python main.py --csv                                    # Add CSV summary
  python main.py --csv --csv-detailed                     # Add both CSV reports
  python main.py --all                                    # All file outputs
  python main.py --email admin@uni.ac.uk                  # Email report to one recipient
  python main.py --email admin@uni.ac.uk qa@uni.ac.uk     # Email to multiple recipients
  python main.py --all --email admin@uni.ac.uk            # Everything + email
  python main.py --output ./reports                       # Custom output directory
"""

import argparse
import os

from src.models import MoodleConfig, AuditConfig, MediaFormats
from src.moodle_client import MoodleClient
from src.checks import (
    BrokenLinkCheck,
    FileTypeCheck,
    FileSizeCheck,
    AuthAccessCheck,
    ContentDepthCheck,
    AccessibilityCheck,
    MaliciousCodeCheck,
    MobileReadyCheck,
)
from src.reporters import (
    ConsoleReporter,
    CsvSummaryReporter,
    CsvDetailedReporter,
    JsonReporter,
    EmailReporter,
    EmailConfig,
    Reporter,
)
from src.engine import AuditEngine


# ─────────────────────────────────────────────
# CONFIGURATION — update these for your instance
# ─────────────────────────────────────────────
MOODLE_URL = "http://localhost:8080"
TOKEN = "b5f2d7d6565e354ec6ac05cbb350f81c"

moodle_config = MoodleConfig(base_url=MOODLE_URL, token=TOKEN)

audit_config = AuditConfig(
    max_file_size_mb=50.0,
    link_timeout_seconds=10,
    max_acceptable_depth=4,
    delay_between_courses=1.0,
    delay_between_requests=0.2,
    only_visible_courses=True,
    exclude_course_ids=frozenset({1}),
    category_id=None,
)

media_formats = MediaFormats()

# ─────────────────────────────────────────────
# EMAIL DEFAULTS — override via CLI or env vars
# ─────────────────────────────────────────────
DEFAULT_SMTP_HOST = os.environ.get("MOODLE_QA_SMTP_HOST", "smtp.your-university.ac.uk")
DEFAULT_SMTP_PORT = int(os.environ.get("MOODLE_QA_SMTP_PORT", "587"))
DEFAULT_SENDER = os.environ.get("MOODLE_QA_SENDER", "moodle-qa@your-university.ac.uk")
DEFAULT_SMTP_USER = os.environ.get("MOODLE_QA_SMTP_USER", "")
DEFAULT_SMTP_PASS = os.environ.get("MOODLE_QA_SMTP_PASS", "")


# ─────────────────────────────────────────────
# CLI ARGUMENT PARSER
# ─────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Moodle Course QA Audit — run quality checks across all courses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                          Console + JSON (default)
  python main.py --csv                                    Add CSV summary
  python main.py --csv --csv-detailed                     Add both CSV reports
  python main.py --all                                    All file outputs
  python main.py --email admin@uni.ac.uk                  Email report to one address
  python main.py --email admin@uni.ac.uk qa@uni.ac.uk     Email to multiple addresses
  python main.py --all --email admin@uni.ac.uk            Everything + email
  python main.py --no-console --email admin@uni.ac.uk     Email only, silent console

Environment variables for email (avoids CLI secrets):
  MOODLE_QA_SMTP_HOST    SMTP server hostname
  MOODLE_QA_SMTP_PORT    SMTP server port (default: 587)
  MOODLE_QA_SENDER       Sender email address
  MOODLE_QA_SMTP_USER    SMTP username
  MOODLE_QA_SMTP_PASS    SMTP password
        """,
    )

    # File output formats
    output_group = parser.add_argument_group("File output formats")
    output_group.add_argument(
        "--csv", action="store_true",
        help="Generate a CSV summary report (one row per course)",
    )
    output_group.add_argument(
        "--csv-detailed", action="store_true",
        help="Generate a detailed CSV report (one row per issue)",
    )
    output_group.add_argument(
        "--json", action="store_true", default=True,
        help="Generate a full JSON report (default: enabled)",
    )
    output_group.add_argument(
        "--no-json", action="store_true",
        help="Disable JSON report output",
    )
    output_group.add_argument(
        "--no-console", action="store_true",
        help="Suppress console summary output",
    )
    output_group.add_argument(
        "--all", action="store_true",
        help="Enable all file output formats (console, CSV summary, CSV detailed, JSON)",
    )

    # Email options
    email_group = parser.add_argument_group("Email options")
    email_group.add_argument(
        "--email", nargs="+", metavar="ADDRESS",
        help="Send the report via email to one or more recipients",
    )
    email_group.add_argument(
        "--smtp-host", type=str, default=DEFAULT_SMTP_HOST,
        help=f"SMTP server hostname (default: {DEFAULT_SMTP_HOST})",
    )
    email_group.add_argument(
        "--smtp-port", type=int, default=DEFAULT_SMTP_PORT,
        help=f"SMTP server port (default: {DEFAULT_SMTP_PORT})",
    )
    email_group.add_argument(
        "--sender", type=str, default=DEFAULT_SENDER,
        help=f"Sender email address (default: {DEFAULT_SENDER})",
    )
    email_group.add_argument(
        "--smtp-user", type=str, default=DEFAULT_SMTP_USER,
        help="SMTP username (default: from env MOODLE_QA_SMTP_USER)",
    )
    email_group.add_argument(
        "--smtp-pass", type=str, default=DEFAULT_SMTP_PASS,
        help="SMTP password (default: from env MOODLE_QA_SMTP_PASS)",
    )
    email_group.add_argument(
        "--no-tls", action="store_true",
        help="Disable STARTTLS for SMTP connection",
    )
    email_group.add_argument(
        "--email-attach-json", action="store_true",
        help="Attach the full JSON report to the email (large file)",
    )
    email_group.add_argument(
        "--email-subject", type=str, default="[Moodle QA]",
        help="Email subject prefix (default: [Moodle QA])",
    )

    # General
    parser.add_argument(
        "--output", "-o", type=str, default="moodle_qa_reports",
        help="Output directory for report files (default: moodle_qa_reports)",
    )

    return parser.parse_args()


# ─────────────────────────────────────────────
# DEPENDENCY WIRING
# ─────────────────────────────────────────────
def build_reporters(args: argparse.Namespace) -> list[Reporter]:
    """Assemble the list of reporters based on CLI flags."""
    reporters: list[Reporter] = []

    include_console = not args.no_console or args.all
    include_csv = args.csv or args.all
    include_csv_detailed = args.csv_detailed or args.all
    include_json = (args.json and not args.no_json) or args.all

    if include_console:
        reporters.append(ConsoleReporter())
    if include_csv:
        reporters.append(CsvSummaryReporter())
    if include_csv_detailed:
        reporters.append(CsvDetailedReporter())
    if include_json:
        reporters.append(JsonReporter())

    # Email reporter — must come AFTER file reporters so attachments exist
    if args.email:
        email_config = EmailConfig(
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            sender_email=args.sender,
            recipient_emails=args.email,
            subject_prefix=args.email_subject,
            username=args.smtp_user or None,
            password=args.smtp_pass or None,
            use_tls=not args.no_tls,
            attach_csv_summary=include_csv,
            attach_csv_detailed=include_csv_detailed,
            attach_json=args.email_attach_json,
        )
        reporters.append(EmailReporter(email_config))

    if not reporters:
        print("  ⚠ No output formats selected — defaulting to console.")
        reporters.append(ConsoleReporter())

    return reporters


def build_checks() -> list:
    """Assemble the list of QA checks."""
    return [
        BrokenLinkCheck(moodle_config, audit_config),
        FileTypeCheck(media_formats),
        FileSizeCheck(audit_config),
        AuthAccessCheck(audit_config),
        ContentDepthCheck(moodle_config, audit_config),
        AccessibilityCheck(media_formats),
        MaliciousCodeCheck(),
        MobileReadyCheck(media_formats),
    ]


def build_engine(args: argparse.Namespace) -> AuditEngine:
    """Wire up all dependencies and return the audit engine."""
    client = MoodleClient(moodle_config)
    checks = build_checks()
    reporters = build_reporters(args)

    return AuditEngine(
        client=client,
        audit_config=audit_config,
        checks=checks,
        reporters=reporters,
        output_dir=args.output,
    )


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()
    engine = build_engine(args)
    engine.run()
