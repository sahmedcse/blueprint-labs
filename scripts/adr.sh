#!/usr/bin/env bash
# File approved ADRs and contracts into the trail. See scripts/contracts.py.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/contracts.py" "$@"
