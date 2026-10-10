# Shared Project Memory — Codex 로컬 플러그인 0.1.4

프로젝트 안의 `project-memory/`로 작업 상태·결정·인계를 공유합니다. 이 배포판은 Codex용이며 Claude 플러그인 manifest/에이전트는 포함하지 않습니다. 공용 Markdown 형식과 초기화 스크립트는 Claude 이식에 재사용할 수 있습니다.

## 기능과 기본값

- SessionStart/startup·resume·clear·compact에서 색인/현재 상태/최신 인계 발췌를 합계 4,000자 이내로 전달합니다. 안내 문구와 기억 발췌를 한 번에 배분하며, 최신 인계(checkpoint)에 최소 800자를 먼저 보장하고 그 경로는 항상 표시합니다. 남는 분량은 색인과 `current.md`에 돌아갑니다.
- 자동 생성은 기본 OFF입니다. 받는 사람이 동의해 ON으로 설정하면 인식된 실제 프로젝트에서만 초기화합니다. main/master 초기화 동의는 별도입니다.
- 기존 기억·지침·다른 설정을 보존하고, 다른 기억 경로나 명시적 프로젝트 금지와 충돌하면 중단합니다. 변경 전 기존 파일은 프로젝트 archive에 백업합니다. 단, 로컬 전용인 `.claude/settings.local.json`의 백업은 `<CLAUDE_CONFIG_DIR 또는 ~/.claude>/shared-project-memory/backups/`에 본인만 읽을 수 있는 권한(POSIX 0600)으로 두며, 이 경로가 링크를 거쳐서라도 프로젝트 안을 가리키면 초기화를 중단합니다.
- `project-memory/.gitignore`가 `archive/`와 `.setup-complete.json`을 Git에서 제외합니다. 기존 `.gitignore`가 있으면 내용을 보존하고 규칙을 덧붙입니다. 규칙이 이미 있어도 `!` 부정 패턴 때문에 Git이 실제로 제외하지 않으면 규칙 묶음을 파일 끝에 다시 붙입니다. Git 저장소에서는 archive에 쓸 실제 파일 경로를 하나하나 `git check-ignore`로 확인한 뒤에만 사본을 만들고, 하나라도 제외되지 않으면 `.gitignore`를 되돌리고 아무것도 쓰지 않은 채 중단합니다. 초기화 결과의 `git_exposure.local_copies_verified_ignored`는 이 사전 검증 결과이고, `tracked_local_files`는 `git ls-files`로 찾은 이미 추적 중인 파일 목록입니다(둘은 별개입니다). 이미 커밋된 파일은 자동으로 추적 해제하지 않으므로 직접 `git rm --cached` 하고, 비밀값이 커밋된 적이 있다면 교체하세요.
- 이 보호 규칙은 초기화를 실행할 때 적용됩니다. 이미 연결된 프로젝트는 세션 시작 때 초기화를 다시 실행하지 않으므로, 업데이트 후 `python scripts/setup_memory.py <프로젝트>`(미리보기)와 `--apply`를 한 번 직접 실행해야 `.gitignore` 보완이 적용됩니다. 이전 버전이 CLAUDE.md에 쓴 절대 경로 줄도 자동으로 고쳐지지 않습니다. 공유 파일(AGENTS.md, CLAUDE.md, MEMORY.md)에는 PC별 절대 경로를 쓰지 않습니다.
- 자동 생성이 켜져 있어도 초기화가 거부되면(main/master 미동의 등) 이미 있는 `project-memory/`는 그대로 불러오고(Claude의 기본 기억 연결이 확인되지 않으면 MEMORY.md 색인도 제한된 길이로 함께 주입) `SHARED_PROJECT_MEMORY_SETUP_SKIPPED`로 이유를 알립니다.
- 모델 선택은 받는 사람의 선택입니다. 기본 모델 매핑은 비어 있고 자동 별도 헬퍼 호출은 없습니다. 프로젝트 초기화·로딩은 Python으로 처리하며 모델을 호출하지 않습니다.
- 작업 인계 저장은 에이전트가 스킬 지침을 따르는 방식입니다. 모든 대화를 자동 보관하거나 매 도구 호출을 관찰하는 기능은 아닙니다.

## 요구 환경

