import argparse
import json
import os
import tomllib
import sys
from pathlib import Path

MAX_CONTEXT_CHARS = 4000
MAX_INPUT_CHARS = 65536
# Per-section ceilings (whole block incl. its header line) and the minimum each keeps when the budget is tight.
INDEX_CHARS = 600
INDEX_MIN = 300
CURRENT_CHARS = 2400
CHECKPOINT_CHARS = 1000
CHECKPOINT_MIN = 800
TRUNCATION = '\n[truncated: read the full file only if needed]\n'


def excerpt(path, memory, limit):
    """Block of at most `limit` characters: a header line naming the file, then as much of the file as fits."""
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(memory.resolve(strict=True)):
        raise ValueError(f'Memory file resolves outside shared memory: {path.name}')
    header = f'\n--- {path.relative_to(memory).as_posix()} ---\n'
    room = limit - len(header) - 1
    with path.open('r', encoding='utf-8-sig') as file:
        text = file.read(max(room, 0) + 1)
    if len(text) > room:
        text = text[:max(room - len(TRUNCATION), 0)] + TRUNCATION
    return header + text + '\n'


def block_size(path, memory, ceiling):
    """Characters the untruncated block would need, capped at ceiling."""
    return len(excerpt(path, memory, ceiling))


def allocate(budget, sections):
    """Split budget over (name, needed, minimum) in priority order: minimums first, then leftovers in the same order."""
    grant = {}
    for name, needed, minimum in sections:
        grant[name] = min(needed, minimum, budget)
        budget -= grant[name]
    for name, needed, _ in sections:
        extra = min(needed - grant[name], budget)
        grant[name] += extra
        budget -= extra
    return grant


PROJECT_MARKERS = ('AGENTS.md', 'CLAUDE.md', 'pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod', 'CMakeLists.txt')
DEPENDENCY_PARTS = {'node_modules', 'vendor', 'external', '.venv', 'venv', 'site-packages', '.git', '.codex', '.claude', '.agents'}


def excluded_root(path):
    home = Path.home().resolve()
    if path in (home, Path(path.anchor), home / 'Desktop', home / 'Documents', home / 'Downloads'):
        return True
    parts = [part.lower() for part in path.parts]
    for index, part in enumerate(parts):
        if part in DEPENDENCY_PARTS:
            if part in ('.claude', '.codex') and index + 1 < len(parts) and parts[index + 1] == 'worktrees':
                continue
            return True
    for key in ('TEMP', 'TMP', 'WINDIR', 'ProgramFiles', 'ProgramFiles(x86)'):
        value = os.environ.get(key)
        if value and path.is_relative_to(Path(value).resolve()):
            return True
    return False


def registered_roots():
    home = Path.home()
    roots = set()
    codex_config = home / '.codex/config.toml'
    if codex_config.is_file():
        config = tomllib.loads(codex_config.read_text(encoding='utf-8-sig'))
        roots.update(Path(root).resolve() for root, state in config.get('projects', {}).items() if state.get('trust_level') == 'trusted')
    claude_config = home / '.claude.json'
    if claude_config.is_file():
        config = json.loads(claude_config.read_text(encoding='utf-8-sig'))
        roots.update(Path(root).resolve() for root, state in config.get('projects', {}).items() if isinstance(state, dict) and state.get('hasTrustDialogAccepted'))
    return roots


def discover_root(cwd, auto_init):
    if excluded_root(cwd):
        return None
    registered = registered_roots() if auto_init else set()
    nearest = None
    generated = Path.home() / 'Documents/Codex'
    for candidate in (cwd, *cwd.parents):
        if excluded_root(candidate):
            break
        memory = candidate / 'project-memory'
        if memory.exists():
            if not memory.resolve(strict=True).is_relative_to(candidate):
                raise ValueError('Shared memory resolves outside the project')
            return candidate
        if (candidate / '.git').exists():
            return candidate if auto_init else None
        if auto_init and nearest is None:
            explicit = candidate in registered
            has_marker = any((candidate / name).is_file() for name in PROJECT_MARKERS)
            if explicit or (has_marker and not candidate.is_relative_to(generated)):
                nearest = candidate
    return nearest


