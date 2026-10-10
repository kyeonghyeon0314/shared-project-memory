import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

parser = argparse.ArgumentParser()
parser.add_argument('--package', required=True)
parser.add_argument('--fixtures', required=True)
args = parser.parse_args()
package = Path(args.package).resolve()
fixtures = Path(args.fixtures).resolve() / ('claude-plugin-check-' + uuid4().hex[:8])
fixtures.mkdir(parents=True)
settings = fixtures / 'user settings.json'
root = fixtures / 'project space 한글'
root.mkdir()
subprocess.run(['git', 'init', '-b', 'memory-test', str(root)], check=True, capture_output=True)
(root / 'pyproject.toml').write_text('[project]\nname="sample"\n', encoding='utf-8')
(root / 'AGENTS.md').write_text('Original project instruction\n', encoding='utf-8')
(root / '.claude').mkdir()
(root / '.claude/settings.local.json').write_text(json.dumps({'permissions': {'allow': ['Read']}}), encoding='utf-8')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CLAUDE_CONFIG_DIR=str(fixtures / 'claude-user'))
checks = []
hook = json.loads((package / 'hooks/hooks.json').read_text(encoding='utf-8'))['hooks']['SessionStart'][0]['hooks'][0]
assert hook['command'] == 'python3' and hook['args'] == ['${CLAUDE_PLUGIN_ROOT}/scripts/hook_entry.py']
for agent, model in (('memory-summarizer', 'claude-sonnet-5-5'), ('simple-extractor', 'claude-haiku-5-5')):
    header = (package / 'agents' / (agent + '.md')).read_text(encoding='utf-8').split('---')[1]
    assert f'name: {agent}' in header and f'model: {model}' in header and 'effort: medium' in header
checks.append('exec-hook-and-agent-models-declared')

def call(script, *arguments, event=None):
    command = [sys.executable, str(package / 'scripts' / script), '--settings', str(settings), *arguments]
    result = subprocess.run(command, input=json.dumps(event, ensure_ascii=False) if event is not None else None, capture_output=True, text=True, encoding='utf-8', env=env)
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout) if result.stdout.strip() else None

