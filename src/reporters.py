"""
src/reporters.py — Output formatters for audit results.

Open/Closed Principle: add new reporters without modifying existing ones.
"""

from __future__ import annotations

import csv
import json
import os
import smtplib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from src.models import CourseAuditResult


class Reporter(ABC):
    """Base class for all report output formats."""

    @abstractmethod
    def generate(self, results: list[CourseAuditResult], output_dir: str) -> str:
        """Write the report and return the file path."""


# ─────────────────────────────────────────────
# Console
# ─────────────────────────────────────────────
class ConsoleReporter(Reporter):
    """Prints a human-readable summary to stdout."""

    def generate(self, results: list[CourseAuditResult], output_dir: str = "") -> str:
        audited = [r for r in results if not r.skipped]
        skipped = [r for r in results if r.skipped]

        totals = self._aggregate(audited)

        print("\n" + "=" * 70)
        print("  MOODLE INSTANCE-WIDE QA AUDIT — FINAL SUMMARY")
        print("=" * 70)
        print(f"  Date:                  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Courses audited:       {len(audited)}")
        print(f"  Courses skipped:       {len(skipped)}")
        print(f"  Total files scanned:   {totals['total_files']}")
        print(f"  Total content size:    {totals['total_size_mb']:.1f} MB")
        print("-" * 70)
        print(f"  1. Broken links:           {totals['broken_links']}")
        print(f"  2. Legacy file formats:    {totals['legacy_formats']}")
        print(f"  3. Oversized files:        {totals['oversized_files']}")
        print(f"  4. Public resources:       {totals['public_resources']}")
        print(f"  5. Accessibility issues:   {totals['accessibility_issues']}")
        print(f"     Videos w/o captions:    {totals['videos_no_captions']}")
        print(f"  6. Suspicious code:        {totals['suspicious_code']}")
        print(f"  7. Mobile issues:          {totals['mobile_issues']}")
        print("=" * 70)

        self._print_top_offenders(audited)
        self._print_skipped(skipped)

        return "(console)"

    @staticmethod
    def _aggregate(audited: list[CourseAuditResult]) -> dict:
        t = dict.fromkeys([
            "broken_links", "legacy_formats", "oversized_files", "public_resources",
            "accessibility_issues", "videos_no_captions", "suspicious_code",
            "mobile_issues", "total_files", "total_size_mb",
        ], 0)
        for r in audited:
            t["broken_links"] += len(r.broken_links.broken)
            t["legacy_formats"] += len(r.file_types.legacy_files)
            t["oversized_files"] += len(r.file_sizes.large_files)
            t["public_resources"] += len(r.auth_access.publicly_accessible)
            t["accessibility_issues"] += len(r.accessibility.issues)
            t["videos_no_captions"] += len(r.accessibility.videos_without_captions)
            t["suspicious_code"] += len(r.malicious_code.findings)
            t["mobile_issues"] += len(r.mobile_ready.issues)
            t["total_files"] += r.file_sizes.file_count
            t["total_size_mb"] += r.file_sizes.total_size_mb
        return t

    @staticmethod
    def _print_top_offenders(audited: list[CourseAuditResult]):
        if not audited:
            return
        ranked = sorted(audited, key=lambda r: r.total_issues, reverse=True)[:5]
        print("\n  TOP 5 COURSES BY TOTAL ISSUES:")
        print("-" * 70)
        for i, r in enumerate(ranked, 1):
            print(f"  {i}. [{r.course_id}] {r.course_name} — {r.total_issues} issue(s)")

    @staticmethod
    def _print_skipped(skipped: list[CourseAuditResult]):
        if not skipped:
            return
        print(f"\n  SKIPPED COURSES ({len(skipped)}):")
        for r in skipped:
            print(f"    [{r.course_id}] {r.course_name} — {r.error}")


