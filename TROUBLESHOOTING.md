# Troubleshooting Guide

## Test Data Population Fails

### Error: "Moodle API Error: ..."

**Cause:** Missing Web Services functions

**Solution:**

1. Go to: **Site administration → Plugins → Web services → External services**
2. Click **Functions** next to "QA Audit Service"
3. Verify these functions are added:
   - `core_course_get_categories`
   - `core_course_create_categories`
   - `core_course_get_courses`
   - `core_course_create_courses`
   - `core_course_delete_courses`
   - `core_course_update_courses`

4. Add any missing functions:
   - Click **Add functions**
   - Search for function name
   - Select it and click **Add functions**

5. Try again:
   ```bash
   python populate_test_data.py --token YOUR_TOKEN
   ```

### Alternative: Skip Test Data Population

You can skip automated test data creation and just run the QA tool:

```bash
# Only needs 2 functions:
# - core_course_get_courses
# - core_course_get_contents

python main.py
```

Then manually create test courses in Moodle.

---

## setup-complete-dev-env.sh Fails at Test Data

The setup script will continue even if test data population fails:

```bash
./setup-complete-dev-env.sh YOUR_TOKEN
```

Output:
```
...
🗃️  Populating test data...
   ⚠ Test data population failed (continuing anyway)
...
✅ Setup Complete!
```

**This is OK!** You can:
- Add missing functions (see above)
- Run `python populate_test_data.py --token YOUR_TOKEN` manually
- Or skip test data and create courses manually

---

## Cannot Access Moodle

### Error: curl: (7) Failed to connect

**Cause:** Moodle container not running

**Solution:**
```bash
# Check status
docker compose ps

# Restart if needed
docker compose down
./start-moodle.sh
```

---

## QA Tool Can't Connect

### Error: "Connection refused"

**Check list:**
1. Moodle accessible: `curl http://localhost:8080`
2. Web Services enabled: Site admin → Advanced features
3. REST protocol enabled: Plugins → Web services → Manage protocols
4. Token correct in `main.py`

**Test token manually:**
```bash
curl "http://localhost:8080/webservice/rest/server.php?\
wstoken=YOUR_TOKEN&\
wsfunction=core_webservice_get_site_info&\
moodlewsrestformat=json"
```

Should return JSON with site info, not an error.

---

## Docker Issues

### Port 8080 already in use

**Solution:**
```bash
# Stop conflicting service, or change port
# Edit docker-compose.yml:
ports:
  - "8081:80"  # Change 8080 to 8081

# Update main.py:
MOODLE_URL = "http://localhost:8081"
```

### Out of disk space

**Check:**
```bash
docker system df
```

**Clean up:**
```bash
docker system prune -a --volumes
```

---

## Python Issues

### ModuleNotFoundError

**Cause:** Dependencies not installed

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Python 3.10+ required

**Check version:**
```bash
python --version
```

**Upgrade if needed** (method varies by OS)

---

## Permission Errors

### Can't execute scripts

**Solution:**
```bash
chmod +x start-moodle.sh
chmod +x setup-complete-dev-env.sh
chmod +x populate_test_data.py
```

---

## Reset Everything

### Complete fresh start

```bash
# 1. Stop and delete all Docker data
docker compose down -v

# 2. Delete Python environment
rm -rf venv

# 3. Start fresh
./start-moodle.sh

# 4. Re-do Web Services setup in browser

# 5. Re-run setup
./setup-complete-dev-env.sh YOUR_NEW_TOKEN
```

---

## Getting More Help

### Enable verbose logging

**For populate script:**
```bash
python populate_test_data.py --token YOUR_TOKEN --url http://localhost:8080 2>&1 | tee populate.log
```

**For Docker:**
```bash
docker logs moodle-app -f
docker logs moodle-db -f
```

**For QA tool:**
```bash
python main.py --all 2>&1 | tee qa.log
```

### Check Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) - Complete setup
- [DOCKER.md](DOCKER.md) - Docker details
- [README.md](README.md) - Full documentation

### Common Gotchas

1. **Token expires** - Generate new token in Moodle
2. **Wrong token** - Copy carefully, tokens are long
3. **Functions not added** - Check External services → Functions
4. **Web Services disabled** - Check Advanced features
5. **REST protocol disabled** - Check Manage protocols
6. **Port conflict** - Change 8080 to another port
7. **Docker not running** - Start Docker Desktop

---

## Still Stuck?

1. Check you followed **all** steps in GETTING_STARTED.md
2. Verify Web Services configuration in Moodle
3. Test token with curl command above
4. Check Docker logs
5. Try manual setup instead of automated script
