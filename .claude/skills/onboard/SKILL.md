---
name: onboard
description: >
  (최초 1회) 이 워크스페이스를 당신의 업무에 맞게 구축한다. 인터뷰 6~8문항 → 디렉토리·DB·조력 에이전트·
  코어 스킬·산출물 뷰어 생성 → 첫 산출물 시연. "워크스페이스 세팅", "처음부터 잡아줘", "온보딩"에서 사용.
---

# /onboard — 워크스페이스 건축

이 스킬은 **워크스페이스를 처음 세우는** 1회성 파이프라인이다. 운전은 `workspace-architect` 에이전트가 한다.

## 절차

1. **건축 에이전트 호출** — Agent 도구로 `workspace-architect` 를 실행. 인터뷰를 위임한다.
   (전체 정의: `.claude/agents/workspace-architect.md`)
2. 건축가가 진행하는 것 (DESIGN §6-A):
   - **인터뷰** 6~8문항 (한 번에 하나씩, 자명하면 건너뛰기) — 직무·도메인·산출물형태·조력자수·톤·이름·명명규약
   - **생성** — `seed.json` 갱신(이름·PREFIX·slug_lang) → `python bin/ws.py init` → `CLAUDE.md`·`PROGRAM.md` 의 `{{...}}` 치환 → 조력 에이전트 1~2명을 `.claude/agents/` 에 작성
   - **시연** — 첫 업무 1개를 `ws.py add` → `ws.py deliver` 로 md+html 산출물 생성
   - **점화** — `deliverables/_dashboard.html` 을 열어 보여주고 "여기서 시작하세요" 안내 후 종료
3. **멱등성** — 이미 구축된 워크스페이스에서 재실행되면 덮어쓰지 말고 누락분만 보완.

## 끝나고

사용자에게: 이후 일상은 `/task`(업무) · `/deliver`(산출물) · `/view`(대시보드) 로 돌린다고 알린다.
