---
name: task
description: >
  업무를 등록·조회·상태 변경한다. "할 일 추가", "업무 등록", "오늘 뭐 해야 하지", "이거 완료" 등에서 사용.
  workspace.db 의 tasks 를 bin/ws.py 로 다룬다.
---

# /task — 업무 관리

`bin/ws.py` 로 `workspace.db` 의 업무를 다룬다. (DB 미초기화면 먼저 `python bin/ws.py init`)

## 매핑

| 의도 | 명령 |
|---|---|
| 등록 | `python bin/ws.py add "제목" [--domain 영역] [--priority 1\|2\|3]` |
| 조회 | `python bin/ws.py list [--status todo\|doing\|done\|all]` |
| 진행 시작 | `python bin/ws.py start <id>` |
| 완료 | `python bin/ws.py done <id>` |

## 가이드

- 사용자가 자연어로 말하면 적절한 명령으로 옮긴다 ("이거 끝냈어" → `done <id>`).
- 우선순위/도메인이 모호하면 기본값(priority 2, domain 없음)으로 두고 묻지 않는다.
- 상태 변경(`start`/`done`)은 자동으로 대시보드를 재빌드한다 — 끝나고 `/view` 를 권할 수 있다.
