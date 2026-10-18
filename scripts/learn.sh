#!/usr/bin/env bash
# Apply an approved retro to principles/. See scripts/learn.py.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/learn.py" "$@"
