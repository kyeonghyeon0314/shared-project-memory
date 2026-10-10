# Shared Project Memory — Claude Code 플러그인 0.1.3

프로젝트 안의 `project-memory/`로 작업 상태·결정·인계를 공유합니다. Codex 0.1.3 패키지와 같은 기억 형식(MEMORY.md / current.md / decisions.md / topics / checkpoints / archive)과 초기화 스크립트를 사용하므로 두 도구가 같은 기억을 이어 씁니다.

## 구성

| 경로 | 역할 |
|---|---|
| `.claude-plugin/plugin.json` | 플러그인 manifest |
| `.claude-plugin/marketplace.json` | 로컬 marketplace `shared-project-memory-local` |
| `hooks/hooks.json` | SessionStart(startup·resume·clear·compact) 훅. exec form: `python3` + `${CLAUDE_PLUGIN_ROOT}/scripts/hook_entry.py`, 셸을 거치지 않음 |
| `agents/` | `shared-project-memory:memory-summarizer`, `shared-project-memory:simple-extractor` |
| `skills/shared-project-memory/` | 작업 시작·저장·인계 지침 |
| `scripts/` | 로딩·초기화·설정·테스트 (Python 3.11+, 모델 호출 없음) |

## 기능과 기본값

- 시작 훅이 현재 상태/최신 인계 발췌를 합계 4,000자 이내로 전달합니다. MEMORY.md 색인은 Claude의 auto memory(`autoMemoryDirectory`)가 로드하므로 훅이 중복 주입하지 않습니다.
- 자동 생성은 기본 OFF입니다. 받는 사람이 동의해 ON으로 설정하면 인식된 실제 프로젝트에서만 초기화합니다. main/master 초기화 동의는 별도입니다.
- 기존 기억·지침·다른 설정을 보존하고, 다른 기억 경로나 명시적 프로젝트 금지와 충돌하면 중단합니다. 변경 전 기존 파일은 프로젝트 archive에 백업합니다. 단, 로컬 전용인 `.claude/settings.local.json`의 백업은 `<CLAUDE_CONFIG_DIR 또는 ~/.claude>/shared-project-memory/backups/`에 본인만 읽을 수 있는 권한(POSIX 0600)으로 두며, 이 경로가 링크를 거쳐서라도 프로젝트 안을 가리키면 초기화를 중단합니다.
- `project-memory/.gitignore`가 `archive/`와 `.setup-complete.json`을 Git에서 제외합니다. 기존 `.gitignore`가 있으면 내용을 보존하고 규칙을 덧붙입니다. 규칙이 이미 있어도 `!` 부정 패턴 때문에 Git이 실제로 제외하지 않으면 규칙 묶음을 파일 끝에 다시 붙입니다. Git 저장소에서는 archive에 쓸 실제 파일 경로를 하나하나 `git check-ignore`로 확인한 뒤에만 사본을 만들고, 하나라도 제외되지 않으면 `.gitignore`를 되돌리고 아무것도 쓰지 않은 채 중단합니다. 초기화 결과의 `git_exposure.local_copies_verified_ignored`는 이 사전 검증 결과이고, `tracked_local_files`는 `git ls-files`로 찾은 이미 추적 중인 파일 목록입니다(둘은 별개입니다). 이미 커밋된 파일은 자동으로 추적 해제하지 않으므로 직접 `git rm --cached` 하고, 비밀값이 커밋된 적이 있다면 교체하세요.
- 이 보호 규칙은 초기화를 실행할 때 적용됩니다. 이미 연결된 프로젝트는 세션 시작 때 초기화를 다시 실행하지 않으므로, 업데이트 후 `python scripts/setup_memory.py <프로젝트>`(미리보기)와 `--apply`를 한 번 직접 실행해야 `.gitignore` 보완이 적용됩니다. 이전 버전이 CLAUDE.md에 쓴 절대 경로 줄도 자동으로 고쳐지지 않습니다. 공유 파일(AGENTS.md, CLAUDE.md, MEMORY.md)에는 PC별 절대 경로를 쓰지 않습니다.
- 자동 생성이 켜져 있어도 초기화가 거부되면(main/master 미동의 등) 이미 있는 `project-memory/`는 그대로 불러오고(Claude의 기본 기억 연결이 확인되지 않으면 MEMORY.md 색인도 제한된 길이로 함께 주입) `SHARED_PROJECT_MEMORY_SETUP_SKIPPED`로 이유를 알립니다.
- 작업 인계 저장은 에이전트가 스킬 지침을 따르는 방식입니다. 모든 대화를 자동 보관하지 않습니다.

## 필요한 것

- 명령 훅을 지원하는 Claude Code(이 패키지는 2.1.280에서 검증).
- PATH에서 `python3`로 실행되는 Python 3.11 이상. 훅은 exec form이라 Git Bash/PowerShell 유무와 무관합니다.
  - Windows: python.org 설치본처럼 `python3`가 없으면 `hooks/hooks.json`의 `"command": "python3"`를 `"python"`으로 바꾸세요(실제 `.exe`여야 하며 `.cmd`/`.bat` 불가).
  - Windows의 Python 설치 관리자(WindowsApps 별칭)는 MSIX 가상화 때문에 `AppData\Roaming` 아래 파일을 못 볼 수 있습니다. 플러그인을 `~/.claude/plugins`(기본 설치 위치)나 Documents 등 AppData 밖에 두세요.
