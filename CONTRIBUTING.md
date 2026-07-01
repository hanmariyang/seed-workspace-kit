# 기여 가이드 — Seed 🌱

Seed 에 관심 가져 주셔서 고맙습니다. 이 문서는 기여 절차와 지켜야 할 원칙을 정리합니다.

## 먼저 읽어주세요 — 프로젝트 철학

Seed 는 **작게 유지되는 것**이 목표입니다. 기능을 더하기 전에 아래 4대 원칙을 지키는지 확인해 주세요.

1. **의존성 0** — `bin/ws.py`·`bin/render.py` 는 Python 표준 라이브러리만 씁니다. `pip install` 이 필요한 변경은 원칙적으로 받지 않습니다. (필요성이 크면 이슈에서 먼저 논의)
2. **상태(state)는 DB, 지식(knowledge)은 플랫 마크다운** — 구조화 데이터는 `workspace.db`, 텍스트 지식은 `wiki/*.md`.
3. **소스 + 렌더 동시 보존** — 산출물은 `.md` + `.html` 쌍으로.
4. **최소 골격** — 과설계 금지. "있으면 좋은" 기능보다 "없으면 곤란한" 기능을 우선합니다.

큰 변경은 **이슈로 먼저 제안**해 방향을 맞춘 뒤 PR 을 보내주세요.

## 개발 환경

의존성 설치가 없습니다. Python 3.9+ 만 있으면 됩니다.

```bash
git clone https://github.com/hanmariyang/seed-workspace-kit my-seed
cd my-seed
python bin/ws.py init                       # DB·seed.json·대시보드 생성
python bin/ws.py add "첫 할 일" --domain 운영 --priority 1
python bin/ws.py deliver "첫 산출물"
open deliverables/_dashboard.html
```

## 기여 절차

1. 저장소를 **fork** 하고 브랜치를 만듭니다: `feat/…`, `fix/…`, `docs/…`
2. 변경 후 로컬에서 스모크 확인:
   ```bash
   python -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('bin/*.py')]"  # 문법
   python bin/ws.py init && python bin/render.py                                            # 렌더 동작
   ```
3. **커밋 메시지**는 이모지 + 짧은 요약을 권장합니다 (예: `✨ feat: 대시보드 도메인 필터`).
4. **PR** 을 열고 템플릿을 채워주세요. 스크린샷이 있으면 리뷰가 빨라집니다.

## 코드 스타일

- 도구는 **단일 파일**로 유지합니다 (`ws.py`, `render.py`).
- 표준 라이브러리만. 외부 패키지 추가 금지.
- 한국어 주석·문서를 기본으로 하되, 코드 식별자는 영어를 씁니다.
- 대시보드·문서 테마는 `deliverables/_assets/theme.css` 한 곳에서 관리합니다.

## 무엇을 기여하면 좋나요

- 🐛 버그 수정 (렌더 깨짐, 명명 규약 엣지 케이스 등)
- 🎨 대시보드 카탈로그(`docs/dashboard-catalog/`) 새 컨셉 — **외부 상용 서비스 이름/출처는 표기하지 않습니다**
- 🌈 테마 액센트 추가 (`render.py` 의 `ACCENTS`)
- 📖 문서·번역 개선

## 행동 강령

이 프로젝트는 [행동 강령](CODE_OF_CONDUCT.md)을 따릅니다. 참여로써 이를 준수하는 데 동의하는 것으로 간주합니다.

## 라이선스

기여하신 내용은 저장소와 동일한 [MIT License](LICENSE) 로 배포됩니다.
