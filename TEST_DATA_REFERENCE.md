# Test Data Reference

## Overview

The `populate_test_data.py` script creates 8 test courses, each designed to trigger specific QA checks.

## Test Courses

### 1. QATEST-LINKS - Broken Links Test
**Triggers:** Broken Links Check

**Content:**
- ✅ 3 working links (moodle.org, google.com, httpstat 200)
- ✅ 1 working image
- ❌ 3 broken links (404, broken domain, 500 error)
- ❌ 2 broken image references
- ❌ 1 broken video source

**Expected Results:**
- 3 working links pass
- 6+ broken links/images/media fail
- HTTP error codes captured
- Mix of failure types detected

---

### 2. QATEST-LEGACY - Legacy File Types
**Triggers:** Content & File Types Check

**Content:**
- ✅ 4 modern formats (MP4, PDF, PPTX, DOCX)
- ❌ Flash/SWF content (2 instances)
- ❌ FLV video format
- ❌ WMV video format
- ❌ AVI video format
- ❌ RealMedia (`.rm`) file

**Expected Results:**
- 4 modern formats pass
- 6 legacy formats fail
- Flash objects detected
- Legacy video formats reported

---

### 3. QATEST-LARGE - Large Files
**Triggers:** File Sizes Check

**Issues:**
- Simulated references to files >50MB:
  - 120MB video file
  - 250MB dataset
  - 85MB image pack
  - 150MB software installer

**Expected Results:**
- Files exceeding threshold flagged
- Size estimates captured

**Note:** These are references only - actual large files aren't uploaded to save space.

---

### 4. QATEST-A11Y - Accessibility Issues
**Triggers:** Accessibility & Captions Check

**Issues:**
- Images without alt text (3 instances)
- Empty links (2 instances)
- Tables without header tags
- Skipped heading levels (h2 → h5)
- Videos without caption files

**Expected Results:**
- Missing alt attributes detected
- Empty/whitespace-only links found
- Table accessibility issues reported
- Heading hierarchy violations flagged
- Missing caption files noted

---

### 5. QATEST-SECURITY - Malicious Code Detection
**Triggers:** Malicious Code Detection Check

**Issues:**
- `<script>` tags in content
- `javascript:` URIs in links
- Inline event handlers (`onclick`, `onload`, `onerror`)
- `eval()` usage
- `document.cookie` references
- Embedded iframes

**Expected Results:**
- All suspicious patterns detected
- Script tags flagged
- JavaScript URIs identified
- Inline handlers caught
- iframe embeds noted

---

### 6. QATEST-MOBILE - Mobile Compatibility
**Triggers:** Mobile-Ready Content Check

**Issues:**
- Flash/SWF objects
- Fixed-width elements (1200px, 1000px, 2000px)
- Non-responsive tables
- Legacy video formats (FLV, WMV)
- Images with fixed large dimensions

**Expected Results:**
- Flash content flagged
- Fixed-width elements detected
- Non-responsive design issues reported
- Legacy format warnings

---

### 7. QATEST-DEPTH - Content Depth
**Triggers:** Content Layering / Depth Check

**Issues:**
- Deeply nested div structure (6+ levels)
- Complex nested lists (5+ levels)
- Simulated deep SCORM/Book module hierarchy

**Expected Results:**
- Depth violations reported
- Nesting level captured
- Structural complexity flagged

---

### 8. QATEST-ALL - Comprehensive Test
**Triggers:** Multiple QA Checks

**Issues:**
- Combination of issues from all categories:
  - Broken link
  - Legacy format (SWF)
  - Large file reference
  - Missing alt text
  - Fixed-width element
  - JavaScript URI

**Expected Results:**
- Multiple check types triggered
- Various issue categories in one course
- Comprehensive report

---

## Running the Tests

### Populate Test Data

```bash
# Make sure Moodle is running and you have a token
python populate_test_data.py --token YOUR_TOKEN
```

**Features:**
- ✅ **Idempotent** - Safe to run multiple times
- ✅ **Clean** - Deletes existing QATEST-* courses first
- ✅ **Fast** - Creates all 8 courses in ~10 seconds

### Run QA Tool

```bash
# Audit all courses (including test courses)
python main.py

# With detailed CSV output
python main.py --csv-detailed

# With all output formats
python main.py --all
```

### Expected Output

You should see issues detected across all 8 QA dimensions:

```
Auditing: QA Test 1: Broken Links (id=2)
  ✗ Broken Links: 7 issues found
  ✓ Content & File Types: OK
  ...

Auditing: QA Test 2: Legacy File Types (id=3)
  ✓ Broken Links: OK
  ✗ Content & File Types: 5 legacy formats found
  ...
```

---

## Verification Checklist

After running the QA tool on test data:

- [ ] Course 1: Broken links detected
- [ ] Course 2: Legacy formats flagged
- [ ] Course 3: Large files identified
- [ ] Course 4: Accessibility issues found
- [ ] Course 5: Malicious code detected
- [ ] Course 6: Mobile issues reported
- [ ] Course 7: Content depth violations
- [ ] Course 8: Multiple issues in one course

---

## Resetting Test Data

```bash
# Delete and recreate all test courses
python populate_test_data.py --token YOUR_TOKEN

# Or manually delete from Moodle:
# Site administration → Courses → Manage courses and categories
# Delete all courses starting with "QATEST-"
```

---

## Adding Custom Test Cases

To add your own test scenarios, edit `populate_test_data.py`:

```python
def create_my_custom_test(self, category_id: int):
    """My custom test case."""
    course_id = self.create_course(
        'QATEST-CUSTOM',
        'My Custom Test',
        category_id
    )

    content = """
    <h2>My Test Content</h2>
    <!-- Add your test HTML here -->
    """

    self.add_page_with_content(course_id, 'Test Page', content)
```

Then call it in `populate_all()`:

```python
def populate_all(self):
    # ... existing courses ...
    self.create_my_custom_test(category_id)
```

---

## Troubleshooting

**Script fails with "API Error"**
- Check your token is valid
- Verify Web Services are enabled
- Confirm required functions are added to service

**No issues detected in test courses**
- Verify courses were created (check Moodle UI)
- Check course IDs in script output
- Review main.py configuration
- Check audit thresholds in AuditConfig

**Courses not deleted on re-run**
- Script requires `core_course_delete_courses` function
- Add function to Web Service or delete manually

---

## Integration with CI/CD

Use test data population in your CI pipeline:

```bash
#!/bin/bash
# ci-test.sh

# Start Moodle
./start-moodle.sh

# Wait for ready
sleep 30

# Get token (from env or vault)
TOKEN="${MOODLE_TOKEN}"

# Populate test data
python populate_test_data.py --token "$TOKEN"

# Run QA tool
python main.py --all

# Check for critical issues
python -c "
import json
with open('moodle_qa_reports/audit_report_*.json') as f:
    report = json.load(f)
    if report['summary']['critical_issues'] > 0:
        exit(1)
"
```

---

## Notes

- Test courses are visible to all users (visibility: 1)
- Created in "QA Test Courses" category
- All have shortname starting with "QATEST-"
- Content is HTML-based (no actual file uploads)
- Safe for production use (no real security issues created)