# ─────────────────────────────────────────────
# CSV — Summary (one row per course)
# ─────────────────────────────────────────────
class CsvSummaryReporter(Reporter):
    """Writes a one-row-per-course CSV summary."""

    HEADERS = [
        "Course ID", "Course Name", "Skipped", "Error",
        "Sections", "Modules", "Total Files", "Total Size (MB)",
        "Broken Links", "Timeouts", "Link Errors",
        "Legacy Formats", "Oversized Files", "Publicly Accessible",
        "Max Depth", "Deep Modules",
        "Accessibility Issues", "Videos w/o Captions",
        "Suspicious Code Patterns", "Mobile Issues", "Total Issues",
    ]

    def generate(self, results: list[CourseAuditResult], output_dir: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"qa_summary_{timestamp}.csv")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for r in results:
                writer.writerow(self._row(r))

        print(f"  CSV summary saved to: {path}")
        return path

    @staticmethod
    def _row(r: CourseAuditResult) -> list:
        if r.skipped:
            return [r.course_id, r.course_name, "YES", r.error or ""] + [""] * 17
        return [
            r.course_id, r.course_name, "NO", "",
            r.sections, r.modules,
            r.file_sizes.file_count, r.file_sizes.total_size_mb,
            len(r.broken_links.broken), len(r.broken_links.timeouts), len(r.broken_links.errors),
            len(r.file_types.legacy_files), len(r.file_sizes.large_files),
            len(r.auth_access.publicly_accessible),
            r.content_depth.max_depth, len(r.content_depth.deep_modules),
            len(r.accessibility.issues), len(r.accessibility.videos_without_captions),
            len(r.malicious_code.findings), len(r.mobile_ready.issues),
            r.total_issues,
        ]


# ─────────────────────────────────────────────
# CSV — Detailed (one row per issue)
# ─────────────────────────────────────────────
class CsvDetailedReporter(Reporter):
    """Writes a flat CSV with one row per individual issue found."""

    HEADERS = [
        "Course ID", "Course Name", "Check", "Severity",
        "Module", "Detail", "File/URL",
    ]

    def generate(self, results: list[CourseAuditResult], output_dir: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"qa_detailed_{timestamp}.csv")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)

            for r in results:
                if r.skipped:
                    writer.writerow([r.course_id, r.course_name, "SKIPPED", "info", "", r.error, ""])
                    continue
                self._write_broken_links(writer, r)
                self._write_file_types(writer, r)
                self._write_file_sizes(writer, r)
                self._write_auth_access(writer, r)
                self._write_content_depth(writer, r)
                self._write_accessibility(writer, r)
                self._write_malicious_code(writer, r)
                self._write_mobile_ready(writer, r)

        print(f"  CSV detailed report saved to: {path}")
        return path

    @staticmethod
    def _write_broken_links(writer: csv.writer, r: CourseAuditResult):
        for link in r.broken_links.broken:
            writer.writerow([
                r.course_id, r.course_name, "Broken Link", "error",
                "", f"HTTP {link.status_code}", link.url,
            ])
        for link in r.broken_links.timeouts:
            writer.writerow([
                r.course_id, r.course_name, "Broken Link", "warning",
                "", "Timeout", link.url,
            ])
        for link in r.broken_links.errors:
            writer.writerow([
                r.course_id, r.course_name, "Broken Link", "warning",
                "", link.error_message, link.url,
            ])

    @staticmethod
    def _write_file_types(writer: csv.writer, r: CourseAuditResult):
        for filename in r.file_types.legacy_files:
            writer.writerow([
                r.course_id, r.course_name, "Legacy File Format", "warning",
                "", "Requires special media player", filename,
            ])

    @staticmethod
    def _write_file_sizes(writer: csv.writer, r: CourseAuditResult):
        for fi in r.file_sizes.large_files:
            writer.writerow([
                r.course_id, r.course_name, "Oversized File", "warning",
                fi.module_name, f"{fi.size_mb} MB", fi.filename,
            ])

    @staticmethod
    def _write_auth_access(writer: csv.writer, r: CourseAuditResult):
        for filename in r.auth_access.publicly_accessible:
            writer.writerow([
                r.course_id, r.course_name, "Public Access", "error",
                "", "Accessible without authentication", filename,
            ])

    @staticmethod
    def _write_content_depth(writer: csv.writer, r: CourseAuditResult):
        for d in r.content_depth.deep_modules:
            writer.writerow([
                r.course_id, r.course_name, "Content Depth", "warning",
                d.module, f"Depth {d.depth} ({d.module_type})", d.section,
            ])

    @staticmethod
    def _write_accessibility(writer: csv.writer, r: CourseAuditResult):
        for issue in r.accessibility.issues:
            writer.writerow([
                r.course_id, r.course_name, "Accessibility", "warning",
                issue.module, f"{issue.issue_type}: {issue.detail}".strip(": "), "",
            ])
        for video in r.accessibility.videos_without_captions:
            writer.writerow([
                r.course_id, r.course_name, "Missing Captions", "warning",
                "", "No .vtt or .srt file found", video,
            ])

    @staticmethod
    def _write_malicious_code(writer: csv.writer, r: CourseAuditResult):
        for finding in r.malicious_code.findings:
            writer.writerow([
                r.course_id, r.course_name, "Suspicious Code", "error",
                finding.module, f"Pattern '{finding.pattern}' × {finding.match_count} in {finding.field}", "",
            ])

    @staticmethod
    def _write_mobile_ready(writer: csv.writer, r: CourseAuditResult):
        for issue in r.mobile_ready.issues:
            writer.writerow([
                r.course_id, r.course_name, "Mobile Compatibility", "warning",
                issue.module, issue.issue, issue.filename,
            ])


