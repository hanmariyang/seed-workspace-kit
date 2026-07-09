---
name: search
description: >
  워크스페이스 전체를 한 번에 검색한다. "그거 어디 적었지", "정산 관련해서 뭐 있었지", "찾아줘" 등에서 사용.
  업무·메모·결정·산출물(DB) + wiki·산출물 본문(파일)을 색인 없이 즉석 grep 으로 훑는다.
---

# /search — 통합 검색

workspace.db 의 구조화 데이터와 `wiki/`·`deliverables/` 의 마크다운을 한 명령으로 뒤진다. (DB 미초기화면 먼저 `python bin/ws.py init`)

## 매핑

| 의도 | 명령 |
|---|---|
| 검색 | `python bin/ws.py search "검색어" [--limit N]` |

훑는 곳: **[업무]** tasks.title · **[메모]** notes.body · **[결정]** decisions(요약+이유) · **[산출물]** deliverables.title · **[wiki]** `wiki/**/*.md` · **[산출물 본문]** `deliverables/**/*.md`

## 가이드

- 사용자가 "어디 적었더라 / ~관련 뭐 있었지 / 찾아줘" 라고 하면 핵심 단어 하나로 `search` 한다.
- 대소문자 구분 없음. 한 단어 부분일치가 기본 — 여러 후보가 나오면 사용자에게 어느 것인지 되묻는다.
- 결과가 wiki·산출물이면 `파일:줄번호` 로 나오니 이어서 그 파일을 열어 보여줄 수 있다.
- **색인·캐시 파일을 만들지 않는다.** 매번 즉석으로 훑는다(정체성: state=DB / knowledge=md 외에 새 SOR 를 만들지 않음). 느려질 만큼 커지면 그건 워크스페이스를 쪼갤 신호다.