로컬 프로젝트와 명령 훅을 지원하는 Codex, 기존 Python 3.11 이상, 기존 Git이 필요합니다. 패키지는 아무것도 설치하지 않습니다. Windows 훅은 Codex의 기존 bundled Python, PATH의 Python/py 순으로 찾습니다. 직접 지정하려면 사용자 환경 변수 `SPM_PYTHON`에 Python 실행 파일 경로를 설정하세요. macOS/Linux는 `python3`가 PATH에 있어야 하며, 이번 배포 검증은 Windows에서 수행했습니다.

## ZIP 업로드와 로컬 설치의 차이

이 패키지의 manifest는 `.codex-plugin/plugin.json` 하나입니다. 0.1.2까지 있던 루트 `plugin.json`(Agent Plugins 형식)은 0.1.3에서 제거했습니다. Codex 0.153·0.162는 루트 `plugin.json`이 있으면 그 파일을 우선 읽는데, 그 형식에서는 플러그인 훅을 불러오지 않아 SessionStart 훅이 `hooks/list`와 `/hooks` 화면에 나타나지 않았습니다(스킬만 로드됨). 같은 문제가 [openai/codex#39895](https://github.com/openai/codex/issues/39895)로 보고되어 있습니다. 그래서 포터블 Agent Plugins 패키지·ZIP 업로드 호환은 보장하지 않습니다. 앱의 새 플러그인 → 파일 선택 → 플러그인 추가는 계정에 비공개 플러그인을 등록하는 경로이며 로컬 marketplace 등록과 같지 않습니다. 이 경로의 업로드 성공은 검증하지 않았습니다. 어느 경로든 지원되는 로컬 Codex 세션에서 설치·훅 신뢰·실제 주입을 확인해야 합니다. cloud-orchestrated Work에서는 이 명령 훅이 지원되지 않습니다.

Claude의 ZIP 업로드는 Claude manifest와 Claude용 훅/호스트 설정이 필요합니다. 현재 ZIP은 여전히 Codex용입니다. PORTING-CLAUDE.md를 기준으로 이식 후 .claude-plugin/plugin.json을 포함하고 Claude의 실제 validator/업로드를 확인해야 합니다.

## 로컬 설치 대안

ZIP을 영구 보관할 폴더로 풉니다. ZIP 안의 `shared-project-memory` 폴더가 marketplace 루트이자 플러그인 소스입니다. 다운로드 ZIP 자체만 열어서는 설치되지 않습니다.

지원되는 Codex 앱의 로컬 marketplace 추가 화면에서 이 폴더를 선택한 뒤 `shared-project-memory`를 설치합니다. 설치 화면이 로컬 marketplace 추가를 제공하지 않으면 같은 로컬 계정의 터미널에서 다음 명령을 사용하고 앱을 갱신합니다. CLI 옵션 지원 여부는 `codex plugin marketplace --help`로 확인하세요.

```powershell
codex plugin marketplace add "C:/path/to/shared-project-memory"
codex plugin add shared-project-memory@shared-project-memory-local
```

앱/CLI의 공식 Hooks 검토 화면에서 이 플러그인의 SessionStart 정의를 검토하고 신뢰하세요. 설치만으로 훅이 신뢰되지 않습니다. 검토 화면이 앱에 없으면 CLI `/hooks`로 검토할 수 있습니다. trust 우회 옵션이나 trust hash 수동 편집은 사용하지 않습니다. 프로젝트 폴더에서 새 세션을 시작하세요.

## 처음 설정

패키지를 푼 폴더에서 실행합니다. 아래 `python`은 Python 3.11+ 실행 파일로 바꿔도 됩니다. 항상 미리보기 결과를 검토한 뒤 `--apply`를 붙이세요.

```powershell
python scripts/configure.py
python scripts/configure.py --enable-auto-init
python scripts/configure.py --enable-auto-init --apply
```

`--enable-auto-init --apply`는 해당 사용자에 대해 인식된 로컬 프로젝트의 기억/지침 연결/Claude 기억 경로를 자동 초기화하도록 동의한다는 뜻입니다. 기존의 main/master 금지까지 승인했다는 뜻은 아닙니다. 사용자가 그 초기화도 별도로 승인한 경우에만 다음을 사용합니다.

```powershell
python scripts/configure.py --approve-main
python scripts/configure.py --approve-main --apply
```

상위 프로젝트 규칙이 더 엄격하면 설정과 무관하게 중단합니다. Git·신뢰 등록·프로젝트 표식이 없는 빈 폴더, 임시/의존성 폴더는 자동 초기화하지 않습니다. 사용자는 다음 명령으로 특정 프로젝트만 미리보기/초기화할 수도 있습니다.

```powershell
python scripts/setup_memory.py "C:/path/to/project"
python scripts/setup_memory.py "C:/path/to/project" --apply
```

기본 사용자 설정 파일은 `<CODEX_HOME 또는 ~/.codex>/shared-project-memory/settings.json`입니다. 업데이트해도 사용자 설정은 패키지 밖에 남습니다. 변경 전 해당 파일은 같은 디렉터리에 백업합니다. `--disable-auto-init --apply`로 자동 생성을 끌 수 있습니다. main/master 동의를 철회하려면 설정 JSON의 `approve_main`을 false로 바꾸세요.

## 작업별 모델 선택 — 선택 사항

본인 계정에서 지원되는 모델과 effort를 직접 정하세요. 두 작업의 선택은 주 대화 모델을 변경하지 않습니다. 아래 자리표시자는 실제 선택값으로 바꿔야 합니다.

```powershell
python scripts/configure.py --summary-model YOUR_SUMMARY_MODEL --summary-effort YOUR_EFFORT --extract-model YOUR_EXTRACTION_MODEL --extract-effort YOUR_EFFORT
# 미리보기 확인 후 같은 명령에 --apply 추가
```

앱의 명시적 모델 override 경로를 사용합니다. 스킬은 첫 실제 호출의 실행 메타데이터를 확인하도록 합니다. 계정/호스트가 모델을 지원하지 않으면 보고하며 다른 모델로 자동 대체하지 않습니다. 이 배포판은 서버에서 모델 정책을 강제하는 라우터가 아닙니다.

## 기존 스킬·훅이 이미 있는 PC

**지금 기존 것을 지울 필요가 없습니다.** ZIP 제작/다운로드만으로 현재 설정은 바뀌지 않습니다.

플러그인으로 전환할 때만 다음을 수행합니다.

1. 기존 설정을 백업합니다. 프로젝트의 `project-memory/`는 유지합니다.
2. Codex의 기존 shared-project-memory SessionStart 훅만 공식 훅 관리 화면에서 비활성화합니다. 다른 훅은 건드리지 않습니다. 기존 훅과 플러그인 훅을 동시에 켜면 중복 로딩·동시 초기화가 생길 수 있습니다.
3. 기존 전역 로컬 스킬은 Codex의 스킬 설정에서 해당 원본 경로만 비활성화합니다. 그 스킬이 Claude와 공용인 경우 원본 폴더나 Junction을 삭제하지 않습니다. Claude 쪽 설정은 그대로 유지합니다. 실제 설정 변경은 사용자 승인 후에 합니다.
4. 플러그인 설치/신뢰/사용자 설정을 완료하고 기존 프로젝트에서 실제 주입을 확인합니다. 실패하면 플러그인을 비활성화하고 기존 Codex 스킬·훅을 다시 켭니다.

현재 작업과 이전 기록은 프로젝트 폴더에 있으므로 전환을 위해 재수집하거나 삭제할 필요가 없습니다. 패키지 제작 과정에서는 설치·전환을 수행하지 않았습니다.

## Claude 이식용 안내

`PORTING-CLAUDE.md`를 전달하세요. Codex hook JSON을 그대로 복사하거나 개인 Python 경로를 하드코딩하지 마세요. 현재 공용 기억 폴더를 유지하고 사용자별 승인/모델 선택을 다시 확인해야 합니다.

## 검증과 한계

```powershell
python scripts/test_setup.py --fixtures "C:/path/to/scratch"
python scripts/test_plugin.py --package . --fixtures "C:/path/to/scratch"
```

테스트는 지정한 scratch 안에 보존되는 가짜 프로젝트만 만들고 실제 프로젝트나 사용자 설정을 바꾸지 않습니다. `verification.json`에 이번 검증 범위를 기록합니다. 패키지 구조/스크립트 검증과 실제 Codex 앱 설치·훅 신뢰·주입 검증은 구분합니다. 이 공유판의 실제 설치, 다른 컴퓨터, macOS/Linux 실행은 아직 검증하지 않았습니다.

출처: [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Codex plugin management](https://learn.chatgpt.com/docs/enterprise/plugin-management).