before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
assert call('hook_entry.py', event={'cwd': str(root)}) is None
assert before == {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
checks.append('default-startup-read-only')
preview = call('configure.py', '--enable-auto-init')
assert preview['applied'] is False and not settings.exists()
checks.append('configuration-dry-run')
call('configure.py', '--apply', '--enable-auto-init')
settings_json = json.loads(settings.read_text(encoding='utf-8'))
assert settings_json['auto_init'] is True and settings_json['approve_main'] is False
checks.append('explicit-user-opt-in')
loaded = call('hook_entry.py', event={'cwd': str(root)})['hookSpecificOutput']['additionalContext']
assert 'SHARED_PROJECT_MEMORY_INITIALIZED' in loaded and 'SHARED_PROJECT_MEMORY_LOADED' in loaded
assert 'shared-project-memory:memory-summarizer' in loaded and 'shared-project-memory:simple-extractor' in loaded
assert len(loaded) <= 4000
assert (root / 'AGENTS.md').read_text(encoding='utf-8').startswith('Original project instruction\n')
assert json.loads((root / '.claude/settings.local.json').read_text(encoding='utf-8'))['permissions'] == {'allow': ['Read']}
checks.append('approved-init-and-settings-preserved')
after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
call('hook_entry.py', event={'cwd': str(root)})
assert after == {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
checks.append('idempotent-startup')
(root / 'project-memory/current.md').write_text('Current verified state\n' + '가' * 12000, encoding='utf-8')
text = call('hook_entry.py', event={'cwd': str(root)})['hookSpecificOutput']['additionalContext']
assert len(text) <= 4000 and 'truncated' in text and 'shared-project-memory:simple-extractor' in text
checks.append('bounded-unicode-context-and-model-policy')
handoff = root / 'project-memory/checkpoints/20261010-120000-codex-budget.md'
handoff.write_text('CHECKPOINT-HEAD: do not reuse the old MPC weights\n' + '세부 ' * 1500, encoding='utf-8')
budgeted = call('hook_entry.py', event={'cwd': str(root)})['hookSpecificOutput']['additionalContext']
assert len(budgeted) <= 4000, len(budgeted)
assert 'Latest checkpoint: checkpoints/20261010-120000-codex-budget.md' in budgeted, 'Newest handoff not named'
assert 'CHECKPOINT-HEAD: do not reuse the old MPC weights' in budgeted, 'Newest handoff dropped by a long current.md'
assert 'Current verified state' in budgeted and 'SHARED_PROJECT_MEMORY_USER_POLICY' in budgeted
handoff.unlink()
checks.append('latest-checkpoint-survives-long-current')
call('configure.py', '--apply', '--disable-auto-init')
assert 'SHARED_PROJECT_MEMORY_LOADED' in call('hook_entry.py', event={'cwd': str(root)})['hookSpecificOutput']['additionalContext']
checks.append('disabled-init-still-loads-memory')
original_settings = settings.read_bytes()
settings.write_text('{"auto_init":"false"}', encoding='utf-8')
failed = call('hook_entry.py', event={'cwd': str(root)})
assert 'SHARED_PROJECT_MEMORY_LOAD_FAILED' in failed['systemMessage']
checks.append('invalid-preferences-visible')
invalid_pair = json.loads(original_settings)
invalid_pair['approve_main'] = 'yes'
settings.write_text(json.dumps(invalid_pair), encoding='utf-8')
assert 'SHARED_PROJECT_MEMORY_LOAD_FAILED' in call('hook_entry.py', event={'cwd': str(root)})['systemMessage']
checks.append('invalid-approve-main-visible')
settings.write_bytes(original_settings)
call('configure.py', '--apply', '--enable-auto-init')
main = fixtures / 'main-project'
main.mkdir()
subprocess.run(['git', 'init', '-b', 'main', str(main)], check=True, capture_output=True)
blocked = call('hook_entry.py', event={'cwd': str(main)})
assert 'SHARED_PROJECT_MEMORY_LOAD_FAILED' in blocked['systemMessage'] and not (main / 'project-memory').exists()
checks.append('main-requires-separate-approval')
clone = fixtures / 'teammate-clone-on-main'
clone.mkdir()
git_id = ['-c', 'user.name=spm-test', '-c', 'user.email=spm-test@example.invalid']
subprocess.run(['git', '-C', str(root), 'add', 'AGENTS.md', 'CLAUDE.md', 'pyproject.toml', 'project-memory'], check=True, capture_output=True)
subprocess.run(['git', '-C', str(root), *git_id, 'commit', '-q', '-m', 'share project memory'], check=True, capture_output=True)
committed = subprocess.run(['git', '-C', str(root), 'ls-files'], check=True, capture_output=True, text=True).stdout.splitlines()
assert 'project-memory/MEMORY.md' in committed and not [name for name in committed if '/archive/' in name or name.startswith('.claude/')], committed
shutil.rmtree(clone)
subprocess.run(['git', 'clone', '-q', str(root), str(clone)], check=True, capture_output=True)
subprocess.run(['git', '-C', str(clone), 'checkout', '-q', '-b', 'main'], check=True, capture_output=True)
assert not (clone / 'project-memory/archive').exists() and not (clone / '.claude').exists()
shared = call('hook_entry.py', event={'cwd': str(clone)})
context = shared['hookSpecificOutput']['additionalContext']
assert 'SHARED_PROJECT_MEMORY_LOADED' in context and 'SHARED_PROJECT_MEMORY_SETUP_SKIPPED' in context, context
assert '--- MEMORY.md ---' in context and 'Current verified state' in context and 'SHARED_PROJECT_MEMORY_LOAD_FAILED' not in json.dumps(shared, ensure_ascii=False)
assert 'SHARED_PROJECT_MEMORY_SETUP_SKIPPED' in shared['systemMessage']
assert not (clone / '.claude').exists()
checks.append('git-clone-on-main-loads-index-and-current')
call('configure.py', '--apply', '--approve-main')
assert 'SHARED_PROJECT_MEMORY_INITIALIZED' in call('hook_entry.py', event={'cwd': str(main)})['hookSpecificOutput']['additionalContext']
checks.append('approved-main-init')
conflict = fixtures / 'conflicting-project'
(conflict / '.claude').mkdir(parents=True)
subprocess.run(['git', 'init', '-b', 'memory-test', str(conflict)], check=True, capture_output=True)
(conflict / 'pyproject.toml').write_text('[project]\n', encoding='utf-8')
(conflict / '.claude/settings.local.json').write_text(json.dumps({'autoMemoryDirectory': str(fixtures / 'other')}), encoding='utf-8')
assert 'SHARED_PROJECT_MEMORY_LOAD_FAILED' in call('hook_entry.py', event={'cwd': str(conflict)})['systemMessage']
assert not (conflict / 'project-memory').exists()
checks.append('conflicting-memory-path-preserved')
readonly = fixtures / 'readonly-project'
readonly.mkdir()
subprocess.run(['git', 'init', '-b', 'memory-test', str(readonly)], check=True, capture_output=True)
(readonly / 'AGENTS.md').write_text('Do not modify any files in this project.\n', encoding='utf-8')
assert 'SHARED_PROJECT_MEMORY_LOAD_FAILED' in call('hook_entry.py', event={'cwd': str(readonly)})['systemMessage']
assert not (readonly / 'project-memory').exists()
checks.append('stricter-project-rule-preserved')
print(json.dumps({'passed': checks, 'fixtures': str(fixtures)}, ensure_ascii=False, indent=2))
