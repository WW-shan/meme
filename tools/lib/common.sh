#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="${PROJECT_ROOT}/run"
LOG_DIR="${PROJECT_ROOT}/logs"

ensure_runtime_dirs() {
  mkdir -p "${RUN_DIR}" "${LOG_DIR}"
}

log_info() { printf '[INFO] %s\n' "$*"; }
log_warn() { printf '[WARN] %s\n' "$*"; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

die() {
  log_error "$*"
  exit 1
}

require_platform() {
  local uname_out
  uname_out="$(uname)"
  case "${uname_out}" in
    Linux|Darwin) ;;
    *) die "Unsupported platform: ${uname_out}. Expected Linux or macOS." ;;
  esac
}
