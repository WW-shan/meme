#!/usr/bin/env bash

resolve_virtualenv_python() {
  if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/.venv/bin/python"
    return 0
  fi
  if [[ -x "${PROJECT_ROOT}/venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/venv/bin/python"
    return 0
  fi
  return 1
}

create_project_venv() {
  command -v python3 >/dev/null 2>&1 || die "python3 not found; cannot auto-create virtualenv"
  printf '[INFO] Virtualenv not found. Creating %s/.venv\n' "${PROJECT_ROOT}" >&2
  python3 -m venv "${PROJECT_ROOT}/.venv" || die "failed to create virtualenv. On Debian/Ubuntu, install python3-venv"
}

ensure_venv_pip() {
  local py="$1"
  if "${py}" -m pip --version >/dev/null 2>&1; then
    return 0
  fi

  printf '[INFO] pip not found in virtualenv, bootstrapping with ensurepip\n' >&2
  "${py}" -m ensurepip --upgrade >&2 || die "failed to bootstrap pip inside virtualenv"
  "${py}" -m pip --version >/dev/null 2>&1 || die "pip still unavailable in virtualenv after ensurepip"
}

venv_root_from_python() {
  local py="$1"
  (cd "$(dirname "${py}")/.." && pwd)
}

requirements_stamp_file() {
  local py="$1"
  printf '%s\n' "$(venv_root_from_python "${py}")/.requirements.sha256"
}

compute_requirements_hash() {
  local py="$1"
  local req_file="$2"
  "${py}" - "${req_file}" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

sync_requirements_if_needed() {
  local py="$1"
  local req_file="${PROJECT_ROOT}/requirements.txt"
  [[ -f "${req_file}" ]] || die "requirements.txt not found: ${req_file}"

  local stamp_file
  stamp_file="$(requirements_stamp_file "${py}")"

  local expected_hash
  expected_hash="$(compute_requirements_hash "${py}" "${req_file}")"

  local current_hash
  current_hash="$(cat "${stamp_file}" 2>/dev/null || true)"

  if [[ "${expected_hash}" == "${current_hash}" ]]; then
    printf '[INFO] requirements unchanged, skipping install\n' >&2
    return 0
  fi

  ensure_venv_pip "${py}"

  printf '[INFO] Installing dependencies from %s\n' "${req_file}" >&2
  "${py}" -m pip install -r "${req_file}" >&2
  printf '%s\n' "${expected_hash}" > "${stamp_file}"
}

require_python_bin() {
  local py
  py="$(resolve_virtualenv_python || true)"

  if [[ -z "${py}" ]]; then
    create_project_venv
    py="${PROJECT_ROOT}/.venv/bin/python"
  fi

  sync_requirements_if_needed "${py}"
  printf '%s\n' "${py}"
}
