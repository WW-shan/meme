#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[DEPRECATED] Use ./tools/memectl bot <action>"
exec "${SCRIPT_DIR}/memectl" bot "${@:-status}"
