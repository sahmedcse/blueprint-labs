#!/usr/bin/env bash
# Per-ticket iteration budget: iter.sh next|undo <REQ> <T>. See scripts/devloop.py.
set -euo pipefail
BPL_PROG=iter.sh exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/devloop.py" iter "$@"
