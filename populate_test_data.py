#!/usr/bin/env python3
"""
Populate Moodle with test data for QA automation tool testing.

Creates courses with intentional QA issues to test all 8 QA checks:
1. Broken Links
2. Legacy File Types
3. Large Files
4. Authenticated Access
5. Content Depth
6. Accessibility Issues
7. Malicious Code
8. Mobile Incompatibility

Usage:
    python populate_test_data.py --url http://localhost:8080 --token YOUR_TOKEN
"""

import argparse
import sys
import requests
import json
from typing import Dict, List, Any


class MoodleTestDataPopulator:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.api_url = f"{self.url}/webservice/rest/server.php"

    def call_api(self, function: str, params: Dict[str, Any]) -> Any:
        """Call Moodle Web Services API."""
        data = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json',
            **params
        }

        try:
            response = requests.post(self.api_url, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            if isinstance(result, dict) and 'exception' in result:
                raise Exception(f"Moodle API Error: {result.get('message', result)}")

            return result
        except requests.RequestException as e:
            raise Exception(f"API request failed: {e}")

    def get_category_id(self) -> int:
        """Get or create a test category."""
        # Get categories
        categories = self.call_api('core_course_get_categories', {
            'criteria[0][key]': 'name',
            'criteria[0][value]': 'QA Test Courses'
        })

        if categories:
            return categories[0]['id']

        # Create category
        result = self.call_api('core_course_create_categories', {
            'categories[0][name]': 'QA Test Courses',
            'categories[0][parent]': 0,
            'categories[0][description]': 'Auto-generated test courses for QA tool testing',
            'categories[0][descriptionformat]': 1
        })
        return result[0]['id']

    def delete_existing_test_courses(self):
        """Delete existing test courses to make the script idempotent."""
        print("🧹 Checking for existing test courses...")

        courses = self.call_api('core_course_get_courses', {})
        test_courses = [c for c in courses if c['shortname'].startswith('QATEST')]

        if test_courses:
            print(f"   Found {len(test_courses)} existing test courses, deleting...")
            for course in test_courses:
                try:
                    self.call_api('core_course_delete_courses', {
                        'courseids[0]': course['id']
                    })
                    print(f"   ✓ Deleted: {course['shortname']}")
                except Exception as e:
                    print(f"   ⚠ Could not delete {course['shortname']}: {e}")
        else:
            print("   No existing test courses found")

    def create_course(self, shortname: str, fullname: str, category_id: int) -> int:
        """Create a course and return its ID."""
        result = self.call_api('core_course_create_courses', {
            'courses[0][fullname]': fullname,
            'courses[0][shortname]': shortname,
            'courses[0][categoryid]': category_id,
            'courses[0][visible]': 1,
            'courses[0][format]': 'topics',
            'courses[0][numsections]': 3
        })
        return result[0]['id']

    def add_page_with_content(self, course_id: int, name: str, content: str, section: int = 0):
        """Add a page resource with HTML content."""
        try:
            # Try to update course summary with the content
            # This is a workaround since core_course_create_contents may not be available
            self.call_api('core_course_update_courses', {
                'courses[0][id]': course_id,
                'courses[0][summary]': content,
                'courses[0][summaryformat]': 1
            })
        except Exception as e:
            # If we can't add content, just log it - courses will still exist for testing
            print(f"      ⚠ Could not add content (course created but empty): {e}")

    def create_broken_links_course(self, category_id: int):
        """Course 1: Broken Links Test."""
        print("\n📝 Creating Course 1: Broken Links Test")

        course_id = self.create_course(
            'QATEST-LINKS',
            'QA Test 1: Broken Links',
            category_id
        )

        # Content with various broken links
        content = """
        <h2>Test Page with Broken Links</h2>
        <p>This page contains intentionally broken links for testing.</p>

        <h3>External Links</h3>
        <ul>
            <li><a href="https://example.com/does-not-exist">Broken link 1 (404)</a></li>
            <li><a href="http://broken-domain-12345.com">Broken domain</a></li>
            <li><a href="https://httpstat.us/500">Server error link (500)</a></li>
        </ul>

        <h3>Broken Images</h3>
        <img src="https://example.com/missing-image.jpg" alt="This image is missing">
        <img src="http://broken-domain.example/logo.png" alt="Another broken image">

        <h3>Broken Media</h3>
        <video src="https://example.com/missing-video.mp4" controls></video>
        <iframe src="https://example.com/missing-embed"></iframe>
        """

        self.add_page_with_content(course_id, 'Broken Links Test Page', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def create_legacy_files_course(self, category_id: int):
        """Course 2: Legacy File Types Test."""
        print("\n📝 Creating Course 2: Legacy File Types Test")

        course_id = self.create_course(
            'QATEST-LEGACY',
            'QA Test 2: Legacy File Types',
            category_id
        )

        # Content referencing legacy file types
        content = """
        <h2>Legacy File Formats</h2>
        <p>This course references legacy media formats that need updating.</p>

        <h3>Flash Content</h3>
        <object data="animation.swf" type="application/x-shockwave-flash"></object>
        <embed src="game.swf" type="application/x-shockwave-flash"></embed>

        <h3>Legacy Video Formats</h3>
        <p>Old video files:</p>
        <ul>
            <li><a href="training_video.flv">FLV video file</a></li>
            <li><a href="presentation.wmv">WMV video file</a></li>
            <li><a href="demo.avi">AVI video file</a></li>
            <li><a href="legacy_recording.rm">RealMedia file</a></li>
        </ul>

        <h3>Other Legacy Formats</h3>
        <video src="old_lecture.flv" controls></video>
        <p>Download: <a href="archive.wmv">Windows Media Video</a></p>
        """

        self.add_page_with_content(course_id, 'Legacy Formats Page', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def create_large_files_course(self, category_id: int):
        """Course 3: Large Files Test."""
        print("\n📝 Creating Course 3: Large Files Test")

        course_id = self.create_course(
            'QATEST-LARGE',
            'QA Test 3: Large Files',
            category_id
        )

        content = """
        <h2>Large File References</h2>
        <p>This course simulates large file references.</p>

        <p><strong>Note:</strong> These are simulated references - the actual files don't exist,
        but the QA tool should flag them based on the names suggesting large sizes.</p>

        <ul>
            <li><a href="full_course_video_1080p_uncompressed.mp4">Course Video (120MB)</a></li>
            <li><a href="dataset_archive_full.zip">Large Dataset (250MB)</a></li>
            <li><a href="high_res_images_pack.zip">High Resolution Images (85MB)</a></li>
            <li><a href="software_installer_v2.exe">Software Package (150MB)</a></li>
        </ul>

        <p>The file names indicate these would exceed the 50MB threshold.</p>
        """

        self.add_page_with_content(course_id, 'Large Files Page', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def create_accessibility_course(self, category_id: int):
        """Course 4: Accessibility Issues Test."""
        print("\n📝 Creating Course 4: Accessibility Issues Test")

        course_id = self.create_course(
            'QATEST-A11Y',
            'QA Test 4: Accessibility Issues',
            category_id
        )

        # Content with accessibility violations
        content = """
        <h2>Accessibility Issues Page</h2>

        <h3>Images Without Alt Text</h3>
        <img src="diagram.png">
        <img src="chart.jpg">
        <img src="infographic.png" alt="">

        <h3>Empty Links</h3>
        <p>Click <a href="next.html"></a> to continue.</p>
        <p>More info: <a href="info.html">   </a></p>

        <h3>Tables Without Headers</h3>
        <table border="1">
            <tr>
                <td>Name</td>
                <td>Score</td>
                <td>Grade</td>
            </tr>
            <tr>
                <td>John</td>
                <td>85</td>
                <td>B</td>
            </tr>
            <tr>
                <td>Jane</td>
                <td>92</td>
                <td>A</td>
            </tr>
        </table>

        <h3>Skipped Heading Levels</h3>
        <h2>Section Title</h2>
        <h5>Subsection (skipped h3 and h4)</h5>

        <h3>Videos Without Captions</h3>
        <video src="lecture_video.mp4" controls></video>
        <p>Note: No .vtt or .srt caption file available</p>
        """

        self.add_page_with_content(course_id, 'Accessibility Issues', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def create_malicious_code_course(self, category_id: int):
        """Course 5: Malicious Code Detection Test."""
        print("\n📝 Creating Course 5: Malicious Code Test")

        course_id = self.create_course(
            'QATEST-SECURITY',
            'QA Test 5: Malicious Code Detection',
            category_id
        )

        # Content with suspicious patterns (escaped for safety)
        content = """
        <h2>Security Test Page</h2>
        <p><strong>Note:</strong> This page contains intentionally suspicious code patterns for testing.</p>

        <h3>Inline Scripts</h3>
        <p>This paragraph has an inline script:
        &lt;script&gt;alert('test');&lt;/script&gt;
        </p>

        <h3>JavaScript URIs</h3>
        <a href="javascript:void(0)">JavaScript link</a>
        <a href="javascript:alert('click')">Another JS link</a>

        <h3>Inline Event Handlers</h3>
        <button onclick="alert('clicked')">Click Me</button>
        <div onload="runCode()">Auto-loading div</div>
        <img src="test.jpg" onerror="handleError()">

        <h3>Suspicious JavaScript</h3>
        <p>Code snippet: <code>eval(userInput)</code></p>
        <p>Code snippet: <code>document.cookie</code></p>

        <h3>Embedded iframe</h3>
        <iframe src="https://external-site.com/embed"></iframe>
        """

        self.add_page_with_content(course_id, 'Security Test Page', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def create_mobile_issues_course(self, category_id: int):
        """Course 6: Mobile Compatibility Issues Test."""
        print("\n📝 Creating Course 6: Mobile Compatibility Test")

        course_id = self.create_course(
            'QATEST-MOBILE',
            'QA Test 6: Mobile Compatibility',
            category_id
        )

        content = """
        <h2>Mobile Compatibility Issues</h2>

        <h3>Flash Content (Not Mobile-Friendly)</h3>
        <object data="interactive.swf" type="application/x-shockwave-flash" width="800" height="600">
            <param name="movie" value="interactive.swf">
        </object>

        <h3>Fixed-Width Elements (Not Responsive)</h3>
        <div style="width: 1200px; height: 800px; background: #eee;">
            <p>This div has a fixed width of 1200px - won't work well on mobile!</p>
        </div>

        <table width="1000" border="1">
            <tr>
                <td width="800">Fixed width table cell</td>
            </tr>
        </table>

        <h3>Legacy Media Formats</h3>
        <p>These formats have poor mobile support:</p>
        <ul>
            <li><a href="video.flv">Flash Video (FLV)</a></li>
            <li><a href="presentation.wmv">Windows Media (WMV)</a></li>
        </ul>

        <h3>Large Images with Fixed Dimensions</h3>
        <img src="banner.jpg" width="2000" height="1000" alt="Very wide banner">
        """

        self.add_page_with_content(course_id, 'Mobile Issues Page', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def create_content_depth_course(self, category_id: int):
        """Course 7: Deep Content Nesting Test."""
        print("\n📝 Creating Course 7: Content Depth Test")

        course_id = self.create_course(
            'QATEST-DEPTH',
            'QA Test 7: Content Depth',
            category_id
        )

        # Deeply nested HTML structure
        content = """
        <h2>Deeply Nested Content Structure</h2>
        <p>This page tests content depth detection.</p>

        <div class="level-1">
            <h3>Level 1</h3>
            <div class="level-2">
                <h4>Level 2</h4>
                <div class="level-3">
                    <h5>Level 3</h5>
                    <div class="level-4">
                        <h6>Level 4</h6>
                        <div class="level-5">
                            <p>Level 5 content (exceeds typical depth threshold)</p>
                            <div class="level-6">
                                <p>Level 6 - very deeply nested!</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h3>Simulated SCORM/Book Module</h3>
        <p>Reference to deeply nested learning object:</p>
        <ul>
            <li>Module 1
                <ul>
                    <li>Chapter 1
                        <ul>
                            <li>Section 1.1
                                <ul>
                                    <li>Subsection 1.1.1
                                        <ul>
                                            <li>Content 1.1.1.1 (5 levels deep)</li>
                                        </ul>
                                    </li>
                                </ul>
                            </li>
                        </ul>
                    </li>
                </ul>
            </li>
        </ul>
        """

        self.add_page_with_content(course_id, 'Deep Nesting Page', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def create_comprehensive_course(self, category_id: int):
        """Course 8: Comprehensive test with multiple issues."""
        print("\n📝 Creating Course 8: Comprehensive Test")

        course_id = self.create_course(
            'QATEST-ALL',
            'QA Test 8: Comprehensive Issues',
            category_id
        )

        content = """
        <h2>Comprehensive QA Test Page</h2>
        <p>This page combines multiple QA issues.</p>

        <h3>Broken Links</h3>
        <a href="https://example.com/404">Broken link</a>

        <h3>Legacy Format</h3>
        <object data="old-content.swf"></object>

        <h3>Accessibility Issue</h3>
        <img src="chart.png">

        <h3>Mobile Issue</h3>
        <div style="width: 1500px;">Not responsive</div>

        <h3>Security Issue</h3>
        <a href="javascript:void(0)">JS link</a>

        <h3>Large File</h3>
        <a href="huge_archive_500mb.zip">Download (500MB)</a>
        """

        self.add_page_with_content(course_id, 'Comprehensive Test', content)
        print(f"   ✓ Created course (ID: {course_id})")

    def populate_all(self):
        """Create all test courses."""
        print("\n🚀 Moodle QA Test Data Population")
        print("=" * 50)

        # Get or create category
        print("\n📁 Setting up course category...")
        category_id = self.get_category_id()
        print(f"   ✓ Using category ID: {category_id}")

        # Delete existing test courses for idempotency
        self.delete_existing_test_courses()

        # Create all test courses
        try:
            self.create_broken_links_course(category_id)
            self.create_legacy_files_course(category_id)
            self.create_large_files_course(category_id)
            self.create_accessibility_course(category_id)
            self.create_malicious_code_course(category_id)
            self.create_mobile_issues_course(category_id)
            self.create_content_depth_course(category_id)
            self.create_comprehensive_course(category_id)

            print("\n" + "=" * 50)
            print("✅ Test data population complete!")
            print("\n📊 Created 8 test courses:")
            print("   1. QATEST-LINKS      - Broken links test")
            print("   2. QATEST-LEGACY     - Legacy file formats")
            print("   3. QATEST-LARGE      - Large files test")
            print("   4. QATEST-A11Y       - Accessibility issues")
            print("   5. QATEST-SECURITY   - Malicious code detection")
            print("   6. QATEST-MOBILE     - Mobile compatibility")
            print("   7. QATEST-DEPTH      - Content depth test")
            print("   8. QATEST-ALL        - Comprehensive test")
            print("\n🔍 Run the QA tool to see issues detected:")
            print("   python main.py")

        except Exception as e:
            print(f"\n❌ Error creating test courses: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(
        description='Populate Moodle with test data for QA tool testing',
        epilog="""
Required Web Services functions:
  - core_course_get_categories
  - core_course_create_categories
  - core_course_get_courses
  - core_course_create_courses
  - core_course_delete_courses
  - core_course_update_courses

Add these in: Site administration → Plugins → Web services → External services
        """
    )
    parser.add_argument(
        '--url',
        default='http://localhost:8080',
        help='Moodle URL (default: http://localhost:8080)'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Moodle Web Services token'
    )

    args = parser.parse_args()

    try:
        populator = MoodleTestDataPopulator(args.url, args.token)
        populator.populate_all()
        return 0
    except Exception as e:
        print(f"\n❌ Failed: {e}", file=sys.stderr)
        print("\nℹ️  Make sure these functions are added to your Web Service:", file=sys.stderr)
        print("   - core_course_get_categories", file=sys.stderr)
        print("   - core_course_create_categories", file=sys.stderr)
        print("   - core_course_get_courses", file=sys.stderr)
        print("   - core_course_create_courses", file=sys.stderr)
        print("   - core_course_delete_courses", file=sys.stderr)
        print("   - core_course_update_courses", file=sys.stderr)
        print("\nSee GETTING_STARTED.md Step 3.4 for instructions", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
