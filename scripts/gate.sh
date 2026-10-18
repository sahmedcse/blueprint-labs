#!/usr/bin/env bash
# The verification gate for one ticket. See scripts/gate.py.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gate.py" "$@"
