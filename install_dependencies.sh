#!/usr/bin/env bash
# Simple helper script to install Python dependencies
set -e

if ! command -v pip >/dev/null 2>&1; then
  echo "pip is required but was not found. Please install Python and pip." >&2
  exit 1
fi

pip install -r requirements.txt