# ─────────────────────────────────────────────
# JSON
# ─────────────────────────────────────────────
class JsonReporter(Reporter):
    """Writes the full audit data as a JSON file."""

    def generate(self, results: list[CourseAuditResult], output_dir: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"full_instance_report_{timestamp}.json")

        serialisable = [asdict(r) for r in results]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serialisable, f, indent=2, default=str)

        print(f"  JSON report saved to: {path}")
        return path


# ─────────────────────────────────────────────
# Email Configuration
# ─────────────────────────────────────────────
@dataclass
class EmailConfig:
    """SMTP connection and message settings."""
    smtp_host: str
    smtp_port: int
    sender_email: str
    recipient_emails: list[str]
    subject_prefix: str = "[Moodle QA]"
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    attach_csv_summary: bool = True
    attach_csv_detailed: bool = True
    attach_json: bool = False


# ─────────────────────────────────────────────
# Email — HTML report with optional attachments
# ─────────────────────────────────────────────
class EmailReporter(Reporter):
    """Sends an HTML email summary with optional CSV/JSON attachments."""

    def __init__(self, config: EmailConfig):
        self._config = config

    def generate(self, results: list[CourseAuditResult], output_dir: str) -> str:
        audited = [r for r in results if not r.skipped]
        skipped = [r for r in results if r.skipped]
        totals = self._aggregate(audited)
        top_offenders = sorted(audited, key=lambda r: r.total_issues, reverse=True)[:5]

        # Build the email
        msg = MIMEMultipart("mixed")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg["Subject"] = f"{self._config.subject_prefix} Audit Report — {timestamp}"
        msg["From"] = self._config.sender_email
        msg["To"] = ", ".join(self._config.recipient_emails)

        # HTML body
        html_body = self._build_html(totals, audited, skipped, top_offenders, timestamp)
        msg.attach(MIMEText(html_body, "html"))

        # Attachments — look for generated files in output_dir
        self._attach_files(msg, output_dir)

        # Send
        try:
            self._send(msg)
            print(f"  ✓ Email sent to: {', '.join(self._config.recipient_emails)}")
            return f"email → {', '.join(self._config.recipient_emails)}"
        except Exception as exc:
            print(f"  ✗ Email failed: {exc}")
            return f"email failed: {exc}"

    # ── HTML body builder ─────────────────────
    def _build_html(
        self,
        totals: dict,
        audited: list[CourseAuditResult],
        skipped: list[CourseAuditResult],
        top_offenders: list[CourseAuditResult],
        timestamp: str,
    ) -> str:
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, Helvetica, sans-serif; color: #333; margin: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #2c3e50; margin-top: 30px; }}
                .summary-box {{
                    background: #f8f9fa; border: 1px solid #dee2e6;
                    border-radius: 8px; padding: 20px; margin: 20px 0;
                }}
                .stat {{ display: inline-block; margin: 10px 20px; text-align: center; }}
                .stat-value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th {{ background: #3498db; color: white; padding: 10px 12px; text-align: left; }}
                td {{ padding: 8px 12px; border-bottom: 1px solid #dee2e6; }}
                tr:nth-child(even) {{ background: #f8f9fa; }}
                .badge {{
                    display: inline-block; padding: 3px 10px; border-radius: 12px;
                    font-size: 12px; font-weight: bold; color: white;
                }}
                .badge-error {{ background: #e74c3c; }}
                .badge-warning {{ background: #f39c12; }}
                .badge-ok {{ background: #27ae60; }}
                .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #dee2e6;
                           font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <h1>Moodle QA Audit Report</h1>
            <p>Generated: <strong>{timestamp}</strong></p>

            <div class="summary-box">
                <div class="stat">
                    <div class="stat-value">{len(audited)}</div>
                    <div class="stat-label">Courses Audited</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(skipped)}</div>
                    <div class="stat-label">Skipped</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{totals['total_files']}</div>
                    <div class="stat-label">Files Scanned</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{totals['total_size_mb']:.1f} MB</div>
                    <div class="stat-label">Total Size</div>
                </div>
            </div>

            <h2>Issue Summary</h2>
            <table>
                <tr>
                    <th>Check</th>
                    <th>Issues Found</th>
                    <th>Status</th>
                </tr>
                {self._issue_row("Broken Links", totals["broken_links"])}
                {self._issue_row("Legacy File Formats", totals["legacy_formats"])}
                {self._issue_row("Oversized Files", totals["oversized_files"])}
                {self._issue_row("Publicly Accessible Resources", totals["public_resources"])}
                {self._issue_row("Accessibility Issues", totals["accessibility_issues"])}
                {self._issue_row("Videos Without Captions", totals["videos_no_captions"])}
                {self._issue_row("Suspicious Code Patterns", totals["suspicious_code"])}
                {self._issue_row("Mobile Compatibility", totals["mobile_issues"])}
            </table>
        """

        # Top offenders
        if top_offenders:
            html += """
            <h2>Top 5 Courses by Issues</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>Course</th>
                    <th>ID</th>
                    <th>Issues</th>
                </tr>
            """
            for i, r in enumerate(top_offenders, 1):
                badge = self._badge(r.total_issues)
                html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{r.course_name}</td>
                    <td>{r.course_id}</td>
                    <td>{badge}</td>
                </tr>
                """
            html += "</table>"

        # Per-course breakdown
        if audited:
            html += """
            <h2>Per-Course Breakdown</h2>
            <table>
                <tr>
                    <th>Course</th>
                    <th>Links</th>
                    <th>Legacy</th>
                    <th>Size</th>
                    <th>Auth</th>
                    <th>A11y</th>
                    <th>Captions</th>
                    <th>Code</th>
                    <th>Mobile</th>
                    <th>Total</th>
                </tr>
            """
            for r in sorted(audited, key=lambda x: x.total_issues, reverse=True):
                html += f"""
                <tr>
                    <td>{r.course_name}</td>
                    <td>{len(r.broken_links.broken)}</td>
                    <td>{len(r.file_types.legacy_files)}</td>
                    <td>{len(r.file_sizes.large_files)}</td>
                    <td>{len(r.auth_access.publicly_accessible)}</td>
                    <td>{len(r.accessibility.issues)}</td>
                    <td>{len(r.accessibility.videos_without_captions)}</td>
                    <td>{len(r.malicious_code.findings)}</td>
                    <td>{len(r.mobile_ready.issues)}</td>
                    <td><strong>{r.total_issues}</strong></td>
                </tr>
                """
            html += "</table>"

        # Skipped courses
        if skipped:
            html += """
            <h2>Skipped Courses</h2>
            <table>
                <tr><th>Course</th><th>ID</th><th>Reason</th></tr>
            """
            for r in skipped:
                html += f"<tr><td>{r.course_name}</td><td>{r.course_id}</td><td>{r.error}</td></tr>"
            html += "</table>"

        html += """
            <div class="footer">
                <p>This is an automated report from the Moodle QA Audit system.
                   CSV and JSON attachments contain full details for remediation.</p>
            </div>
        </body>
        </html>
        """
        return html

    # ── helpers ───────────────────────────────
    @staticmethod
    def _issue_row(label: str, count: int) -> str:
        if count == 0:
            badge = '<span class="badge badge-ok">PASS</span>'
        elif count <= 5:
            badge = f'<span class="badge badge-warning">{count}</span>'
        else:
            badge = f'<span class="badge badge-error">{count}</span>'
        return f"<tr><td>{label}</td><td>{count}</td><td>{badge}</td></tr>"

    @staticmethod
    def _badge(count: int) -> str:
        if count == 0:
            return '<span class="badge badge-ok">0</span>'
        elif count <= 5:
            return f'<span class="badge badge-warning">{count}</span>'
        return f'<span class="badge badge-error">{count}</span>'

    @staticmethod
    def _aggregate(audited: list[CourseAuditResult]) -> dict:
        t = dict.fromkeys([
            "broken_links", "legacy_formats", "oversized_files", "public_resources",
            "accessibility_issues", "videos_no_captions", "suspicious_code",
            "mobile_issues", "total_files", "total_size_mb",
        ], 0)
        for r in audited:
            t["broken_links"] += len(r.broken_links.broken)
            t["legacy_formats"] += len(r.file_types.legacy_files)
            t["oversized_files"] += len(r.file_sizes.large_files)
            t["public_resources"] += len(r.auth_access.publicly_accessible)
            t["accessibility_issues"] += len(r.accessibility.issues)
            t["videos_no_captions"] += len(r.accessibility.videos_without_captions)
            t["suspicious_code"] += len(r.malicious_code.findings)
            t["mobile_issues"] += len(r.mobile_ready.issues)
            t["total_files"] += r.file_sizes.file_count
            t["total_size_mb"] += r.file_sizes.total_size_mb
        return t

    def _attach_files(self, msg: MIMEMultipart, output_dir: str):
        """Attach generated report files based on config."""
        attachment_map = {
            "qa_summary_": self._config.attach_csv_summary,
            "qa_detailed_": self._config.attach_csv_detailed,
            "full_instance_report_": self._config.attach_json,
        }

        if not os.path.isdir(output_dir):
            return

        for filename in sorted(os.listdir(output_dir), reverse=True):
            for prefix, should_attach in attachment_map.items():
                if should_attach and filename.startswith(prefix):
                    filepath = os.path.join(output_dir, filename)
                    try:
                        with open(filepath, "rb") as f:
                            part = MIMEApplication(f.read(), Name=filename)
                        part["Content-Disposition"] = f'attachment; filename="{filename}"'
                        msg.attach(part)
                        print(f"    📎 Attached: {filename}")
                    except OSError as exc:
                        print(f"    ⚠ Could not attach {filename}: {exc}")
                    attachment_map[prefix] = False
                    break

    def _send(self, msg: MIMEMultipart):
        """Send the email via SMTP."""
        cfg = self._config

        if cfg.use_tls:
            server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port)

        try:
            if cfg.username and cfg.password:
                server.login(cfg.username, cfg.password)
            server.sendmail(cfg.sender_email, cfg.recipient_emails, msg.as_string())
        finally:
            server.quit()
