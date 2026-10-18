#!/usr/bin/env bash
# Fails if a ticket's tree changed after its gate passed. See scripts/gate.py.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gate.py" verify "$@"
