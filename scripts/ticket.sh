#!/usr/bin/env bash
# Tickets. Status changes only go through here. See scripts/ticket.py for commands and exit codes.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ticket.py" "$@"
