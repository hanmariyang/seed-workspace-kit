# {{WORKSPACE_NAME}}

> 🌱 이 워크스페이스는 **Seed** 템플릿에서 자라났습니다.
> 아직 `/onboard` 를 돌리지 않았다면 지금 실행하세요 — 인터뷰로 이 파일이 당신에 맞게 채워집니다.

---

## 정체성

- **주인**: {{OWNER}}
- **직무/역할**: {{ROLE}}
- **주요 도메인**: {{DOMAINS}}
- **주 산출물 형태**: {{DELIVERABLE_TYPES}}

## 조력 에이전트

{{ASSISTANTS}}

→ 일상 업무는 조력 에이전트가 `/deliver` 로 처리합니다. 건축가(`workspace-architect`)는 최초 1회만 부릅니다.

---

## 운영 규칙

- **상태(state)는 DB, 지식(knowledge)은 플랫 마크다운.**
  - 변하는 구조화 데이터(업무·산출물 메타) → `workspace.db` (SQLite)
  - 쌓이는 텍스트 지식(정책·배운 것·결정 이유) → `wiki/*.md`
- **모든 산출물은 `.md` + `.html` 쌍으로 저장**되고, 저장 즉시 `deliverables/_dashboard.html` 이 재빌드됩니다.
- **의존성 0** — `bin/ws.py`·`bin/render.py` 는 Python 표준 라이브러리만 씁니다.

## 명명 규약 (seed.json 이 강제)

| 대상 | 패턴 |
|---|---|
| 산출물 폴더 | `{{PREFIX}}-{id:0{{ID_PAD}}d}-{slug}` |
| 산출물 파일 | `{slug}.md` · `{slug}.html` |
| wiki 지식 | `{topic-slug}.md` |
| 빠른 메모 | `{YYYY-MM-DD}-{slug}.md` |

- slug 언어: `{{SLUG_LANG}}` · PREFIX: `{{PREFIX}}`

---

## 도구 치트시트

```bash
python bin/ws.py init                 # 최초 1회 — DB·디렉토리 생성
python bin/ws.py add "할 일" --domain 영역 --priority 1
python bin/ws.py list --status todo
python bin/ws.py start 3              # 진행중
python bin/ws.py done 3               # 완료
python bin/ws.py deliver "보고서 제목" --task 3 --from draft.md
python bin/ws.py build                # 대시보드만 재빌드
open deliverables/_dashboard.html     # 대시보드 열기
```

## 스킬

- `/onboard` — (최초 1회) 인터뷰로 워크스페이스 맞춤 구축
- `/task` — 업무 등록·조회·상태 변경
- `/deliver` — 산출물 생성 (md+html+DB) + 대시보드 재빌드
- `/view` — 대시보드 열기
