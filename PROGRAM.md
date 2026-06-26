# PROGRAM — 이 워크스페이스의 작동 원리 (아이디어 파일)

> Karpathy 의 `program.md` 패턴. 이 파일은 **워크스페이스가 어떻게 돌아가는지**를 평문으로 적은 단일 지시서이자,
> 시간이 지나며 **스스로 갱신하는 개선 로그**다. 코드가 아니라 *원리*를 적는다.

## 작동 원리 (현재)

1. **업무**는 `workspace.db` 의 `tasks` 에 등록된다 (`/task` 또는 `ws.py add`).
2. **산출물**은 `/deliver` 로 만든다 → `deliverables/<PREFIX>-<id>-<slug>/` 에 `.md`(소스) + `.html`(렌더) 쌍이 생기고,
   `workspace.db` 에 메타가 기록되며, `_dashboard.html` 이 재빌드된다.
3. **지식**은 DB 가 아니라 `wiki/*.md` 평문에 쌓는다. 한 파일 = 한 주제. `wiki/index.md` 가 목차.
4. **메모**는 `notes/inbox/` 에 빠르게 적고, 정제되면 `wiki/` 로 승격한다.
5. **대시보드**(`deliverables/_dashboard.html`)는 서버 없이 더블클릭으로 연다. 저장할 때마다 새로 구워진다.

## 설계 원칙 (바꾸지 말 것)

- 상태 ≠ 지식 (DB vs 플랫 마크다운)
- 산출물은 항상 md+html 이중 저장
- 의존성 0 (표준 라이브러리)

## 개선 로그

<!-- 워크스페이스를 손볼 때마다 한 줄씩 아래에 추가. 날짜 YYYY-MM-DD. -->
- {{TODAY}} 🌱 Seed 템플릿에서 생성됨.
