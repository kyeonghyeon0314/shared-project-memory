# Claude 이식 인계

이 패키지는 Codex용입니다. 공용 기억 형식, setup_memory.py, session_start.py와 사용자 동의 설계만 재사용합니다. .claude-plugin/plugin.json과 Claude용 hooks/agents 정의를 별도로 만들고 해당 호스트에서 검증해야 합니다. 이번 배포판에 Claude 설치 성공을 표시하지 마세요.

- project-memory의 MEMORY.md/current.md/decisions.md/topics/checkpoints/archive 구조를 유지합니다.
- 개인 프로젝트 내용, SQLite 백업, 계정 정보, 이전 사용자의 동의·모델 선택은 넣지 않습니다.
- 공유판의 자동 생성 기본 OFF와 main/master 별도 동의를 유지합니다. Claude의 plugin data 경로는 CLAUDE_PLUGIN_DATA로 따로 처리하고 Codex 사용자 설정 파일을 자동으로 수정하지 않습니다.
- core build_context(event, host='claude', auto_init=사용자동의, approve_main=별도승인)를 사용합니다. Claude hook 명령은 Codex의 commandWindows를 그대로 쓰지 않고 해당 호스트 형식에 맞춥니다. plugin root 변수는 경로 공백을 포함해 안전하게 전달합니다.
- 모델이 필요한 경우 사용자의 두 작업별 선택을 받아 전용 에이전트 파일에 명시합니다. 호출할 때 model을 생략해 파일 선택을 사용합니다. plugin 에이전트는 namespaced 이름이므로 실제 Agent 목록에서 이름을 확인합니다. 실행 기록에서 첫 실제 model/effort를 확인합니다.
- 받은 사용자에게 파일 생성 범위와 기존 스킬/훅 중복 위험을 설명합니다. 기존의 다른 기억 경로·엄격한 프로젝트 규칙·정책 제한을 덮어쓰지 않습니다.
- setup_memory.py가 만든 프로젝트 CLAUDE.md/autoMemoryDirectory는 공유 연결을 위한 것입니다. 그것만으로 Claude 플러그인이 설치된 것은 아닙니다.
- 같은 사용자에게 기존 Codex·Claude 공용 스킬이 있으면 공유 원본이나 Junction을 삭제하지 않습니다. 도구별 호출/훅만 한 경로로 전환합니다.
- 실제 프로젝트에서 읽기, idempotent 초기화, 동시 인계 보존, 경로 공백/한글, 오류 표시, 첫 실제 모델 호출을 검증합니다. 원본 archive를 읽기 기본값에 넣지 않습니다.

공식 문서: https://code.claude.com/docs/en/plugins-reference
