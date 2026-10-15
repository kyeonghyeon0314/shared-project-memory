---
name: shared-project-memory
description: Use for substantive local project work, resuming project work, and saving a Codex/Claude handoff. Not for general questions, temporary output folders, or dependencies.
---

# Shared Project Memory

This package is a Codex local plugin. All project memory stays in the selected project's `project-memory/`. No daemon, observer, external API, archive scan, or provider call runs on startup. Personal approvals from the package author do not authorize changes for another user.

## Start or resume

1. Resolve the actual user project. Do not use the generated chat folder, home, drive root, dependency folder, or another project. Follow stricter project rules.
2. If the active project's `SHARED_PROJECT_MEMORY_LOADED` context is supplied, use its bounded excerpts without repeated reads. Otherwise read `project-memory/MEMORY.md`, `current.md`, and only the relevant latest checkpoint/topic. Read full files only when necessary. When answering from memory, say which parts were recorded as verified; do not present unverified or interpreted notes as established facts.
3. If memory is missing, explain the small setup diff and ask the user's approval unless this user has already authorized that exact scope. Setup covers memory files, AGENTS/CLAUDE adapters, and `.claude/settings.local.json`. Existing project/code/data permissions remain in force. Automatic setup is OFF until this recipient opts in; hook trust alone is not setup consent.
4. Preview `scripts/setup_memory.py PROJECT` with an existing Python 3.11+ interpreter. Apply only the approved scope with `--apply`; main/master requires separate `--approve-main` approval. Preserve existing memory directories and all unrelated settings. Report conflicting paths or stricter project rules; do not force changes.

The scripts are in `../../scripts/` relative to this SKILL.md. Resolve absolute paths from this skill location before running them. See `../../README.md` for installation, user preference commands, and legacy setup migration. Never install dependencies silently.

## User preferences

Use the resolved `scripts/configure.py` path. It previews one user preference file by default and writes only with `--apply`. The default is `<CODEX_HOME or ~/.codex>/shared-project-memory/settings.json`.

- Ask once whether this recipient authorizes automatic memory setup in recognized real projects. Show the initializer's exact scope. Only after approval use `configure.py --enable-auto-init --apply`. This is a standing memory-only setup preference, not permission to edit code/data, delete files, commit/push, install dependencies, or override project rules.
- Main/master setup requires separate approval and `configure.py --approve-main --apply`. Do not add that flag implicitly.
- Ask the recipient to select model and effort for memory summarization and simple extraction only if they want separate helpers. Preview their selected values, then persist them with configure.py. Never choose the package author's models for another user. No mapping means no separate helper delegation; use the existing parent context for ordinary memory updates.
- Keep research/coding main models unchanged. Follow the mapped model/effort via the supported app spawn route with explicit model overrides and `fork_turns=none`. Do not claim a named custom role is available unless the host actually exposes it. Report unsupported routes or unavailable models; do not substitute silently.
- Verify model/effort from execution metadata after the first real helper call; an agent's self-description or config file is not runtime evidence. Do not create a test call just for routine saves.

## Save and hand off

After meaningful changes/verification, at completion, and before switching tools, follow the project index. Create a unique `checkpoints/YYYYMMDD-HHMMSS-agent-session.md` containing purpose, actual changed files, verification conditions/results, unresolved items, next step, and sources. Mark proposals and unverified history distinctly.

For meeting notes, keep goals, what each person said, your interpretation, and proposed follow-ups in separate parts. Attach the original wording or source to every number and strong claim, and compare against the source before saving.

Re-read current.md before updating it. With concurrent writers, leave a separate checkpoint instead of overwriting shared state. Keep MEMORY.md concise; stable decisions go in decisions.md/topics. Do not include credentials, delete archives, mix projects, or claim a failed write succeeded. A startup hook loads memory; it does not capture every conversation or guarantee saves.

## Verify

Confirm the active memory root, preservation of previous instructions/settings, and no changes on repeat initialization. `scripts/test_setup.py --fixtures WORK_DIRECTORY` tests the initializer with retained local fixtures. `scripts/test_plugin.py --package PLUGIN_ROOT --fixtures WORK_DIRECTORY` tests the package; never point fixtures at a user project. Neither test calls a model. Keep the hook output at 4,000 characters.

If a tool fails, report the actual failure. Use only permitted narrow retries; do not bypass sandbox, approval, or hook trust. The plugin requires the official hook review/trust flow before its hooks run.
