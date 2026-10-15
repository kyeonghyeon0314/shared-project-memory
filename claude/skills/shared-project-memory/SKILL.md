---
name: shared-project-memory
description: Use for substantive local project work, resuming project work, and saving a Codex/Claude handoff. Not for general questions, temporary output folders, or dependencies.
---

# Shared Project Memory

This package is a Claude Code plugin. All project memory stays in the selected project's `project-memory/`. No daemon, observer, external API, archive scan, or model call runs on startup. Personal approvals from the package author do not authorize changes for another user.

## Start or resume

1. Resolve the actual user project. Do not use a generated chat/scratch folder, home, drive root, dependency folder, or another project. Follow stricter project rules.
2. If the active project's `SHARED_PROJECT_MEMORY_LOADED` context is supplied, use its bounded excerpts without repeated reads. Otherwise read `project-memory/current.md` and only the relevant latest checkpoint/topic; `MEMORY.md` is loaded by Claude's native auto memory when `autoMemoryDirectory` points at `project-memory/`. Read full files only when necessary. When answering from memory, say which parts were recorded as verified; do not present unverified or interpreted notes as established facts.
3. If memory is missing, explain the small setup diff and ask the user's approval unless this user has already authorized that exact scope. Setup covers memory files, AGENTS/CLAUDE adapters, and `.claude/settings.local.json`. Existing project/code/data permissions remain in force. Automatic setup is OFF until this recipient opts in; enabling the plugin alone is not setup consent.
4. Preview `scripts/setup_memory.py PROJECT` with an existing Python 3.11+ interpreter. Apply only the approved scope with `--apply`; main/master requires separate `--approve-main` approval. Preserve existing memory directories and all unrelated settings. Report conflicting paths or stricter project rules; do not force changes.

The scripts are in `../../scripts/` relative to this SKILL.md. Resolve absolute paths from this skill location before running them. See `../../README.md` for installation, user preference commands, and migration from an existing hook. Never install dependencies silently.

## User preferences

Use the resolved `scripts/configure.py` path. It previews one user preference file by default and writes only with `--apply`. The file is `<CLAUDE_CONFIG_DIR or ~/.claude>/shared-project-memory/settings.json`.

- Ask once whether this recipient authorizes automatic memory setup in recognized real projects. Show the initializer's exact scope. Only after approval use `configure.py --enable-auto-init --apply`. This is a standing memory-only setup preference, not permission to edit code/data, delete files, commit/push, install dependencies, or override project rules.
- Main/master setup requires separate approval and `configure.py --approve-main --apply`. Do not add that flag implicitly.

## Helper agents (optional)

Ordinary memory updates use the parent context. Delegate only when a separate helper is useful, with an isolated bounded evidence packet:

- Summarization: `shared-project-memory:memory-summarizer` (agent file sets `claude-sonnet-5-5`, effort `medium`).
- Simple extraction: `shared-project-memory:simple-extractor` (agent file sets `claude-haiku-5-5`, effort `medium`).

Always use these full namespaced names, and omit the `model` argument so the agent file's model and effort apply. Same-named agents in the user's `~/.claude/agents/` are different agents; do not use them for these tasks. Keep the main conversation model unchanged. If a model is unavailable for the account, report it; do not substitute silently. Verify model/effort from execution metadata after the first real helper call; an agent's self-description or config file is not runtime evidence. Do not create a test call just for routine saves.

## Save and hand off

After meaningful changes/verification, at completion, and before switching tools, follow the project index. Create a unique `checkpoints/YYYYMMDD-HHMMSS-agent-session.md` containing purpose, actual changed files, verification conditions/results, unresolved items, next step, and sources. Mark proposals and unverified history distinctly.

For meeting notes, keep goals, what each person said, your interpretation, and proposed follow-ups in separate parts. Attach the original wording or source to every number and strong claim, and compare against the source before saving.

Re-read current.md before updating it. With concurrent writers, leave a separate checkpoint instead of overwriting shared state. Keep MEMORY.md concise; stable decisions go in decisions.md/topics. Do not include credentials, delete archives, mix projects, or claim a failed write succeeded. A startup hook loads memory; it does not capture every conversation or guarantee saves.

## Verify

Confirm the active memory root, preservation of previous instructions/settings, and no changes on repeat initialization. `scripts/test_setup.py --fixtures WORK_DIRECTORY` tests the initializer with retained local fixtures. `scripts/test_plugin.py --package PLUGIN_ROOT --fixtures WORK_DIRECTORY` tests the package; never point fixtures at a user project, and do not place fixtures under TEMP (excluded from auto-init by design). Neither test calls a model. Keep the hook output at 4,000 characters.

If a tool fails, report the actual failure. Use only permitted narrow retries; do not bypass sandbox, permission prompts, or hook settings.
