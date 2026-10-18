#!/usr/bin/env bash
# See scripts/handoff.py.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/handoff.py" merge-review "$@"
