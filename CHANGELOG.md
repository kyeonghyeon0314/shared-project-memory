# Changelog

## 0.1.3 — 2026-10-10

### 수정
- Codex: SessionStart 훅이 발견되지 않던 문제를 고쳤습니다. 루트 `codex/plugin.json`(Agent Plugins 형식)이 있으면 Codex가 그 파일을 우선 읽고 플러그인 훅을 불러오지 않아, 0.1.2까지 Codex에서는 자동 기억 주입이 동작하지 않았습니다(스킬만 로드). 루트 manifest를 제거해 `.codex-plugin/plugin.json`의 `hooks` 선언이 쓰이도록 했습니다. 같은 증상이 Codex 저장소에 [openai/codex#39895](https://github.com/openai/codex/issues/39895)로 보고되어 있습니다.
- 영향: 루트 Agent Plugins manifest가 없으므로 포터블 Agent Plugins 패키지·ChatGPT ZIP 업로드 호환은 보장하지 않습니다(로컬 Codex·Claude Code 사용이 대상).
- 회귀 검사: Codex 패키지에 루트 `plugin.json`이 없고 `.codex-plugin/plugin.json`이 훅 파일을 가리키는지 확인합니다.

### 검증
- Codex: 실제 Windows 호스트(데스크톱 런타임 0.162.0-alpha.2)에서 설치, `/hooks` 신뢰 승인, 새 세션의 기억 자동 주입을 확인했습니다. 4,000자 제한 때문에 최신 인계 발췌는 일부 잘릴 수 있습니다.
- Claude Code: Docker에서 설치, 세션 시작 훅 실행, 모델 컨텍스트 수신을 확인했습니다(0.1.2 기준, 코드 동일).

### 업데이트 후
- Codex에서 플러그인을 0.1.3으로 업데이트한 뒤 `/hooks` 화면에서 shared-project-memory의 SessionStart 훅을 검토·신뢰해야 동작합니다.

## 0.1.2 — 2026-10-10

### 보안·개인정보
- `.claude/settings.local.json` 백업을 프로젝트 `archive/` 대신 `<CLAUDE_CONFIG_DIR 또는 ~/.claude>/shared-project-memory/backups/`에 0600 권한(폴더 0700)으로 저장합니다. 백업 위치가 링크를 거쳐서라도 프로젝트 안을 가리키면 중단합니다.
- `project-memory/.gitignore`로 `archive/`와 `.setup-complete.json`을 Git에서 제외합니다. 기존 `.gitignore`는 보존합니다.
- archive에 쓸 실제 경로를 `git check-ignore`로 하나씩 확인한 뒤에만 사본을 만듭니다. `!` 부정 패턴이 백업을 다시 포함시키면 규칙을 파일 끝에 덧붙이고, 그래도 제외되지 않으면 `.gitignore`를 되돌리고 아무것도 쓰지 않은 채 중단합니다.
- 이미 Git이 추적 중인 local-only 파일은 따로 경고합니다(자동 추적 해제는 하지 않음).

### 동작
- `CLAUDE.md`와 `MEMORY.md`에 PC별 절대 경로 대신 상대 경로를 씁니다.
- 자동 초기화가 거부돼도(main/master 미동의 등) 이미 있는 `project-memory/`는 불러오고 `SHARED_PROJECT_MEMORY_SETUP_SKIPPED`로 알립니다.
- Claude의 기본 기억 연결이 확인되지 않으면 `MEMORY.md` 색인 일부를 직접 주입합니다.

### 개발
- GitHub Actions: Linux·Windows·macOS × Python 3.11·3.13에서 테스트 4개 실행.
- MIT 라이선스 추가.

### 업데이트 시 주의
- 이미 연결된 프로젝트에는 `setup_memory.py <프로젝트> --apply`를 한 번 다시 실행해야 새 보호 규칙이 적용됩니다.
- 이전 버전이 `CLAUDE.md`에 쓴 절대 경로 줄은 자동으로 고쳐지지 않습니다.
