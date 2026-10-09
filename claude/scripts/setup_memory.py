import argparse
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

MEMORY_FOLDER = 'project-memory'
MARKER = '<!-- shared-project-memory -->'

def validate_project_rules(root):
    prohibition = r"(?i)\b(?:never|do not|don't|must not|forbidden|prohibited)\b.*\b(?:modify|edit|write|create|change|overwrite)\b"
    targets = r"(?i)project-memory|AGENTS\.md|CLAUDE\.md|settings(?:\.local)?\.json|\b(?:any|all)\s+files?\b"
    for name in ('AGENTS.md', 'CLAUDE.md'):
        path = root / name
        if path.is_file():
            for line in path.read_text(encoding='utf-8-sig').splitlines():
                explicit_deny = re.search(prohibition, line) and re.search(targets, line)
                readonly = re.search(r'(?i)read.only (?:project|repository)|(?:project|repository) is read.only|프로젝트.*읽기.?전용|모든.*파일.*(?:수정|생성).*금지', line)
                korean_deny = re.search(r'금지|수정하지|생성하지|만들지', line) and re.search(targets, line)
                if explicit_deny or readonly or korean_deny:
                    raise RuntimeError(f'Project instruction restricts automatic managed-file changes: {name}')


def is_connected(root):
    root = Path(root).resolve()
    memory = root / MEMORY_FOLDER
    for path in (memory / 'MEMORY.md', memory / 'current.md', memory / 'decisions.md', root / 'AGENTS.md', root / 'CLAUDE.md', root / '.claude/settings.local.json'):
        if not path.is_file():
            return False
        if not path.resolve().is_relative_to(root):
            raise RuntimeError(f'Managed path resolves outside the project: {path}')
    agents = (root / 'AGENTS.md').read_text(encoding='utf-8-sig')
    claude = (root / 'CLAUDE.md').read_text(encoding='utf-8-sig')
    settings = json.loads((root / '.claude/settings.local.json').read_text(encoding='utf-8-sig'))
    configured = settings.get('autoMemoryDirectory')
    return bool(
        (MARKER in agents or 'project-memory/MEMORY.md' in agents)
        and (MARKER in claude or 'project-memory/current.md' in claude or '@AGENTS.md' in claude)
        and configured and Path(configured).expanduser().resolve() == memory
    )


