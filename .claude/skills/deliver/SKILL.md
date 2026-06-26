---
name: deliver
description: >
  산출물을 만든다 — 본문 작성 → md+html 동시 저장 → DB 기록 → 대시보드 재빌드. "보고서 써줘", "산출물 만들어줘",
  "문서 정리해서 저장" 등에서 사용. 업무 파이프라인(DESIGN §6-B)의 Persist·Report 단계.
---

# /deliver — 산출물 생성

업무 파이프라인의 핵심. **본문은 LLM 이 쓰고, 저장·렌더·대시보드는 `bin/ws.py` 가 한다.**

## 절차

1. **Capture/Route** — 어떤 산출물인지 파악. 연결할 업무가 있으면 `--task <id>`.
2. **Execute** — 산출물 본문을 **마크다운으로 작성**. (헤더·표·리스트·코드·인용 지원 — `render.py` 가 변환)
3. **Persist + Report** — 작성한 마크다운을 파일로 저장한 뒤:
   ```bash
   python bin/ws.py deliver "산출물 제목" --task <id> --from <작성한.md>
   ```
   - 이게 `deliverables/<PREFIX>-<id>-<slug>/` 에 `.md`+`.html` 을 만들고, DB 에 기록하고, `_dashboard.html` 을 재빌드한다.
   - 본문을 파일 대신 stdin 으로 넘겨도 된다: `echo "..." | python bin/ws.py deliver "제목"`
4. 결과로 출력된 html 경로를 사용자에게 알리고, 대시보드를 열려면 `/view`.

## 지식이면 wiki 로

산출물이 *재사용할 지식*(정책·배운 것)이라면, 추가로 `wiki/<주제>.md` 에 적고 `wiki/index.md` 에 한 줄 포인터를 남긴다.
(상태=DB / 지식=wiki 분리 원칙.)

## 명명

slug·PREFIX 는 `seed.json` 규약을 따른다. 직접 정하려면 `--slug <slug>`. 보통은 제목에서 자동 파생되게 둔다.
