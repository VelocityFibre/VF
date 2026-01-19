#!/bin/bash
# Setup automated database cleanup cron job

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 Setting up database cleanup cron job..."

# Install psycopg2 if not already installed
echo "📦 Checking Python dependencies..."
if ! "$PROJECT_DIR/venv/bin/pip" show psycopg2-binary > /dev/null 2>&1; then
    echo "  Installing psycopg2-binary..."
    "$PROJECT_DIR/venv/bin/pip" install psycopg2-binary
else
    echo "  ✅ psycopg2-binary already installed"
fi

# Test the script in dry-run mode
echo ""
echo "🧪 Testing script in dry-run mode..."
"$PROJECT_DIR/venv/bin/python3" "$SCRIPT_DIR/database-cleanup.py" --dry-run

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Script test successful!"
else
    echo ""
    echo "❌ Script test failed. Please check the error above."
    exit 1
fi

# Create cron job entry
CRON_ENTRY="0 2 * * 0  cd $PROJECT_DIR && $PROJECT_DIR/venv/bin/python3 $SCRIPT_DIR/database-cleanup.py >> $PROJECT_DIR/logs/database-cleanup.log 2>&1"

echo ""
echo "📅 Cron job entry (runs every Sunday at 2 AM):"
echo "$CRON_ENTRY"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "database-cleanup.py"; then
    echo ""
    echo "⚠️  Cron job already exists. Skipping installation."
    echo "   To reinstall, first remove the existing job:"
    echo "   crontab -e  # then delete the database-cleanup.py line"
else
    echo ""
    read -p "Install this cron job? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Add to crontab
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        echo "✅ Cron job installed successfully!"
    else
        echo "❌ Cron job installation skipped."
        echo ""
        echo "To install manually, run:"
        echo "  crontab -e"
        echo ""
        echo "Then add this line:"
        echo "  $CRON_ENTRY"
    fi
fi

echo ""
echo "📊 Manual usage:"
echo "  Dry run:    $PROJECT_DIR/venv/bin/python3 $SCRIPT_DIR/database-cleanup.py --dry-run"
echo "  Clean all:  $PROJECT_DIR/venv/bin/python3 $SCRIPT_DIR/database-cleanup.py"
echo "  One table:  $PROJECT_DIR/venv/bin/python3 $SCRIPT_DIR/database-cleanup.py --table qcontact_sync_log"
echo ""
echo "✅ Setup complete!"
