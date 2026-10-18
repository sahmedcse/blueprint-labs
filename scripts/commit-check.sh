#!/usr/bin/env bash
# Small, reviewable commits: message format and size. See scripts/commit_check.py.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/commit_check.py" "$@"
