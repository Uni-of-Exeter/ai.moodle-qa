# 👋 Welcome!

## Fresh Clone? Start Here

```bash
# 1. Clone (you probably just did this)
git clone <repository-url>
cd moodle-qa

# 2. Read the complete setup guide
cat GETTING_STARTED.md
# Or open it in your editor/browser

# 3. Follow the 5-minute setup
./start-moodle.sh
# ... setup Web Services (see GETTING_STARTED.md) ...
./setup-complete-dev-env.sh YOUR_TOKEN

# 4. Run!
python main.py --all
```

**Complete instructions:** [GETTING_STARTED.md](GETTING_STARTED.md)

---

## Already Set Up?

```bash
# Start Moodle
docker compose up -d

# Activate Python
source venv/bin/activate

# Run QA tool
python main.py
```

---

## Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** ← Fresh clone? Start here
- **[README.md](README.md)** - What this tool does
- **[DOCKER.md](DOCKER.md)** - Docker reference
- **[TEST_DATA_REFERENCE.md](TEST_DATA_REFERENCE.md)** - Test data explained
- **[DOCS_INDEX.md](DOCS_INDEX.md)** - All documentation

---

## Quick Help

**Something not working?**
- See: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Can't access Moodle?**
```bash
docker logs moodle-app -f
```

**Need to reset?**
```bash
docker compose down -v
./start-moodle.sh
```

**Test data fails?**
- Add all 7 functions (see TROUBLESHOOTING.md)
- Or skip it: `python main.py` still works

---

**Questions?** Read [GETTING_STARTED.md](GETTING_STARTED.md) - everything you need is there! 🚀
