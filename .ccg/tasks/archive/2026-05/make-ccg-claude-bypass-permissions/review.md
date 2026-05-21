# Review

## Claude reviewer

Initial review found actionable issues:
- `--backend claude resume <session> - <workdir>` was misparsed.
- Claude passthrough arguments were silently dropped.
- Bypass had no opt-out or audit marker.
- The shim did not validate `claude` resolution or workdir existence.
- Log file handling needed restrictive permissions.

Fixes applied:
- Implemented Claude resume translation via `claude --resume <session>`.
- Added `CODEAGENT_CLAUDE_BYPASS=0` opt-out.
- Added explicit unsupported-argument errors and ignored-argument warnings.
- Added `claude` binary and workdir validation.
- Moved shim logs to `~/.claude/logs` with `0600` files.

## Gemini reviewer

Not run: local Gemini backend is unavailable (`gemini command not found in PATH`).

## Verification

- `python3 -m py_compile /Users/ww/.claude/bin/codeagent-wrapper` passed.
- Standard CCG Claude call returned:
  - `HASH=fc62820e9d6c3f5f1d49c4b48df62f28f59d915bcc2fd90a2ba80fba7ae3368a`
  - `LINES=253`
- Shim log confirmed `permissionMode:"bypassPermissions"` and `permission_denials:[]`.
- Log permissions confirmed `-rw-------`.
- `CODEAGENT_CLAUDE_BYPASS=0` removed the bypass flag.
- `--backend claude resume <session> - <workdir>` returned `RESUME_BYPASS_OK`.
