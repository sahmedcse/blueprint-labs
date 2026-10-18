#!/usr/bin/env bash
# Requests and their overall status. See scripts/request.py for commands.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/request.py" "$@"
