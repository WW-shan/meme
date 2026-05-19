# GOAL DOCUMENT RULES

## SCOPE

These rules apply to every file in `docs/goals/`.

## HARD GUARDRAIL

- Goal documents are user-controlled workflow contracts.
- Do not modify, rewrite, rename, move, delete, reformat, or auto-improve any goal document unless the user explicitly requests that exact goal-document change in the current turn.
- Continuing a goal, executing a plan, improving model optimization, updating docs or research, committing/pushing work, or changing runtime/model behavior is not permission to edit files in this directory.

## REQUIRED CHECK

- Before any commit or push, run or inspect `git status --short --untracked-files=all -- docs/goals`, `git diff -- docs/goals/`, and `git diff --cached -- docs/goals/`.
- If there is any unrequested added, modified, renamed, moved, deleted, reformatted, or staged file under `docs/goals/`, stop and remove only your own unrequested goal-document changes before continuing.
- If the user did request a goal-document change, state the requested scope before editing and keep the diff limited to that scope.

## WHERE TO WRITE INSTEAD

- Use the task-appropriate non-goal file for evidence, research, plans, config, and code changes instead of editing goal docs.
