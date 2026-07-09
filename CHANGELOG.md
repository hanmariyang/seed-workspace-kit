# 변경 이력

이 프로젝트의 주요 변경을 기록합니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/),
버전은 [유의적 버전(SemVer)](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### 추가됨
- **`/note` · `/decide` 스킬** — 이미 있던 `notes`·`decisions` DB 테이블을 실제로 쓰는 CLI(`ws.py note` / `ws.py decide`). 인자 없이 부르면 최근 목록 조회. CLAUDE.md 가 약속한 `state=DB` 의 미이행분을 채움(원탁 5회차 — 약속 부채 청산, 동결 예외).
- **지식 파이프라인 — `ws.py promote` + `/search` 스킬** — 메모를 `wiki/{topic}.md` 지식으로 승격(DB→md 단방향, 승격 시 notes 에서 이동)하고, 업무·메모·결정·산출물(DB) + wiki·산출물 본문(파일)을 색인 없이 즉석 grep 으로 통합 검색. CLAUDE.md 가 약속한 `knowledge=wiki` 실작동(원탁 5회차 a2+c1). 검색은 별도 도구화·색인 파일 없이 `ws.py` 단일 파일에 흡수.
- **산출물 유형 템플릿 — `templates/*.md` (12종) + `ws.py templates` / `deliver --template`** — 보고서·회의록·기획·스펙·제안·의사결정(ADR)·리서치·가이드·체크리스트·주간·회고·사고회고 골격. `--template <이름>` 으로 시작하면 `{{title}}`·`{{date}}` 자동 치환. 템플릿은 코드가 아니라 마크다운 파일이라 `templates/<이름>.md` 하나 떨어뜨리면 코드 변경 없이 확장(원탁 5회차 a3).
- **자라는 CLAUDE.md — 재문진 `ws.py checkup` + `/checkup` 스킬** — 축적 데이터(주요 도메인·태그·씨실·산출물/지식/결정 수)를 읽어 CLAUDE.md 를 지금의 나에 다시 맞추도록 제안. 인터뷰를 1회성 DNA → 반복 성장으로. 트리거 3층: `seed.json`의 `last_checkup` 마커(30일 또는 산출물 15건) · `checkup --due`(어시스턴트 heartbeat, CLAUDE.md 규칙) · 대시보드 `🌱 재문진 권장` 칩. **가드**(원탁 6회차 C): 데몬/cron 없음·강제 실행 없음·CLAUDE.md 자동 수정 없음 — pull·권유·사람 승인 편집만.
- **씨실(backlinks) — `[[주제]]` 지식 연결 + `/links` 스킬** — wiki·산출물 어디서든 `[[주제]]` 평문 링크로 지식을 그물로 엮음. `ws.py links` 로 엮임 현황, `ws.py links "주제"` 로 백링크(참조하는 것)·아웃링크(가리키는 것) 즉석 grep. `promote` 가 승격 본문의 `[[]]` 감지, `search` 가 검색어의 참조 수 귀띔. 핵심 기술로 승격·검색·대시보드를 꿰는 가로실(원탁 6회차 B). **절제선**: `[[]]` 파서 금지(깨진 링크도 텍스트)·그래프 시각화 금지(숫자로만)·백링크 색인 저장 금지(매번 즉석 grep) — 넘으면 위키 엔진이라 각하.
- **성장 나이테 — `ws.py growth` + 대시보드 푸터 서사** — `created_at` 타임스탬프를 읽어 "이 워크스페이스는 심은 지 34일째 — 산출물 2·지식 1·결정 2 만큼 자랐습니다. 가장 바빴던 주는…" 한 줄로. 차트·그래프 없이 문장만(원탁 6회차 A, render 각하선 밖). 씨앗→나무 성장을 눈에 보이게.
- **대시보드 헤더 집계 — `결정`·`지식` 스탯 카드** — 기존 `.stats` 스트립에 DB 파생 카운트 2칸 추가(`decisions` 수 · `wiki/*.md` 수). 새 레이아웃·차트 없이 기존 골격의 헤더 채우기만(render.py 순증 +6줄, 원탁 5회차 c2 — 4회차 각하선 아래로 통과).

## [0.1.0] — 2026-07-01

첫 공개 릴리스. 🌱

### 추가됨
- **인터뷰 온보딩** — `/onboard` 로 6~8문항 인터뷰 후 워크스페이스 맞춤 생성 (`workspace-architect` 에이전트)
- **무의존 도구** — `bin/ws.py`(SQLite CLI) · `bin/render.py`(md→html 렌더러 + 대시보드 빌더), 표준 라이브러리만
- **코어 스킬** — `/task` · `/deliver` · `/view`
- **산출물 이중 저장** — 모든 산출물은 `.md`(소스) + `.html`(렌더) 쌍으로, 저장 시 대시보드 자동 재빌드
- **대시보드 카탈로그** — 같은 데이터를 10가지 컨셉(테이블·칸반·갤러리·차트·타임라인·기여 그래프·다크 집중·리뷰 등)으로 보여주는 시안 모음 (`docs/dashboard-catalog/`)
- **테마 커스텀** — `seed.json` 의 `theme.accent`(6종) / `theme.mode`(light·dark) + 대시보드 라이트/다크 토글
- **파비콘** — 🌱 새싹 마크 (인라인 SVG, 자기완결)
- **문서** — README · DESIGN · 프로젝트 포스터(HTML)
- **커뮤니티** — LICENSE(MIT) · CONTRIBUTING · CODE_OF_CONDUCT · SECURITY · 이슈/PR 템플릿 · CI 스모크

[Unreleased]: https://github.com/hanmariyang/seed-workspace-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hanmariyang/seed-workspace-kit/releases/tag/v0.1.0
