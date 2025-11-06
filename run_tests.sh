#!/bin/bash
# Test runner script that can be executed as postgres user

cd "$(dirname "$0")"

# Check if running as postgres user
if [ "$(whoami)" = "postgres" ]; then
    # Already postgres, just run
    python3 -m pytest test_database.py "$@"
else
    # Need to switch to postgres user
    sudo -u postgres python3 -m pytest test_database.py "$@"
fi
