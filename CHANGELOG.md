# Changelog

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
