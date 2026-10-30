# Web Services Functions Reference

Quick reference for Moodle Web Services functions needed by this project.

---

## For QA Tool Only (Minimum)

Add these 2 functions to run the QA tool:

```
core_course_get_courses     - List all courses
core_course_get_contents    - Get course content
```

### How to Add

1. **Site administration** → **Plugins** → **Web services** → **External services**
2. Click **Functions** next to "QA Audit Service"
3. Click **Add functions**
4. Search and add each function
5. Click **Add functions**

---

## For Test Data Population (Full)

Add these 7 functions to auto-populate test courses:

```
core_course_get_courses          - List courses
core_course_get_contents         - Get course content
core_course_get_categories       - List categories
core_course_create_categories    - Create category
core_course_create_courses       - Create courses
core_course_delete_courses       - Delete courses (for cleanup)
core_course_update_courses       - Update course content
```

---

## What Each Function Does

| Function | Used By | Purpose |
|----------|---------|---------|
| `core_course_get_courses` | QA tool, populate script | List all courses |
| `core_course_get_contents` | QA tool | Get course modules and content |
| `core_course_get_categories` | populate script | Find or check category |
| `core_course_create_categories` | populate script | Create "QA Test Courses" category |
| `core_course_create_courses` | populate script | Create test courses |
| `core_course_delete_courses` | populate script | Delete old test courses (idempotent) |
| `core_course_update_courses` | populate script | Add content to courses |

---

## Setup Steps

### Minimal Setup (QA Tool Only)

**Functions needed:** 2

1. Go to External services
2. Add to "QA Audit Service":
   - `core_course_get_courses`
   - `core_course_get_contents`
3. Done! Can run: `python main.py`

### Full Setup (QA Tool + Test Data)

**Functions needed:** 7 (all of the above)

1. Go to External services
2. Add all 7 functions listed above
3. Done! Can run: `./setup-complete-dev-env.sh TOKEN`

---

## Checking What's Added

### Via Web UI

1. **Site administration** → **Plugins** → **Web services** → **External services**
2. Look at "QA Audit Service"
3. Click **Functions**
4. See list of added functions

### Via API

```bash
curl "http://localhost:8080/webservice/rest/server.php?\
wstoken=YOUR_TOKEN&\
wsfunction=core_webservice_get_site_info&\
moodlewsrestformat=json"
```

If this returns site info (not an error), your token works!

---

## Troubleshooting

### Error: "Function not available"

**Cause:** Function not added to service

**Fix:** Add the missing function (see above)

### Error: "Access control exception"

**Cause:** User not authorized for service

**Fix:** 
1. Go to External services → "QA Audit Service"
2. Click **Authorised users**
3. Add your admin user

### Script says functions missing

Run with `-h` to see what's needed:

```bash
python populate_test_data.py -h
```

---

## Function Groups

### Read-Only (Safe for Production)
- `core_course_get_courses` ✅
- `core_course_get_contents` ✅
- `core_course_get_categories` ✅

### Write Operations (Test Only!)
- `core_course_create_categories` ⚠️
- `core_course_create_courses` ⚠️
- `core_course_delete_courses` ⚠️
- `core_course_update_courses` ⚠️

**Note:** Only use write functions on test/development Moodle instances!

---

## Quick Commands

**Check functions for a service:**
```bash
# In Moodle UI
Site admin → Web services → External services → Functions
```

**Test token:**
```bash
curl "http://localhost:8080/webservice/rest/server.php?\
wstoken=YOUR_TOKEN&\
wsfunction=core_webservice_get_site_info&\
moodlewsrestformat=json" | jq
```

**List available functions:**
```bash
# In Moodle
Site admin → Web services → API documentation
```

---

## See Also

- [GETTING_STARTED.md](GETTING_STARTED.md) - Complete setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [DOCKER.md](DOCKER.md) - Docker setup
