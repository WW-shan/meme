#!/usr/bin/env bash

pid_file_for() {
  local svc="$1"
  printf '%s\n' "${RUN_DIR}/${svc}.pid"
}

log_file_for() {
  local svc="$1"
  printf '%s\n' "${LOG_DIR}/${svc}.log"
}

read_pid() {
  local pid_file="$1"
  [[ -f "${pid_file}" ]] || return 1
  local pid
  pid="$(cat "${pid_file}" 2>/dev/null || true)"
  [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
  printf '%s\n' "${pid}"
}

is_pid_alive() {
  local pid="$1"
  ps -p "${pid}" >/dev/null 2>&1
}

process_matches_signature() {
  local pid="$1"
  local signature="$2"
  local cmd
  cmd="$(ps -p "${pid}" -o command= 2>/dev/null || true)"
  [[ "${cmd}" == *"tmux new-session"* ]] && return 1
  [[ -n "${cmd}" && "${cmd}" == *"${signature}"* ]]
}

is_service_running() {
  local svc="$1"
  local signature="$2"
  local pid_file pid
  pid_file="$(pid_file_for "${svc}")"
  pid="$(read_pid "${pid_file}" || true)"
  [[ -n "${pid}" ]] || return 1
  is_pid_alive "${pid}" || return 1
  process_matches_signature "${pid}" "${signature}" || return 1
  printf '%s\n' "${pid}"
}

write_pid_file() {
  local svc="$1"; local pid="$2"
  printf '%s\n' "${pid}" > "$(pid_file_for "${svc}")"
}

clear_pid_file() {
  local svc="$1"
  rm -f "$(pid_file_for "${svc}")"
}

stop_with_timeout() {
  local svc="$1"; local signal_name="$2"; local timeout_s="$3"
  local pid_file pid
  pid_file="$(pid_file_for "${svc}")"
  pid="$(read_pid "${pid_file}" || true)"
  [[ -n "${pid}" ]] || return 0

  if ! is_pid_alive "${pid}"; then
    clear_pid_file "${svc}"
    return 0
  fi

  kill "-${signal_name}" "${pid}" 2>/dev/null || true

  local i
  for ((i=0; i<timeout_s; i++)); do
    if ! is_pid_alive "${pid}"; then
      clear_pid_file "${svc}"
      return 0
    fi
    sleep 1
  done

  kill -9 "${pid}" 2>/dev/null || true
  sleep 1
  clear_pid_file "${svc}"
  return 0
}
