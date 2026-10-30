# Documentation Index

Quick reference to all documentation in this repository.

---

## 🚀 Getting Started

### **[GETTING_STARTED.md](GETTING_STARTED.md)** ⭐ START HERE
**Complete setup guide for fresh clone to working environment**
- Prerequisites
- 5-minute quick setup
- Manual setup alternative
- Troubleshooting
- Common commands

**Use this if:** You just cloned the repo and want to get running

---

## 🆘 Troubleshooting

### **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** 🔧
**Dedicated troubleshooting guide**
- Test data population errors
- Web Services function issues
- Connection problems
- Docker issues
- Reset procedures

**Use this when:** Something isn't working

---

## 📖 Core Documentation

### **[README.md](README.md)**
**Main project documentation**
- Project overview & features
- QA checks explanation
- Quick start reference
- Usage examples (all output formats)
- Configuration options
- Moodle API setup
- Project structure
- Testing

**Use this for:** Understanding what the tool does and how to use it

---

### **[DOCKER.md](DOCKER.md)**
**Docker Moodle setup reference**
- Quick start commands
- Web Services setup steps
- Configuration instructions
- Docker commands
- Database access

**Use this for:** Docker-specific details and Web Services configuration

---

### **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
**Common issues and solutions**
- Test data population failures
- Connection issues
- Docker problems
- Permission errors
- Complete reset instructions

**Use this for:** When something goes wrong

---

## 🎯 Development

### **[QUICKSTART_DEV.md](QUICKSTART_DEV.md)**
**Fast reference for dev environment setup**
- Condensed 5-minute workflow
- Manual alternative
- Reset instructions
- File reference

**Use this for:** Quick reference when you know the steps

---

### **[TEST_DATA_REFERENCE.md](TEST_DATA_REFERENCE.md)**
**Test course documentation**
- All 8 test courses explained
- Expected issues for each course
- Verification checklist
- Adding custom test cases
- CI/CD integration

**Use this for:** Understanding test data and what each course tests

---

## 📦 Configuration Files

### **docker-compose.yml**
Docker service definitions for Moodle + MariaDB

### **.env.example**
Environment variable template for Docker

### **requirements.txt**
Python dependencies

---

## 🛠️ Scripts

### **start-moodle.sh**
Start Docker Moodle environment
```bash
./start-moodle.sh
```

### **setup-complete-dev-env.sh**
Automated complete environment setup
```bash
./setup-complete-dev-env.sh YOUR_TOKEN
```

### **populate_test_data.py**
Create test courses with QA issues
```bash
python populate_test_data.py --token YOUR_TOKEN
```

### **main.py**
QA tool entry point
```bash
python main.py [options]
```

---

## 📊 Documentation Map

```
Fresh Clone
    ↓
GETTING_STARTED.md ← START HERE
    ↓
├─→ Need Docker help?        → DOCKER.md
├─→ Need test data?          → TEST_DATA_REFERENCE.md
├─→ Quick dev reference?     → QUICKSTART_DEV.md
└─→ Full tool documentation? → README.md
```

---

## Quick Workflows

### First Time Setup
1. Read: **GETTING_STARTED.md**
2. Run: `./start-moodle.sh`
3. Follow Web Services setup
4. Run: `./setup-complete-dev-env.sh TOKEN`

### Daily Development
```bash
docker compose up -d              # Start Moodle
source venv/bin/activate          # Activate Python
python main.py --all              # Run tool
```

### Reset Environment
```bash
docker compose down -v            # Delete all data
rm -rf venv                       # Delete Python env
./start-moodle.sh                 # Start fresh
# ... repeat setup ...
```

### Add Test Data
```bash
python populate_test_data.py --token YOUR_TOKEN
```

---

## File Sizes

| File | Size | Description |
|------|------|-------------|
| GETTING_STARTED.md | ~12 KB | Complete setup guide |
| README.md | ~8 KB | Project documentation |
| TEST_DATA_REFERENCE.md | ~10 KB | Test data details |
| DOCKER.md | ~2 KB | Docker reference |
| QUICKSTART_DEV.md | ~2 KB | Quick dev guide |
| populate_test_data.py | ~22 KB | Test data script |
| setup-complete-dev-env.sh | ~2 KB | Setup automation |

**Total documentation: ~58 KB**

---

## Documentation Status

✅ All documentation is current and synchronized  
✅ All cross-references are valid  
✅ All examples tested  
✅ Fresh clone workflow documented  

**Last Updated:** 2026-10-30

---

## Contributing to Documentation

When updating documentation:

1. **Keep cross-references in sync**
   - Update all files that reference changed content
   - Check links are still valid

2. **Test commands**
   - All bash commands should be tested
   - All code examples should work

3. **Update this index**
   - Add new files here
   - Update "Last Updated" date

4. **Follow the structure**
   - GETTING_STARTED.md - complete workflows
   - README.md - features and usage
   - DOCKER.md - Docker specifics
   - TEST_DATA_REFERENCE.md - test details
   - QUICKSTART_DEV.md - condensed reference

---

## Quick Links

- [Getting Started](GETTING_STARTED.md) - Start here!
- [README](README.md) - Main documentation
- [Docker Setup](DOCKER.md) - Docker details
- [Test Data](TEST_DATA_REFERENCE.md) - Test courses
- [Quick Dev Reference](QUICKSTART_DEV.md) - Fast setup
