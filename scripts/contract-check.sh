#!/usr/bin/env bash
# Every repo builds against the current contract. See scripts/contracts.py.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/contracts.py" check "$@"
