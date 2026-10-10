# Shared Project Memory

Codex와 Claude Code가 같은 프로젝트 기억(`project-memory/`)을 이어 쓰도록 하는 로컬 플러그인입니다. 두 도구용 패키지는 같은 기억 형식(MEMORY.md / current.md / decisions.md / topics / checkpoints / archive)과 같은 초기화 스크립트를 사용합니다.

| 폴더 | 대상 | 버전 |
|---|---|---|
| [`claude/`](claude/) | Claude Code 플러그인 (SessionStart 훅, 헬퍼 에이전트 2개, 스킬) | 0.1.2 |
| [`codex/`](codex/) | Codex 로컬 플러그인 | 0.1.2 |

공통 요구 사항: Python 3.11 이상, Git. 프로젝트 기억은 각 프로젝트 폴더 안에 있으므로 플러그인과 별개로 프로젝트를 따라 이동합니다.

## Claude Code 설치

```bash
claude plugin marketplace add kyeonghyeon0314/shared-project-memory
claude plugin install shared-project-memory@shared-project-memory-local
```

설치 후 한 번, 자동 생성 동의를 설정합니다(PC마다 따로 저장됨). 미리보기 후 `--apply`를 붙이세요.

```bash
python3 <설치된 claude 폴더>/scripts/configure.py --enable-auto-init
python3 <설치된 claude 폴더>/scripts/configure.py --enable-auto-init --apply
```

- 헬퍼 모델: `shared-project-memory:memory-summarizer`(claude-sonnet-5-5 / medium), `shared-project-memory:simple-extractor`(claude-haiku-5-5 / medium). 바꾸려면 `claude/agents/*.md`의 `model:`/`effort:`를 수정합니다.
- 이미 같은 이름(`shared-project-memory-local`)의 로컬 marketplace를 등록한 PC는 먼저 `claude plugin marketplace remove shared-project-memory-local` 후 위 명령으로 바꿉니다. 두 경로를 동시에 켜면 훅이 중복 실행됩니다.
- 자세한 설정·제약: [`claude/README.md`](claude/README.md)

## Codex 설치

저장소를 클론한 뒤 `codex/` 폴더를 로컬 marketplace로 등록합니다.

```bash
codex plugin marketplace add "<클론 경로>/codex"
codex plugin add shared-project-memory@shared-project-memory-local
```

훅 신뢰와 사용자 설정은 [`codex/README.md`](codex/README.md)를 따릅니다.

## 두 도구를 함께 쓸 때

- 같은 프로젝트의 `project-memory/`를 공유합니다. 도구를 바꾸기 전에 인계(checkpoint)를 남기세요.
- 자동 생성 동의와 main/master 동의는 도구별 설정 파일에 따로 저장됩니다(Claude: `~/.claude/shared-project-memory/settings.json`, Codex: `~/.codex/shared-project-memory/settings.json`).

## 0.1.2로 업데이트할 때

- 플러그인을 업데이트한 뒤, 이미 초기화한 각 프로젝트에서 `setup_memory.py <프로젝트>`(미리보기)와 `--apply`를 한 번 실행하세요. 그래야 `project-memory/.gitignore` 보호 규칙이 적용됩니다.
- 이전 버전이 `CLAUDE.md`에 적은 절대 경로 줄(`공유 기억 경로: /...`)은 자동으로 바뀌지 않으니 직접 지우거나 `project-memory/`로 고치세요.
- 변경 내역: [CHANGELOG.md](CHANGELOG.md)

## 라이선스

[MIT](LICENSE)
