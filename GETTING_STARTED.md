# Getting Started - Fresh Clone Setup

Complete guide for setting up the Moodle QA tool from a fresh repository clone.

---

## Prerequisites

- **Docker Desktop** installed and running
- **Python 3.10+** installed
- **Git** installed

---

## Quick Setup (5 minutes)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd moodle-qa
```

### Step 2: Start Moodle

```bash
./start-moodle.sh
```

Wait for:
```
✅ Moodle is ready!

📍 http://localhost:8080
🔐 admin / Admin123!
```

**Access Moodle:** http://localhost:8080  
**Login:** `admin` / `Admin123!`

### Step 3: Enable Web Services (in browser)

Follow these steps in Moodle:

#### 3.1 Enable Web Services
1. Go to **Site administration** → **Advanced features**
2. Check ✅ **Enable web services**
3. Click **Save changes**

#### 3.2 Enable REST Protocol
1. Go to **Site administration** → **Plugins** → **Web services** → **Manage protocols**
2. Click **Enable** next to **REST protocol**

#### 3.3 Create External Service
1. Go to **Site administration** → **Plugins** → **Web services** → **External services**
2. Click **Add** under "Custom services"
3. Enter:
   - **Name:** `QA Audit Service`
   - **Short name:** `qa_audit`
   - **Enabled:** ✅ checked
   - **Authorized users only:** ✅ checked
4. Click **Add service**

#### 3.4 Add Functions
1. Click **Functions** next to "QA Audit Service"
2. Click **Add functions**
3. Search and add these functions:

   **Required (for QA tool):**
   - `core_course_get_courses`
   - `core_course_get_contents`

   **Optional (for test data population):**
   - `core_course_get_categories`
   - `core_course_create_categories`
   - `core_course_create_courses`
   - `core_course_delete_courses`
   - `core_course_update_courses`

4. Click **Add functions**

**Note:** 
- You only need the first 2 for running the QA tool
- Add all 7 if you want to auto-populate test data
- You can skip test data population and create courses manually

#### 3.5 Authorize User
1. Go back to **External services**
2. Click **Authorised users** next to "QA Audit Service"
3. Select **Admin User** from dropdown
4. Click **Add**

#### 3.6 Generate Token
1. Go to **Site administration** → **Plugins** → **Web services** → **Manage tokens**
2. Click **Add**
3. Select:
   - **User:** Admin User
   - **Service:** QA Audit Service
4. Click **Save changes**
5. **COPY THE TOKEN** (looks like: `a1b2c3d4e5f6...`)

### Step 4: Complete Setup

Run the automated setup with your token:

```bash
./setup-complete-dev-env.sh YOUR_TOKEN_HERE
```

This will:
- ✅ Create Python virtual environment
- ✅ Install dependencies
- ✅ Configure `main.py` with token
- ✅ Create 8 test courses with QA issues
- ✅ Run test audit

### Step 5: Run QA Tool

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run audit
python main.py

# Run with all output formats
python main.py --all
```

**View reports:** `moodle_qa_reports/`

---

## Manual Setup (Alternative)

If you prefer manual control over each step:

### 1. Clone & Start Moodle

```bash
git clone <repository-url>
cd moodle-qa
./start-moodle.sh
```

### 2. Setup Web Services

Follow Step 3 above (in browser) → get token

### 3. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Connection

Edit `main.py` (near top of file):

```python
# ─── Connection ───────────────────────────────
MOODLE_URL = "http://localhost:8080"
TOKEN = "your_token_here"  # Paste your token
```

### 5. Populate Test Data (Optional)

```bash
python populate_test_data.py --token YOUR_TOKEN
```

Creates 8 test courses with intentional QA issues.

### 6. Run QA Tool

```bash
python main.py
```

---

## What You Get

After setup, you'll have:

### Test Courses (if populated)
8 courses with intentional issues to test all QA checks:

| Course | Issues |
|--------|--------|
| QATEST-LINKS | Broken links, missing images |
| QATEST-LEGACY | Flash, FLV, WMV files |
| QATEST-LARGE | Large file references |
| QATEST-A11Y | Missing alt text, bad tables |
| QATEST-SECURITY | Scripts, JS URIs |
| QATEST-MOBILE | Fixed widths, Flash |
| QATEST-DEPTH | Deep nesting (6+ levels) |
| QATEST-ALL | Multiple issues |

### QA Tool Ready
Run against any Moodle instance (local or remote)

---

## Directory Structure

