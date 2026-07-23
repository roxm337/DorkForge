#!/usr/bin/env bash
set -euo pipefail

echo "==> DorkForge Installer"
echo ""

# Check Python
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3 not found"
    exit 1
fi
echo "[+] Python: $($PYTHON --version)"

# Create venv if not in one
if [ -z "${VIRTUAL_ENV:-}" ]; then
    if [ ! -d .venv ]; then
        echo "[+] Creating virtual environment..."
        $PYTHON -m venv .venv
    fi
    source .venv/bin/activate
    echo "[+] Virtual env: .venv"
fi

# Upgrade pip
pip install --upgrade pip >/dev/null

# Install deps
echo "[+] Installing dependencies..."
pip install -r requirements.txt >/dev/null

# Install package
echo "[+] Installing DorkForge..."
pip install -e . >/dev/null

echo ""
echo "==> Done!"
echo ""
echo "Try:"
echo "  dorkforge categories"
echo "  dorkforge cve"
echo "  dorkforge search --category 'Exposed Files' --enrich --export html"
echo "  dorkforge-gui"
