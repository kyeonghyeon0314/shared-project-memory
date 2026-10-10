# Shared Project Memory

English | [한국어](README.ko.md)

**One project memory for Claude Code and OpenAI Codex.** Switch between the two coding agents without re-explaining where you left off.

Each agent gets a plugin. Both read and write the same plain Markdown files in your repository (`project-memory/`). At the start of every session, a SessionStart hook injects a bounded excerpt of that memory, so the next agent — Claude or Codex — starts from the latest state and handoff.

No server, database, vector store or external API. Just files in your project and two small Python hooks.

## Why

If you use more than one coding agent on the same project, each new session starts cold: it doesn't know what the other agent changed, what was verified, or what was decided. You end up pasting summaries by hand. Shared Project Memory makes the handoff a file that both agents load automatically.

## How it works

```
 Claude Code session                         Codex session (later)
 ───────────────────                         ─────────────────────
 work on the task                            SessionStart hook runs
 save a handoff  ──►  project-memory/  ──►   injects ≤ 4,000 chars:
   checkpoints/20261010-1400-claude.md         • latest checkpoint (path always shown)
   current.md                                  • MEMORY.md index
                                               • current.md
                                             continues from the handoff
```

| Step | Automatic? |
|---|---|
| **Loading** memory at session start (startup, resume, clear, compact) | Yes — SessionStart hook, no model call |
| **Saving** a handoff (checkpoint) after meaningful work or before switching tools | The agent does it by following the bundled skill; it is not a transcript recorder |
| First-time setup of `project-memory/` in a project | Only after you opt in (off by default) |

The injected excerpt is capped at 4,000 characters. The budget goes to the newest checkpoint first (at least 800 characters, and its path is always listed), then the index, then `current.md`. Anything truncated is marked so the agent knows to open the full file.

## Memory layout

```
project-memory/
├── MEMORY.md        index and save rules
├── current.md       current state of the project
├── decisions.md     confirmed decisions and preferences
├── topics/          notes read only when relevant
├── checkpoints/     one handoff file per session — never overwritten
├── archive/         backups of pre-existing files (git-ignored)
└── .gitignore       keeps archive/ and machine state out of Git
```

## Quick start

Requirements: Python 3.11+, Git, and Claude Code and/or Codex with command hooks.

### Claude Code

```bash
claude plugin marketplace add kyeonghyeon0314/shared-project-memory
claude plugin install shared-project-memory@shared-project-memory-local
```

Restart Claude Code. To let the plugin create `project-memory/` automatically in recognized projects, opt in once per machine (preview first, then apply):

```bash
python3 <installed claude plugin dir>/scripts/configure.py --enable-auto-init
python3 <installed claude plugin dir>/scripts/configure.py --enable-auto-init --apply
```

Or set up a single project explicitly: `python3 <plugin dir>/scripts/setup_memory.py <project> --apply`.

### Codex

```bash
git clone https://github.com/kyeonghyeon0314/shared-project-memory.git
codex plugin marketplace add "<clone path>/codex"
codex plugin add shared-project-memory@shared-project-memory-local
```

Then open `/hooks` in Codex, review the shared-project-memory SessionStart hook and trust it — Codex does not run plugin hooks until you do. Opt-in for automatic setup works the same way with `codex/scripts/configure.py`.

Details: [`claude/README.md`](claude/README.md), [`codex/README.md`](codex/README.md) (Korean).

## Safety and privacy

- **Off by default.** Installing the plugin does not create files. Automatic setup needs an explicit opt-in; setup on `main`/`master` needs a second, separate approval.
- **Preview first.** Every setup and configuration command prints the changes and writes nothing without `--apply`.
- **Existing files are preserved.** `AGENTS.md`, `CLAUDE.md` and settings are appended to, never replaced. Conflicting memory paths or project rules that forbid edits stop setup.
- **Local secrets stay local.** Backups of `.claude/settings.local.json` go to your user config folder (mode 0600), never into the project. Before writing anything into `archive/`, setup asks Git (`git check-ignore`) whether each exact path is ignored and aborts without writing if not — even when an existing `.gitignore` uses `!` negations.
- **No absolute paths** in shared files, so the memory works for teammates who clone the repo.

## Verification status (0.1.4)

| | Claude Code | Codex |
|---|---|---|
| Marketplace install | ✅ | ✅ |
| SessionStart hook runs and injects memory | ✅ (Docker, live session) | ✅ (Windows host, after `/hooks` trust) |
| Latest checkpoint survives a long `current.md` | ✅ | ✅ |
| Helper agents run on the configured model | ✅ Sonnet / Haiku | ✅ user-selected models and effort |

CI runs the test suite on Linux, Windows and macOS with Python 3.11 and 3.13. Details are recorded in `claude/verification.json` and `codex/verification.json`.

## Known limitations

- Saving handoffs depends on the agent following the skill; an abrupt exit can lose an unsaved handoff.
- The 4,000-character injection is an excerpt. Keep `current.md` short and move history into checkpoints or `topics/`.
- Codex reads the plugin from `.codex-plugin/plugin.json`; a portable root `plugin.json` hides plugin hooks in current Codex versions ([openai/codex#39895](https://github.com/openai/codex/issues/39895)), so ChatGPT ZIP upload is not supported.
- Projects initialized by older versions need one `setup_memory.py <project> --apply` run after updating to get the `.gitignore` protection.

## Updating

```bash
# Claude Code
claude plugin marketplace update shared-project-memory-local
claude plugin update shared-project-memory@shared-project-memory-local
```

For Codex, pull the clone and run `codex plugin add shared-project-memory@shared-project-memory-local` again. See [CHANGELOG.md](CHANGELOG.md).

## Feedback

Installation problems and bugs: please [open an issue](https://github.com/kyeonghyeon0314/shared-project-memory/issues/new/choose). Reports from setups other than Windows + Codex desktop or Linux + Claude Code are especially welcome.

## License

[MIT](LICENSE)
