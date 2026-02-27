#!/usr/bin/env bash

resolve_python_bin() {
  if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/.venv/bin/python"
    return 0
  fi
  if [[ -x "${PROJECT_ROOT}/venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/venv/bin/python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  return 1
}

require_python_bin() {
  local py
  py="$(resolve_python_bin || true)"
  [[ -n "${py}" ]] || die "Python interpreter not found (.venv/venv/python3)."
  printf '%s\n' "${py}"
}
