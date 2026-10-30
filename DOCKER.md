# Docker Moodle Setup

Quick setup for local Moodle testing.

## Quick Start

```bash
# 1. Start Moodle
./start-moodle.sh

# 2. Access Moodle
open http://localhost:8080
```

**Login:** `admin` / `Admin123!`

---

## Enable Web Services (Required for QA Tool)

### 1. Enable Web Services
- **Site administration → Advanced features**
- Check ✅ **Enable web services** → Save

### 2. Enable REST Protocol
- **Site administration → Plugins → Web services → Manage protocols**
- Enable **REST protocol**

### 3. Create Service
- **Site administration → Plugins → Web services → External services**
- Click **Add**
  - Name: `QA Audit Service`
  - Short name: `qa_audit`
  - Enabled: ✅
  - Authorized users only: ✅
- Click **Add service**

### 4. Add Functions
- Click **Functions** next to service
- Add minimum (for QA tool):
  - `core_course_get_courses`
  - `core_course_get_contents`
- Add optional (for test data):
  - `core_course_get_categories`
  - `core_course_create_categories`
  - `core_course_create_courses`
  - `core_course_delete_courses`
  - `core_course_update_courses`

### 5. Authorize User
- Click **Authorised users** next to service
- Add **Admin User**

### 6. Generate Token
- **Site administration → Plugins → Web services → Manage tokens**
- Click **Add**
  - User: **Admin User**
  - Service: **QA Audit Service**
- **Copy the token!**

---

## Configure & Test QA Tool

### 1. Configure Connection

Edit `main.py`:

```python
MOODLE_URL = "http://localhost:8080"
TOKEN = "your_token_here"
```

### 2. Populate Test Data (Optional)

Create test courses with intentional QA issues:

```bash
# Activate Python environment
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Run population script
python populate_test_data.py --token your_token_here
```

This creates 8 test courses covering all QA checks:
- Broken links
- Legacy file formats
- Large files
- Accessibility issues
- Malicious code
- Mobile compatibility issues
- Deep content nesting
- Comprehensive test

**Idempotent:** Safe to run multiple times - deletes and recreates test courses.

### 3. Run QA Tool

```bash
python main.py
```

---

## Docker Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker logs moodle-app -f

# Reset (deletes all data)
docker compose down -v
```

---

## Database Access

```bash
# MySQL CLI
docker exec -it moodle-db mysql -u moodle -pmoodle_password moodle

# Or as root
docker exec -it moodle-db mysql -u root -proot_password
```

**Credentials:**
- Host: `db` (from container) or `localhost:3306` (from host)
- Database: `moodle`
- User: `moodle`
- Password: `moodle_password`
- Root Password: `root_password`

---

## Troubleshooting

**Can't login?**
```bash
docker exec moodle-app php /var/www/html/admin/cli/reset_password.php \
  --username=admin --password=Admin123! --ignore-password-policy
```

**Start fresh?**
```bash
docker compose down -v
./start-moodle.sh
```

**Check status:**
```bash
docker compose ps
docker logs moodle-app
```