```
moodle-qa/
├── main.py                      # QA tool entry point
├── src/                         # Core modules
│   ├── models.py               # Data models
│   ├── moodle_client.py        # API client
│   ├── checks.py               # QA checks
│   ├── reporters.py            # Output formats
│   └── engine.py               # Audit orchestrator
├── tests/                       # Test suite
├── docker-compose.yml           # Docker setup
├── start-moodle.sh             # Start script
├── populate_test_data.py       # Test data generator
├── setup-complete-dev-env.sh   # Automated setup
├── requirements.txt            # Python dependencies
└── moodle_qa_reports/          # Output directory (created)
```

---

## Configuration Options

Edit `main.py` to customize:

```python
audit_config = AuditConfig(
    max_file_size_mb=50.0,           # File size threshold
    link_timeout_seconds=10,          # Link check timeout
    max_acceptable_depth=4,           # Content depth limit
    delay_between_courses=1.0,        # Rate limiting
    delay_between_requests=0.2,       # HTTP throttling
    only_visible_courses=True,        # Skip hidden courses
    exclude_course_ids=frozenset({1}),# Skip course IDs
    category_id=None,                 # Limit to category
)
```

---

## Common Commands

```bash
# Start Moodle
./start-moodle.sh

# Stop Moodle (keep data)
docker compose down

# Stop & delete all data
docker compose down -v

# View logs
docker logs moodle-app -f

# Populate test data
python populate_test_data.py --token TOKEN

# Run QA tool (various formats)
python main.py                    # Console + JSON
python main.py --csv              # Add CSV summary
python main.py --csv-detailed     # Add detailed CSV
python main.py --all              # All formats

# Email report
python main.py --email admin@example.com

# Run tests
pytest
pytest --cov=src
```

---

## Troubleshooting

### Docker won't start
```bash
# Check Docker is running
docker info

# Restart Docker Desktop
# macOS: Menu bar icon → Restart

# Try again
./start-moodle.sh
```

### Can't access Moodle
```bash
# Check containers
docker compose ps

# View logs
docker logs moodle-app -f

# Wait 2 minutes for first startup
# Then: open http://localhost:8080
```

### Can't login to Moodle
```bash
# Reset admin password
docker exec moodle-app php /var/www/html/admin/cli/reset_password.php \
  --username=admin --password=Admin123! --ignore-password-policy
```

### QA tool can't connect
1. Check Moodle is accessible: http://localhost:8080
2. Verify Web Services enabled (Advanced features)
3. Verify REST protocol enabled
4. Check token is correct in `main.py`
5. Test token manually:
   ```bash
   curl "http://localhost:8080/webservice/rest/server.php?wstoken=YOUR_TOKEN&wsfunction=core_webservice_get_site_info&moodlewsrestformat=json"
   ```

### Test data population fails

**See:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md#test-data-population-fails)

Quick fix:
1. Verify ALL 7 functions added to service (see Step 3.4 above)
2. Re-run: `python populate_test_data.py --token YOUR_TOKEN`
3. Or skip and create courses manually

The setup script continues even if this fails, so you can still use the QA tool.

### Start fresh
```bash
# Delete everything
docker compose down -v

# Remove Python environment
rm -rf venv

# Start over
./start-moodle.sh
# ... follow setup steps ...
```

---

## Next Steps

### For Development
- Read **[TEST_DATA_REFERENCE.md](TEST_DATA_REFERENCE.md)** - test course details
- Run test suite: `pytest`
- Check code coverage: `pytest --cov=src`

### For Production Use
1. Update `main.py` with production Moodle URL
2. Generate token on production instance
3. Configure audit thresholds for your needs
4. Set up email reporting (SMTP credentials)
5. Schedule via cron for regular audits

### For Customization
- Add new QA checks in `src/checks.py`
- Add output formats in `src/reporters.py`
- Extend test data in `populate_test_data.py`

---

## Documentation

- **[README.md](README.md)** - Project overview & features
- **[DOCKER.md](DOCKER.md)** - Docker details & commands
- **[QUICKSTART_DEV.md](QUICKSTART_DEV.md)** - Quick reference
- **[TEST_DATA_REFERENCE.md](TEST_DATA_REFERENCE.md)** - Test courses explained
- **This file** - Complete setup guide

---

## Support

**Issues?**
1. Check troubleshooting section above
2. Review relevant documentation
3. Check Docker/Moodle logs
4. Verify Web Services configuration

**Working?**
- Create courses and run audits
- Experiment with different output formats
- Test on production Moodle (read-only operations)

---

## Summary

```bash
# Complete workflow from fresh clone:

git clone <repo>                              # 1. Clone
cd moodle-qa                                  # 2. Enter
./start-moodle.sh                             # 3. Start (2 min)
# ... setup Web Services in browser ...       # 4. Web Services (2 min)
./setup-complete-dev-env.sh YOUR_TOKEN        # 5. Setup (1 min)
python main.py --all                          # 6. Run!

# Total time: ~5 minutes
```

You're ready! 🚀