def initialize(root, apply=False, approve_main=False):
    root = Path(root).resolve(strict=True)
    if not root.is_dir() or root == Path(root.anchor) or root == Path.home().resolve():
        raise RuntimeError('Choose a specific project directory, not the drive or home root')
    validate_project_rules(root)
    memory = root / MEMORY_FOLDER
    managed_paths = (memory, memory / 'topics', memory / 'checkpoints', memory / 'archive', memory / 'MEMORY.md', memory / 'current.md', memory / 'decisions.md', root / 'AGENTS.md', root / 'CLAUDE.md', root / '.claude/settings.json', root / '.claude/settings.local.json')
    for target in managed_paths:
        if not target.resolve().is_relative_to(root):
            raise RuntimeError(f'Memory folder resolves outside project: {target}')
    settings_path = root / '.claude/settings.local.json'
    settings_bytes = settings_path.read_bytes() if settings_path.exists() else None
    settings = json.loads(settings_bytes.decode('utf-8-sig')) if settings_bytes is not None else {}
    config_root = Path(os.environ.get('CLAUDE_CONFIG_DIR', str(Path.home() / '.claude'))).expanduser()
    scope_paths = [config_root / 'settings.json', root / '.claude/settings.json', settings_path]
    if os.name == 'nt':
        scope_paths.append(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'ClaudeCode/managed-settings.json')
    else:
        scope_paths.append(Path('/etc/claude-code/managed-settings.json'))
    configured = None
    configured_source = None
    for scope_path in scope_paths:
        if scope_path.is_file():
            scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
            if scope.get('autoMemoryDirectory'):
                configured = scope['autoMemoryDirectory']
                configured_source = str(scope_path)
    if configured and Path(configured).expanduser().resolve() != memory.resolve():
        raise RuntimeError(f'A different effective autoMemoryDirectory exists in {configured_source}; preserve it and ask before redirecting')
    git = subprocess.run(['git', '-C', str(root), 'branch', '--show-current'], capture_output=True, text=True)
    if git.returncode and 'not a git repository' not in git.stderr.lower():
        raise RuntimeError(git.stderr.strip() or 'Cannot inspect the project Git branch')
    branch = git.stdout.strip() if git.returncode == 0 else None
    if apply and branch in ('main', 'master') and not approve_main:
        raise RuntimeError('main/master setup requires the explicit --approve-main flag')
    protocol = f'''# {root.name} 공유 기억 색인

프로젝트: `{root.as_posix()}`

## 작업 시작

- 이 색인이 이미 컨텍스트에 있으면 다시 읽지 않습니다.
- [현재 상태](current.md)와 해당 작업의 최신 checkpoints 인계를 읽습니다.
- [결정과 선호](decisions.md), 필요한 주제 파일만 추가로 읽습니다. archive 전체를 기본 컨텍스트에 넣지 않습니다.
- 기억과 현재 파일이 다르면 현재 파일/로그를 확인하고 차이를 기록합니다. 과거 AI 해석은 사실이나 새 승인으로 취급하지 않습니다.

## 저장

- 중요한 변경/검증 후, 작업 종료, 도구 전환 전에 새 인계 파일을 남깁니다.
- 경로: checkpoints/YYYYMMDD-HHMMSS-agent-session.md. 세션별 파일을 사용하고 기존 인계를 덮어쓰지 않습니다.
- 목적, 실제 변경 파일, 확인 결과와 조건, 미완료/실패, 다음 작업, 출처를 기록합니다. 제안/미검증 내용을 구분합니다.
- 단독 작업이면 최신 current.md를 다시 읽고 갱신합니다. 동시 작업이면 각자 인계를 쓰고 공용 현재 상태를 서로 덮어쓰지 않습니다.
- 안정된 결정만 decisions.md/관련 주제에 반영합니다. 원본 archive와 기존 기억은 삭제하지 않습니다.
- 새 사용자 지시와 작업 권한이 우선합니다. 쓰기가 실패하면 저장했다고 말하지 않습니다.
- 강제 종료 전에 저장하지 못한 대화는 자동 복원되지 않습니다.

## 구조

- current.md / decisions.md: 현재 상태와 확정한 결정.
- topics/: 필요할 때 읽는 주제별 기억.
- checkpoints/: 두 도구의 작업 인계.
- archive/: 기존 기억/초기 설정 사본. 과거 기록의 현재 유효성은 별도로 확인합니다.
'''
    index_was_absent = not (memory / 'MEMORY.md').exists()
    desired = {
        memory / 'MEMORY.md': protocol.encode('utf-8'),
        memory / 'current.md': f'# 현재 상태 — {root.name}\n\n공유 기억 경로를 연결했습니다. 프로젝트의 진행 상태와 연구 결과는 아직 확인하지 않았습니다.\n새 작업에서 현재 파일/로그를 확인한 뒤 이 문서와 세션별 인계를 갱신합니다.\n'.encode('utf-8'),
        memory / 'decisions.md': '# 결정과 사용자 선호\n\n새 사용자 지시와 기존 프로젝트 규칙을 우선합니다. 확인된 선호와 결정만 출처/날짜와 함께 기록합니다.\n'.encode('utf-8'),
    }
    desired = {path: content for path, content in desired.items() if not path.exists()}
    blocks = {
        root / 'AGENTS.md': f'''\n\n{MARKER}
## 공유 프로젝트 기억

- 작업 시작에 project-memory/MEMORY.md와 current.md, 해당 작업의 최신 checkpoints 인계를 읽습니다.
- 필요한 주제만 읽고 archive 전체를 매번 로드하지 않습니다.
- 중요한 작업/검증 완료, 종료, 도구 전환 전에 공용 색인의 저장 규칙에 따라 인계를 남깁니다.
- 기존 사용자 지침, 승인 범위, 코드/데이터 보존 규칙을 그대로 따릅니다.
''',
        root / 'CLAUDE.md': f'''\n\n{MARKER}
## 공유 프로젝트 기억

공유 기억 경로: `{memory.as_posix()}`.
색인은 auto memory로 기본 로드됩니다. 이미 컨텍스트에 있으면 다시 읽지 않습니다.
작업 시작에 project-memory/current.md와 해당 작업의 최신 checkpoints 인계를 읽습니다.
중요 작업 완료, 종료, Codex로 전환 전에 공용 색인의 저장 규칙에 따라 인계를 남깁니다.
기존 프로젝트 지침/권한을 보존합니다. 과거 기록과 현재 파일이 다르면 현재 자료를 재확인합니다.
''',
    }
    for path, block in blocks.items():
        original = path.read_bytes() if path.exists() else b''
        text = original.decode('utf-8-sig')
        if MARKER not in text:
            for line in text.splitlines():
                if 'project-memory' in line.lower() and re.search(r'do not|never|금지|생성하지|만들지|수정하지', line, re.I):
                    raise RuntimeError(f'Existing memory instruction may prohibit setup; inspect it first: {path}')
            if path.name == 'CLAUDE.md' and not path.exists():
                block = '@AGENTS.md\n' + block
            desired[path] = original + block.encode('utf-8')
    if not configured:
        settings['autoMemoryDirectory'] = memory.as_posix()
        desired[settings_path] = (json.dumps(settings, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    native = Path.home() / '.claude/projects' / re.sub(r'[^A-Za-z0-9]', '-', str(root)) / 'memory'
    if index_was_absent and native.is_dir():
        for path in native.glob('*.md'):
            destination = memory / 'archive/claude-native' / path.name
            if not destination.exists():
                desired[destination] = path.read_bytes()
    for path in desired:
        if not path.resolve().is_relative_to(root):
            raise RuntimeError(f'Write target resolves outside the project: {path}')
    before = {path: path.read_bytes() if path.exists() else None for path in desired}
    changed = [path.relative_to(root).as_posix() for path in desired]
    if apply:
        if changed:
            backup = memory / 'archive' / ('setup-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:8])
            for path, content in before.items():
                if content is not None:
                    copy = backup / path.relative_to(root)
                    copy.parent.mkdir(parents=True, exist_ok=True)
                    copy.write_bytes(content)
        for path, content in desired.items():
            current = path.read_bytes() if path.exists() else None
            if current != before[path]:
                raise RuntimeError(f'File changed during setup; refusing to overwrite: {path}')
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, prefix=path.name+'.', delete=False) as temporary:
                temporary.write(content)
                temporary_path = temporary.name
            os.replace(temporary_path, path)
        for folder in ('topics', 'checkpoints', 'archive'):
            target = memory / folder
            if not target.resolve().is_relative_to(root):
                raise RuntimeError(f'Memory folder resolves outside project: {target}')
            target.mkdir(parents=True, exist_ok=True)
    if apply and is_connected(root):
        completion = memory / '.setup-complete.json'
        if changed or not completion.exists():
            completion.write_text(json.dumps({'status': 'complete', 'version': 1}) + '\n', encoding='utf-8')
    return {'project': str(root), 'branch': branch, 'applied': apply, 'changed': changed, 'shared_memory': str(memory), 'native_memory_candidate_found': native.is_dir(), 'settings_check': 'user/project/local/managed files; live CLI or hosted policy overrides need host verification'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preview or initialize local Codex/Claude shared project memory. No network, inference calls, installs, commits or deletion.')
    parser.add_argument('project')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--approve-main', action='store_true')
    args = parser.parse_args()
    print(json.dumps(initialize(args.project, args.apply, args.approve_main), ensure_ascii=False, indent=2))
