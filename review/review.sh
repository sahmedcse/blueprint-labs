#!/usr/bin/env bash
# Review gates for one request. See review/review.py for commands and exit codes.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/review.py" "$@"
