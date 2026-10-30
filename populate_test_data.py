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
        """Course 1: Broken Links Test - Mix of working and broken links."""
        print("\n📝 Creating Course 1: Broken Links Test")

        course_id = self.create_course(
            'QATEST-LINKS',
            'QA Test 1: Broken Links',
            category_id
        )

        # Content with BOTH working and broken links
        content = """
        <h2>Link Testing Page</h2>
        <p>This page contains both working and broken links to test detection.</p>

        <h3>✅ Working Links (Should Pass)</h3>
        <ul>
            <li><a href="https://www.moodle.org">Moodle.org</a> - Valid link</li>
            <li><a href="https://www.google.com">Google</a> - Valid link</li>
            <li><a href="https://httpstat.us/200">HTTP 200 OK</a> - Valid status</li>
        </ul>

        <h3>❌ Broken Links (Should Fail)</h3>
        <ul>
            <li><a href="https://example.com/does-not-exist-404">Broken link (404)</a></li>
            <li><a href="http://this-domain-definitely-does-not-exist-12345.com">Broken domain</a></li>
            <li><a href="https://httpstat.us/500">Server error link (500)</a></li>
        </ul>

        <h3>✅ Working Images (Should Pass)</h3>
        <img src="https://via.placeholder.com/150" alt="Valid placeholder image">

        <h3>❌ Broken Images (Should Fail)</h3>
        <img src="https://example.com/missing-image-404.jpg" alt="This image is missing">
        <img src="http://broken-domain.example/logo.png" alt="Another broken image">

        <h3>❌ Broken Media (Should Fail)</h3>
        <video src="https://example.com/missing-video.mp4" controls></video>

        <p><strong>Expected Results:</strong> 3 working links pass, 5+ broken links/images/media fail</p>
        """

        self.add_page_with_content(course_id, 'Mixed Link Test Page', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: 3 passing links, 5+ failing links")

    def create_legacy_files_course(self, category_id: int):
        """Course 2: Legacy File Types Test - Mix of modern and legacy formats."""
        print("\n📝 Creating Course 2: Legacy File Types Test")

        course_id = self.create_course(
            'QATEST-LEGACY',
            'QA Test 2: Legacy File Types',
            category_id
        )

        # Content with BOTH modern and legacy file types
        content = """
        <h2>File Format Testing</h2>
        <p>This course has both modern and legacy media formats.</p>

        <h3>✅ Modern Formats (Should Pass)</h3>
        <ul>
            <li><a href="lecture.mp4">MP4 video file</a> - Modern format ✓</li>
            <li><a href="presentation.pdf">PDF document</a> - Standard format ✓</li>
            <li><a href="slides.pptx">PowerPoint (PPTX)</a> - Modern format ✓</li>
            <li><a href="document.docx">Word document (DOCX)</a> - Modern format ✓</li>
        </ul>

        <h3>❌ Legacy Formats (Should Fail)</h3>
        <p><strong>Flash Content:</strong></p>
        <object data="animation.swf" type="application/x-shockwave-flash"></object>
        <embed src="game.swf" type="application/x-shockwave-flash"></embed>

        <p><strong>Legacy Video Formats:</strong></p>
        <ul>
            <li><a href="training_video.flv">FLV video file</a> - Legacy ❌</li>
            <li><a href="presentation.wmv">WMV video file</a> - Legacy ❌</li>
            <li><a href="demo.avi">AVI video file</a> - Legacy ❌</li>
            <li><a href="legacy_recording.rm">RealMedia file</a> - Legacy ❌</li>
        </ul>

        <video src="old_lecture.flv" controls></video>

        <p><strong>Expected Results:</strong> 4 modern formats pass, 6 legacy formats fail</p>
        """

        self.add_page_with_content(course_id, 'Mixed Format Page', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: 4 modern formats pass, 6 legacy formats fail")

    def create_large_files_course(self, category_id: int):
        """Course 3: Large Files Test - Mix of reasonable and large files."""
        print("\n📝 Creating Course 3: Large Files Test")

        course_id = self.create_course(
            'QATEST-LARGE',
            'QA Test 3: Large Files',
            category_id
        )

        content = """
        <h2>File Size Testing</h2>
        <p>This course has files of varying sizes to test threshold detection.</p>

        <h3>✅ Reasonable File Sizes (Should Pass)</h3>
        <p>These files are under the 50MB threshold:</p>
        <ul>
            <li><a href="lecture_slides.pdf">Lecture Slides (2.5MB)</a></li>
            <li><a href="tutorial_video.mp4">Tutorial Video (15MB)</a></li>
            <li><a href="worksheet.docx">Worksheet (1.2MB)</a></li>
            <li><a href="sample_data.csv">Sample Data (8MB)</a></li>
        </ul>

        <h3>❌ Large Files (Should Fail)</h3>
        <p>These files exceed the 50MB threshold:</p>
        <ul>
            <li><a href="full_course_video_1080p_uncompressed.mp4">4K Course Video (120MB)</a></li>
            <li><a href="dataset_archive_full.zip">Complete Dataset (250MB)</a></li>
            <li><a href="high_res_images_pack.zip">High-Res Image Pack (85MB)</a></li>
            <li><a href="software_installer_v2.exe">Software Package (150MB)</a></li>
            <li><a href="research_data_backup.tar.gz">Research Backup (180MB)</a></li>
        </ul>

        <p><strong>Note:</strong> File sizes are simulated references for testing.</p>
        <p><strong>Expected Results:</strong> 4 reasonable files pass, 5 large files fail</p>
        """

        self.add_page_with_content(course_id, 'Mixed File Size Page', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: 4 small files pass, 5 large files fail")

    def create_accessibility_course(self, category_id: int):
        """Course 4: Accessibility Issues Test - Mix of good and bad accessibility."""
        print("\n📝 Creating Course 4: Accessibility Issues Test")

        course_id = self.create_course(
            'QATEST-A11Y',
            'QA Test 4: Accessibility Issues',
            category_id
        )

        # Content with BOTH good and bad accessibility
        content = """
        <h2>Accessibility Testing Page</h2>

        <h3>✅ Images With Alt Text (Should Pass)</h3>
        <img src="diagram.png" alt="System architecture diagram showing database and web server">
        <img src="chart.jpg" alt="Bar chart comparing Q1 vs Q2 sales figures">

        <h3>❌ Images Without Alt Text (Should Fail)</h3>
        <img src="infographic.png">
        <img src="missing-alt.jpg">
        <img src="no-description.png" alt="">

        <h3>✅ Good Links (Should Pass)</h3>
        <p>Click <a href="next.html">here to continue</a> to the next page.</p>
        <p>More info: <a href="info.html">detailed information page</a></p>

        <h3>❌ Empty Links (Should Fail)</h3>
        <p>Click <a href="empty.html"></a> here.</p>
        <p>More: <a href="whitespace.html">   </a></p>

        <h3>✅ Table With Headers (Should Pass)</h3>
        <table border="1">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Score</th>
                    <th>Grade</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Alice</td>
                    <td>95</td>
                    <td>A</td>
                </tr>
            </tbody>
        </table>

        <h3>❌ Table Without Headers (Should Fail)</h3>
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
        </table>

        <h3>✅ Proper Heading Hierarchy (Should Pass)</h3>
        <h2>Main Section</h2>
        <h3>Subsection</h3>
        <h4>Detail Level</h4>

        <h3>❌ Skipped Heading Levels (Should Fail)</h3>
        <h2>Section Title</h2>
        <h5>Subsection (skipped h3 and h4)</h5>

        <p><strong>Expected Results:</strong> ~7 accessibility passes, ~7 failures</p>
        """

        self.add_page_with_content(course_id, 'Mixed Accessibility Page', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: ~7 passes, ~7 failures")

    def create_malicious_code_course(self, category_id: int):
        """Course 5: Malicious Code Detection Test - Mix of safe and suspicious code."""
        print("\n📝 Creating Course 5: Malicious Code Test")

        course_id = self.create_course(
            'QATEST-SECURITY',
            'QA Test 5: Malicious Code Detection',
            category_id
        )

        # Content with BOTH safe and suspicious patterns
        content = """
        <h2>Security Testing Page</h2>
        <p><strong>Note:</strong> This page tests code pattern detection.</p>

        <h3>✅ Safe Links (Should Pass)</h3>
        <a href="https://www.moodle.org">Moodle website</a>
        <a href="/course/view.php?id=1">Internal course link</a>
        <a href="mailto:admin@example.com">Email link</a>

        <h3>❌ JavaScript URIs (Should Fail)</h3>
        <a href="javascript:void(0)">JavaScript link</a>
        <a href="javascript:alert('click')">Another JS link</a>

        <h3>✅ Safe Event Handling (Should Pass)</h3>
        <button>Safe Button</button>
        <div class="content">Safe div with class</div>

        <h3>❌ Inline Event Handlers (Should Fail)</h3>
        <button onclick="alert('clicked')">Click Me</button>
        <div onload="runCode()">Auto-loading div</div>
        <img src="test.jpg" onerror="handleError()">

        <h3>✅ Safe Code Examples (Should Pass)</h3>
        <p>Example: <code>function calculate() { return x + y; }</code></p>
        <p>Example: <code>const data = fetchData();</code></p>

        <h3>❌ Suspicious Code (Should Fail)</h3>
        <p>Dangerous: <code>eval(userInput)</code></p>
        <p>Dangerous: <code>document.cookie</code></p>

        <h3>✅ Embedded Video (Should Pass)</h3>
        <video src="lecture.mp4" controls></video>

        <h3>❌ External iframe (Should Fail)</h3>
        <iframe src="https://external-site.com/embed"></iframe>

        <p><strong>Expected Results:</strong> ~5 safe patterns pass, ~6 suspicious patterns fail</p>
        """

        self.add_page_with_content(course_id, 'Mixed Security Test Page', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: ~5 safe passes, ~6 suspicious fails")

    def create_mobile_issues_course(self, category_id: int):
        """Course 6: Mobile Compatibility Issues Test - Mix of responsive and fixed content."""
        print("\n📝 Creating Course 6: Mobile Compatibility Test")

        course_id = self.create_course(
            'QATEST-MOBILE',
            'QA Test 6: Mobile Compatibility',
            category_id
        )

        content = """
        <h2>Mobile Compatibility Testing</h2>

        <h3>✅ Mobile-Friendly Content (Should Pass)</h3>
        <p>Responsive text content that adapts to screen size.</p>
        <div style="max-width: 100%; padding: 10px;">
            <p>This div uses max-width: 100% - mobile friendly!</p>
        </div>

        <h3>✅ Responsive Media (Should Pass)</h3>
        <video src="lecture.mp4" controls style="max-width: 100%;"></video>
        <img src="diagram.jpg" alt="Diagram" style="max-width: 100%; height: auto;">

        <h3>❌ Flash Content (Should Fail)</h3>
        <object data="interactive.swf" type="application/x-shockwave-flash" width="800" height="600">
            <param name="movie" value="interactive.swf">
        </object>

        <h3>❌ Fixed-Width Elements (Should Fail)</h3>
        <div style="width: 1200px; height: 800px; background: #eee;">
            <p>This div has a fixed width of 1200px - not responsive!</p>
        </div>

        <table width="1000" border="1">
            <tr>
                <td width="800">Fixed width table cell</td>
            </tr>
        </table>

        <h3>✅ Modern Formats (Should Pass)</h3>
        <ul>
            <li><a href="video.mp4">MP4 video</a> - mobile compatible</li>
            <li><a href="presentation.pdf">PDF document</a> - mobile compatible</li>
        </ul>

        <h3>❌ Legacy Formats (Should Fail)</h3>
        <ul>
            <li><a href="video.flv">Flash Video (FLV)</a></li>
            <li><a href="presentation.wmv">Windows Media (WMV)</a></li>
        </ul>

        <h3>❌ Fixed Dimension Images (Should Fail)</h3>
        <img src="banner.jpg" width="2000" height="1000" alt="Very wide banner">

        <p><strong>Expected Results:</strong> ~4 mobile-friendly passes, ~5 issues fail</p>
        """

        self.add_page_with_content(course_id, 'Mixed Mobile Test Page', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: ~4 responsive passes, ~5 mobile issues fail")

    def create_content_depth_course(self, category_id: int):
        """Course 7: Deep Content Nesting Test - Mix of shallow and deep nesting."""
        print("\n📝 Creating Course 7: Content Depth Test")

        course_id = self.create_course(
            'QATEST-DEPTH',
            'QA Test 7: Content Depth',
            category_id
        )

        # Mix of reasonable and deeply nested structures
        content = """
        <h2>Content Depth Testing</h2>
        <p>This page tests content depth detection with mixed nesting levels.</p>

        <h3>✅ Reasonable Nesting (Should Pass)</h3>
        <div class="section">
            <h4>Section Title</h4>
            <div class="content">
                <p>Content at level 2 - acceptable depth</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
        </div>

        <h3>✅ Simple Lists (Should Pass)</h3>
        <ul>
            <li>Level 1
                <ul>
                    <li>Level 2
                        <ul>
                            <li>Level 3 (reasonable depth)</li>
                        </ul>
                    </li>
                </ul>
            </li>
        </ul>

        <h3>❌ Excessive Nesting (Should Fail)</h3>
        <div class="level-1">
            <h4>Level 1</h4>
            <div class="level-2">
                <h5>Level 2</h5>
                <div class="level-3">
                    <h6>Level 3</h6>
                    <div class="level-4">
                        <p>Level 4</p>
                        <div class="level-5">
                            <p>Level 5 (exceeds threshold)</p>
                            <div class="level-6">
                                <p>Level 6 - very deeply nested!</p>
                                <div class="level-7">
                                    <p>Level 7 - excessive!</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h3>❌ Deeply Nested Lists (Should Fail)</h3>
        <ul>
            <li>Module 1
                <ul>
                    <li>Chapter 1
                        <ul>
                            <li>Section 1.1
                                <ul>
                                    <li>Subsection 1.1.1
                                        <ul>
                                            <li>Sub-subsection 1.1.1.1
                                                <ul>
                                                    <li>Content (6 levels - too deep!)</li>
                                                </ul>
                                            </li>
                                        </ul>
                                    </li>
                                </ul>
                            </li>
                        </ul>
                    </li>
                </ul>
            </li>
        </ul>

        <p><strong>Expected Results:</strong> ~2 shallow structures pass, ~2 deep structures fail</p>
        """

        self.add_page_with_content(course_id, 'Mixed Depth Page', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: ~2 shallow passes, ~2 deep nesting fails")

    def create_comprehensive_course(self, category_id: int):
        """Course 8: Comprehensive test with mixed good and bad examples across all dimensions."""
        print("\n📝 Creating Course 8: Comprehensive Test")

        course_id = self.create_course(
            'QATEST-ALL',
            'QA Test 8: Comprehensive Issues',
            category_id
        )

        content = """
        <h2>Comprehensive QA Test Page</h2>
        <p>This page combines multiple QA checks with both passing and failing examples.</p>

        <h3>Links</h3>
        <p>✅ <a href="https://www.moodle.org">Working link</a></p>
        <p>❌ <a href="https://example.com/404">Broken link</a></p>

        <h3>File Formats</h3>
        <p>✅ <a href="document.pdf">Modern PDF</a></p>
        <p>❌ <object data="old-content.swf"></object></p>

        <h3>File Sizes</h3>
        <p>✅ <a href="presentation.pdf">Small file (5MB)</a></p>
        <p>❌ <a href="huge_archive_500mb.zip">Large download (500MB)</a></p>

        <h3>Accessibility</h3>
        <p>✅ <img src="diagram.jpg" alt="System diagram"></p>
        <p>❌ <img src="chart.png"></p>

        <h3>Mobile Compatibility</h3>
        <p>✅ <video src="lecture.mp4" controls style="max-width:100%;"></video></p>
        <p>❌ <div style="width: 1500px;">Not responsive</div></p>

        <h3>Security</h3>
        <p>✅ <a href="/course/view.php?id=1">Safe link</a></p>
        <p>❌ <a href="javascript:void(0)">JS link</a></p>

        <h3>Content Depth</h3>
        <div class="ok">
            <p>✅ Shallow nesting (OK)</p>
        </div>
        <div><div><div><div><div>
            <p>❌ Deep nesting (Too deep)</p>
        </div></div></div></div></div>

        <p><strong>Expected Results:</strong> ~7 checks with mixed pass/fail results</p>
        """

        self.add_page_with_content(course_id, 'Comprehensive Mixed Test', content)
        print(f"   ✓ Created course (ID: {course_id})")
        print(f"      Expected: Multiple checks, both passes and failures")

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