- Git(브랜치 확인용).

## 도우미 모델 — 받는 사람이 확인할 것

| 작업 | 에이전트(전체 이름) | 모델 / effort |
|---|---|---|
| 요약 | `shared-project-memory:memory-summarizer` | `claude-sonnet-5-5` / `medium` |
| 추출 | `shared-project-memory:simple-extractor` | `claude-haiku-5-5` / `medium` |

이 값은 패키지 작성자의 선택입니다. 계정에서 해당 모델을 쓸 수 없거나 다른 모델을 원하면 `agents/*.md` 앞부분의 `model:`/`effort:` 줄을 바꾼 뒤 `claude plugin validate`로 확인하세요. 호출할 때는 전체 이름을 쓰고 `model` 인수를 생략합니다. 같은 이름의 사용자 에이전트(`~/.claude/agents/`)와는 별개입니다. 첫 실제 호출에서 실행 기록의 모델/effort를 확인하세요.

## 설치 (승인 후 직접 수행)

ZIP을 영구 보관할 폴더(AppData 밖)에 풉니다. 안의 `shared-project-memory` 폴더가 marketplace 루트이자 플러그인입니다.

먼저 설치 없이 이번 세션에만 로드해 확인할 수 있습니다:

```powershell
claude plugin validate "C:/path/to/shared-project-memory"
cd "C:/path/to/some-project"
claude --plugin-dir "C:/path/to/shared-project-memory" --debug-file "$env:TEMP/spm-hook.log" --init-only
```

로그에서 `SHARED_PROJECT_MEMORY_LOADED`(기억이 있는 프로젝트) 또는 훅 오류를 확인합니다. 기억이 없는 프로젝트에서 자동 생성이 꺼져 있으면 훅은 아무것도 출력하지 않습니다.

영구 설치:

```powershell
claude plugin marketplace add "C:/path/to/shared-project-memory"
claude plugin install shared-project-memory@shared-project-memory-local
```

## 처음 설정

항상 미리보기 결과를 검토한 뒤 `--apply`를 붙이세요. 설정 파일은 `<CLAUDE_CONFIG_DIR 또는 ~/.claude>/shared-project-memory/settings.json`이며 패키지 밖에 남습니다(변경 전 같은 폴더에 백업).

```powershell
python3 scripts/configure.py
python3 scripts/configure.py --enable-auto-init
python3 scripts/configure.py --enable-auto-init --apply
```

main/master 초기화는 별도로 승인한 경우에만:

```powershell
python3 scripts/configure.py --approve-main --apply
```

특정 프로젝트만 미리보기/초기화:

```powershell
python3 scripts/setup_memory.py "C:/path/to/project"
python3 scripts/setup_memory.py "C:/path/to/project" --apply
```

`--disable-auto-init --apply`로 자동 생성을 끕니다. main/master 동의 철회는 설정 JSON의 `approve_main`을 false로 바꿉니다.

## 기존 훅·에이전트가 이미 있는 PC

**지금 지울 것은 없습니다.** ZIP 제작/다운로드만으로 현재 설정은 바뀌지 않습니다. 전환할 때만:

1. `~/.claude/settings.json`과 기존 훅 스크립트를 백업합니다. 프로젝트의 `project-memory/`는 그대로 둡니다.
2. 기존 shared-project-memory SessionStart 훅만 비활성화합니다(다른 훅은 유지). 기존 훅과 플러그인 훅을 동시에 켜면 중복 로딩·동시 초기화가 생길 수 있습니다.
3. 플러그인을 설치하고 기존 프로젝트에서 새 세션으로 주입을 확인합니다.
4. 사용자 에이전트 `memory-summarizer`/`simple-extractor`는 지우지 않아도 됩니다. 플러그인 에이전트는 이름 공간이 달라 충돌하지 않습니다. Codex와 공용인 원본·Junction은 삭제하지 않습니다.
5. 실패하면 `claude plugin disable shared-project-memory@shared-project-memory-local` 후 기존 훅을 다시 켭니다.

기존 Codex 사용자 설정(`~/.codex/shared-project-memory/settings.json`)은 읽거나 옮기지 않습니다. Claude 쪽 동의는 위 `configure.py`로 따로 받습니다.

## 검증과 한계

```powershell
python3 scripts/test_setup.py --fixtures "C:/path/to/scratch"
python3 scripts/test_plugin.py --package . --fixtures "C:/path/to/scratch"
```

테스트는 지정한 scratch 안에 가짜 프로젝트만 만들고 실제 프로젝트나 사용자 설정을 바꾸지 않습니다. scratch를 TEMP 아래에 두지 마세요(TEMP는 자동 초기화 제외 대상). `verification.json`에 검증 범위를 기록합니다. 영구 설치, 다른 컴퓨터, macOS/Linux 실행은 아직 검증하지 않았습니다.

참고: [Claude Code hooks](https://code.claude.com/docs/en/hooks), [plugins reference](https://code.claude.com/docs/en/plugins-reference).
