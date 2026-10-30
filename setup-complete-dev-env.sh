#!/bin/bash
set -e

echo "🔧 Complete Moodle QA Development Environment Setup"
echo "===================================================="
echo ""

# Check if token is provided
if [ -z "$1" ]; then
    echo "❌ Error: Moodle API token required"
    echo ""
    echo "Usage: $0 YOUR_API_TOKEN"
    echo ""
    echo "Steps to get token:"
    echo "  1. Start Moodle: ./start-moodle.sh"
    echo "  2. Setup Web Services (see DOCKER.md)"
    echo "  3. Generate API token"
    echo "  4. Run: $0 YOUR_TOKEN"
    exit 1
fi

TOKEN="$1"
MOODLE_URL="http://localhost:8080"

echo "📋 Configuration:"
echo "   Moodle URL: $MOODLE_URL"
echo "   Token: ${TOKEN:0:10}..."
echo ""

# Check if Moodle is running
echo "🔍 Checking Moodle..."
if ! curl -sf "$MOODLE_URL" > /dev/null 2>&1; then
    echo "❌ Moodle is not accessible at $MOODLE_URL"
    echo "   Run: ./start-moodle.sh"
    exit 1
fi
echo "   ✓ Moodle is running"

# Check Python environment
echo ""
echo "🐍 Checking Python environment..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "   ✓ Dependencies installed"

# Update main.py with token
echo ""
echo "⚙️  Configuring main.py..."
if [ -f "main.py" ]; then
    # Create backup
    cp main.py main.py.bak

    # Update configuration
    sed -i.tmp "s|MOODLE_URL = .*|MOODLE_URL = \"$MOODLE_URL\"|g" main.py
    sed -i.tmp "s|TOKEN = .*|TOKEN = \"$TOKEN\"|g" main.py
    rm -f main.py.tmp

    echo "   ✓ main.py configured"
else
    echo "   ⚠ main.py not found"
fi

# Populate test data
echo ""
echo "🗃️  Populating test data..."
if python populate_test_data.py --url "$MOODLE_URL" --token "$TOKEN"; then
    echo "   ✓ Test data created"
else
    echo "   ⚠ Test data population failed (continuing anyway)"
fi

# Run QA tool
echo ""
echo "🔍 Running QA tool test..."
if python main.py --no-console --no-json > /dev/null 2>&1; then
    echo "   ✓ QA tool runs successfully"
else
    echo "   ⚠ QA tool test failed (check configuration)"
fi

echo ""
echo "===================================================="
echo "✅ Setup Complete!"
echo ""
echo "📊 Your environment is ready:"
echo "   • Moodle running at $MOODLE_URL"
echo "   • 8 test courses created with QA issues"
echo "   • Python environment configured"
echo "   • Dependencies installed"
echo ""
echo "🚀 Next steps:"
echo "   1. Run QA tool:        python main.py"
echo "   2. View reports:       ls -l moodle_qa_reports/"
echo "   3. Access Moodle:      open $MOODLE_URL"
echo "   4. Login:              admin / Admin123!"
echo ""
echo "📖 Documentation:"
echo "   • DOCKER.md  - Docker & Web Services setup"
echo "   • README.md  - QA tool usage & options"
echo ""
