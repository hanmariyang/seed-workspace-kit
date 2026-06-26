# 🌱 My Workspace (Seed)

이 repo 는 [Seed](https://github.com/) 템플릿에서 시작한 **개인 워크스페이스**입니다.

## 시작하기

1. Claude Code 를 이 폴더에서 열고 **`/onboard`** 를 실행하세요.
   인터뷰 몇 개로 디렉토리·DB·조력 에이전트·산출물 뷰어가 당신에 맞게 구성됩니다.
2. 수동으로 먼저 보고 싶다면:

```bash
python bin/ws.py init
python bin/ws.py add "첫 할 일"
python bin/ws.py deliver "첫 산출물"
open deliverables/_dashboard.html
```

## 구조

- `workspace.db` — 업무·산출물 상태 (SQLite, git 제외)
- `wiki/` — 평문 마크다운 지식베이스
- `deliverables/` — 산출물 (md+html 쌍) + `_dashboard.html`
- `bin/` — `ws.py`(DB CLI), `render.py`(렌더러) — 의존성 0
- `.claude/` — 에이전트 + 스킬(`/onboard` `/task` `/deliver` `/view`)

자세한 작동 원리는 `PROGRAM.md`, 정체성·규칙은 `CLAUDE.md`.