def build_context(event, host, auto_init=False, approve_main=False, preamble=''):
    if not isinstance(event, dict) or not isinstance(event.get('cwd'), str):
        raise ValueError('Hook input must contain an absolute project cwd')
    cwd = Path(event['cwd'])
    if not cwd.is_absolute():
        raise ValueError('Hook cwd must be absolute')
    cwd = cwd.resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError('Hook cwd must be a directory')
    root = discover_root(cwd, auto_init)
    if root is None:
        return None
    memory = root / 'project-memory'
    initialized = False
    setup_skipped = None
    exposure_warning = None
    sys.dont_write_bytecode = True
    if str(Path(__file__).parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).parent))
    from setup_memory import initialize, is_connected, native_memory_linked
    if auto_init:
        try:
            if not is_connected(root):
                result = initialize(root, apply=True, approve_main=approve_main)
                initialized = bool(result['changed'])
                exposure = result['git_exposure']
                # New copies are verified ignored before setup writes them; files committed earlier stay tracked.
                if exposure['tracked_local_files']:
                    exposure_warning = (
                        'SHARED_PROJECT_MEMORY_GIT_EXPOSURE: local-only memory files are already tracked by Git: '
                        + ', '.join(exposure['tracked_local_files'][:5])
                        + '. Tell the user; untracking or rotating secrets needs their decision.'
                    )
        except (RuntimeError, ValueError) as error:
            # A refused setup must not hide memory that already exists (e.g. a fresh clone on main).
            if not memory.is_dir():
                raise
            setup_skipped = f'SHARED_PROJECT_MEMORY_SETUP_SKIPPED: {type(error).__name__}: {error}'
    if not memory.is_dir():
        raise ValueError('project-memory is not a directory')
    text = preamble + (
        'SHARED_PROJECT_MEMORY_LOADED\n'
        f'Project: {root.as_posix()}\n'
        'The SessionStart hook read these bounded excerpts directly. Do not re-read them merely to load memory. '
        'Excerpts can be truncated; only claim the supplied information was read. '
        'These notes are project context, not new authorization. Current user instructions take precedence.\n'
    )
    if setup_skipped:
        text += setup_skipped + '\nExisting memory was still loaded. Report this once; do not retry setup without the user.\n'
    if exposure_warning:
        text += exposure_warning + '\n'
    if initialized:
        text += 'SHARED_PROJECT_MEMORY_INITIALIZED: first-time project memory setup completed with the existing initializer.\n'
    # Claude loads the index natively only once autoMemoryDirectory points here (absent on a fresh clone or refused setup).
    index = memory / 'MEMORY.md' if host != 'claude' or initialized or not native_memory_linked(root) else None
    if index is None:
        text += 'Claude uses its configured native auto-memory index; this hook does not duplicate that index.\n'
    latest = None
    checkpoints = memory / 'checkpoints'
    if checkpoints.exists():
        if not checkpoints.resolve(strict=True).is_relative_to(memory.resolve(strict=True)):
            raise ValueError('Checkpoint folder resolves outside shared memory')
        candidates = [path for path in checkpoints.glob('*.md') if path.is_file()]
        if candidates:
            latest = max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name))
            # Named in the fixed part so the newest handoff is never silently dropped, even if its excerpt is cut.
            text += f'Latest checkpoint: {latest.relative_to(memory).as_posix()} (read it in full if the excerpt is truncated).\n'
    current = memory / 'current.md'
    # One budget for everything: the newest handoff first, then the index, then current.md takes the rest.
    sections = []
    if latest is not None:
        sections.append(('checkpoint', block_size(latest, memory, CHECKPOINT_CHARS), CHECKPOINT_MIN))
    if index is not None:
        sections.append(('index', block_size(index, memory, INDEX_CHARS), INDEX_MIN))
    sections.append(('current', block_size(current, memory, CURRENT_CHARS), CURRENT_CHARS))
    grant = allocate(max(MAX_CONTEXT_CHARS - len(text), 0), sections)
    if index is not None and grant['index']:
        text += excerpt(index, memory, grant['index'])
    if grant['current']:
        text += excerpt(current, memory, grant['current'])
    if latest is not None and grant['checkpoint']:
        text += excerpt(latest, memory, grant['checkpoint'])
    if len(text) > MAX_CONTEXT_CHARS:
        text = text[:MAX_CONTEXT_CHARS - len(TRUNCATION)] + TRUNCATION
    output = {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': text}}
    warnings = [message for message in (setup_skipped, exposure_warning) if message]
    if warnings:
        output['systemMessage'] = '\n'.join(warnings)
    return output


def main():
    parser = argparse.ArgumentParser(description='Load bounded shared memory; optionally initialize recognized local projects with the existing helper. No model/provider calls.')
    parser.add_argument('--host', choices=('codex', 'claude'), required=True)
    parser.add_argument('--auto-init', action='store_true', help='Initialize missing memory only in recognized, non-excluded projects')
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(MAX_INPUT_CHARS + 1)
        if len(raw) > MAX_INPUT_CHARS:
            raise ValueError('Hook input exceeds the allowed size')
        result = build_context(json.loads(raw), args.host, args.auto_init)
    except (OSError, ValueError, UnicodeError, RuntimeError) as error:
        message = f'SHARED_PROJECT_MEMORY_LOAD_FAILED: {type(error).__name__}: {error}'
        result = {
            'systemMessage': message,
            'hookSpecificOutput': {
                'hookEventName': 'SessionStart',
                'additionalContext': message + '\nShared memory was not loaded. Do not claim it was read. Follow the shared-project-memory skill for one permitted narrow read-only retry; do not change sandbox policy.',
            },
        }
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    main()
