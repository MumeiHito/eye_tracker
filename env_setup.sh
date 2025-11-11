#!/usr/bin/env bash
# Environment setup script for the gaze tracker project.
# Usage:
#   chmod +x env_setup.sh
#   ./env_setup.sh

set -euo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3.12}
VENV_DIR=${VENV_DIR:-venv}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: $PYTHON_BIN not found. Please install Python 3.12 and try again." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR"/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Virtual environment created in $VENV_DIR."

