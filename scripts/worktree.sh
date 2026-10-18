#!/usr/bin/env bash
# One worktree per ticket. See scripts/devloop.py.
set -euo pipefail
BPL_PROG=worktree.sh exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/devloop.py" "$@"
