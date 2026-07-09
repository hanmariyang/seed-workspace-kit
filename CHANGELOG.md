# 변경 이력

이 프로젝트의 주요 변경을 기록합니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/),
버전은 [유의적 버전(SemVer)](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### 추가됨
- **`/note` · `/decide` 스킬** — 이미 있던 `notes`·`decisions` DB 테이블을 실제로 쓰는 CLI(`ws.py note` / `ws.py decide`). 인자 없이 부르면 최근 목록 조회. CLAUDE.md 가 약속한 `state=DB` 의 미이행분을 채움(원탁 5회차 — 약속 부채 청산, 동결 예외).

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
