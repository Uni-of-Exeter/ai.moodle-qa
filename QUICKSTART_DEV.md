# Quick Start - Complete Dev Environment

Get a fully working Moodle QA environment in 5 minutes.

## Prerequisites

- Docker Desktop running
- Python 3.10+

## Step 1: Start Moodle (2 min)

```bash
./start-moodle.sh
```

Access: http://localhost:8080  
Login: `admin` / `Admin123!`

## Step 2: Enable Web Services (2 min)

Follow **DOCKER.md** sections 1-6:

1. Enable web services (Advanced features)
2. Enable REST protocol
3. Create service "QA Audit Service"
4. Add functions: `core_course_get_courses`, `core_course_get_contents`
5. Authorize admin user
6. Generate token → **Copy it!**

## Step 3: Complete Setup (1 min)

```bash
# Run complete setup with your token
./setup-complete-dev-env.sh YOUR_TOKEN_HERE
```

This will:
- ✅ Configure Python environment
- ✅ Install dependencies  
- ✅ Update main.py with token
- ✅ Create 8 test courses with QA issues
- ✅ Run test audit

## Step 4: Run QA Tool

```bash
python main.py --all
```

View reports in `moodle_qa_reports/`

---

## What You Get

- 8 test courses with intentional issues:
  - QATEST-LINKS (broken links)
  - QATEST-LEGACY (old file formats)
  - QATEST-LARGE (large files)
  - QATEST-A11Y (accessibility)
  - QATEST-SECURITY (malicious code)
  - QATEST-MOBILE (mobile issues)
  - QATEST-DEPTH (deep nesting)
  - QATEST-ALL (combined issues)

- All 8 QA checks will find problems
- Complete development environment
- Repeatable setup

---

## Manual Alternative

If you prefer manual setup:

```bash
# 1. Start Moodle
./start-moodle.sh

# 2. Setup Web Services (see DOCKER.md)
# ... follow steps in browser ...

# 3. Create venv and install deps
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Update main.py with your token
# Edit: MOODLE_URL and TOKEN

# 5. Populate test data
python populate_test_data.py --token YOUR_TOKEN

# 6. Run QA tool
python main.py
```

---

## Reset Everything

```bash
# Stop and delete all data
docker compose down -v

# Start fresh
./start-moodle.sh

# Re-run setup
./setup-complete-dev-env.sh YOUR_TOKEN
```

---

## Files

- `start-moodle.sh` - Start Docker Moodle
- `setup-complete-dev-env.sh` - Complete environment setup
- `populate_test_data.py` - Create test courses
- `main.py` - QA tool
- `DOCKER.md` - Full Docker documentation
- `TEST_DATA_REFERENCE.md` - Test course details
