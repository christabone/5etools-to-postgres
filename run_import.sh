#!/bin/bash
# Wrapper script to run imports as postgres user
# Works around directory permission issues

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy necessary files to /tmp
cp "$SCRIPT_DIR/db_helpers.py" /tmp/
cp "$SCRIPT_DIR/$1" /tmp/
cp -r "$SCRIPT_DIR/cleaned_data" /tmp/ 2>/dev/null || true
cp -r "$SCRIPT_DIR/extraction_data" /tmp/ 2>/dev/null || true

# Run as postgres user from /tmp
cd /tmp
sudo -u postgres python3 "/tmp/$1"

# Capture exit code
EXIT_CODE=$?

# Cleanup
rm -f /tmp/db_helpers.py "/tmp/$1"

exit $EXIT_CODE
